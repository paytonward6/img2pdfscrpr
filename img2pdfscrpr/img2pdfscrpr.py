from bs4 import BeautifulSoup
import requests
import subprocess
from PIL import Image
from PIL import UnidentifiedImageError
import re
import traceback
from pathlib import Path
import argparse

class ImageDownloader:
    VALID_OFFSETS = [
        ['s', 'single'],
        ['d', 'double'],
        ['c', 'combo']
        ]

    PARSER = argparse.ArgumentParser(
        description="Downloads images from webpages and generates "
                     "a side-by-side PDF (optimized manga)")
    PARSER.add_argument("-o", "--offset", type=str,
        help="used to specify if the first page should "
             "be a (s)ingle, (d)ouble spread, or (c)ombo (leaves first page by itself and combines 2nd/3rd image)")
    PARSER.add_argument("-f", "--file", type=str,
        help='specify text file of URLs from which to download')
     
    def __init__(self):
        self.args = self.PARSER.parse_args()
        self.offset = self.check_page_offset() 

        if self.args.file:
            self.url_file = self.args.file.strip()
        else:
            self.url = None

    def check_page_offset(self) -> str:
        """ 
        refers to if the first should be made a double spread or not

        Options are: 
            single, s -> for Single first Page
            double, d -> for doubled first page
            combo, c --> combination (leaves first page by itself and combines 2nd/3rd image)
        """
        if (self.args.offset in 
           (item for sublist in self.VALID_OFFSETS for item in sublist)):
            return self.args.offset
        else:
            print(f"{self.args.offset} is not a valid offset. "
                   "Defaulting to (s)ingle offset")
            return 's'
    
    def __get_url(self) -> str:
        return str(input("Input a URL: "))

    def parse_url(self, user_input) -> str:
        url = re.sub('/$', '', user_input)
        print()
        return url 

    def set_url(self) -> None:
        if self.args.file:
            pass
        else:
            url = self.__get_url()
            self.url = self.parse_url(url)

    def get_folder_name(self, url) -> str:
        """
        Get final path of the URL and make that the name 
        of the temporary folder to store images in before 
        combining into PDF.

        (i.e. foo.com/directories/bar will make 'bar' the folder name)
        (also the name of the PDF later on; bar.pdf)
        """
        last_slash = url.rindex('/')
        return url[last_slash + 1::]

    def __create_temporary_folder(self) -> None:
        """
        Create a directory and a subdirectory to put the images to download in
        """
        is_path_conflict = self.is_path_conflicts()
        if not is_path_conflict:
            subprocess.run(['mkdir', '-p', self.folder_name + '/' + "combined"])
        else:
            print(f"\nFile or directory '{self.folder_name}(.pdf)'"
                   " already exists; Exiting.")
            quit()

    def is_path_conflicts(self) -> bool:
        """
        Returns 'True' if there are conflicts; else False
        """
        folder_path = Path(f"./{self.folder_name}")
        file_path = Path(f"./{self.folder_name}.pdf")
        
        if folder_path.exists() or file_path.exists():
            return True
        else:
            return False

    def scrape_webpage(self, url) -> list:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        #Obtain all img tags at the specified URL
        image_links = soup.find_all("img")
        images_to_convert = []
        i = 0
        print(f"Downloading {self.folder_name}")
        for image in image_links:

            #Obtain the URL of the image on in each img tag
            image_to_download = image["src"]

            #Only want the URLs that begin with http or https
            if re.search('^http|^https', image_to_download):
                file_name = f"{self.folder_name + '_' + str(i) + '.jpg'}"
                subprocess.run(['curl', '-o', self.folder_name + '/'
                               + file_name, image_to_download])
                images_to_convert.append(file_name)
                i += 1
    
        return images_to_convert

    def convert_images_to_RGB(self, images_to_convert) -> list:
        """
        Loops through each image downloaded and converts to RGB after 
        opening (PIL gets upset if not converted; need to look into it more)
        """
        rgb_images = []
        for f in images_to_convert:
            try:
                rgb_images.append(Image.open('./' + self.folder_name + '/' + f)
                    .convert('RGB')) # Last method removes RGBA warning
            except UnidentifiedImageError: 
                traceback.print_exc()
            except:
                traceback.print_exc()
        return rgb_images

    def save_double_page(self, rgb_images, combined_images, i):
        """
        Since manga is read left to right, the order of the images on the
        page is as so:
        ----------------------
        |         ||         |
        |         ||         |
        |    2    ||    1    |
        |         ||         |
        |         ||         |
        ----------------------
        """
        image_array = [rgb_images[i + 1], rgb_images[i]]

        total_width = 0
        max_height = 0
        # Find the width and height of the final image
        for img in image_array:
            total_width += img.size[0]
            max_height = max(max_height, img.size[1])

        new_img = Image.new('RGB', (total_width, max_height))
        current_width = 0
        file_name = self.folder_name + "/combined/image_" + str(i) + ".jpg"
        # Create a new image, combinding two images side by side
        for img in image_array:
            new_img.paste(img, (current_width,0))
            current_width += img.size[0]
        new_img.save(file_name)
        combined_images.append(file_name)

    def combine_images(self, rgb_images) -> list:

        iter_max = len(rgb_images)
        file_name = self.folder_name + '/combined/image_0.jpg'

        """ For for manga, oftentimes the first page, so we
            put it on it's own page
        """

        i = 0
        combined_images = []
        # To determine if the
        if self.offset in self.VALID_OFFSETS[0]: 
            if len(rgb_images) != 0:
                combined_images.append(file_name)
                rgb_images[0].save(file_name)
            i = 1
        elif self.offset in self.VALID_OFFSETS[1]:
            self.save_double_page(rgb_images, combined_images, i)
            i = 2
        elif self.offset in self.VALID_OFFSETS[2]:
            if len(rgb_images) > 2:
                combined_images.append(file_name)
                rgb_images[0].save(file_name)
            self.save_double_page(rgb_images, combined_images, i=1)
            i = 3

        while i < iter_max:
            try:
                # If the width is greater than 1400, put that image on it's own page
                    # size[0] -> width, size[1] -> height
                if (rgb_images[i].size[0] > rgb_images[i].size[1] 
                    or i == iter_max - 1
                    or (rgb_images[i].size[0] < rgb_images[i].size[1]
                        and rgb_images[i + 1].size[0] > rgb_images[i+1].size[1]
                        and i != 1)):
                    file_name = self.folder_name + "/combined/image_" + str(i) + ".jpg"
                    rgb_images[i].save(file_name)
                    combined_images.append(file_name)
                    i += 1

                elif (i < iter_max - 1 
                      and rgb_images[i].size[0] < rgb_images[i].size[1] 
                      and rgb_images[i+1].size[0] < rgb_images[i + 1].size[1]):
                    self.save_double_page(rgb_images, combined_images, i)
                    i += 2
            except KeyboardInterrupt:
                traceback.print_exc()
                quit()
            except:
                traceback.print_exc()
        return combined_images

    def generate_pdf(self, combined_images) -> None:
        #Write the opened combined Images to a new list
        images = []
        for f in combined_images:
            images.append(Image.open(f))

        pdf_path = "./" + self.folder_name + ".pdf"
        
        #Save the combined images in a new pdf
        images[0].save(
                pdf_path, "PDF", 
                resolution=100.0, 
                save_all=True,
                append_images=images[1::]
        )

    def img2pdf_from_file(self, url_file):
        try:
            with open(url_file, "r") as file:
                urls = file.readlines()
                for url in urls:
                    url = url.strip()
                    if url == "":
                        pass
                    else:
                        self.img2pdf_from_url(url)
        except FileNotFoundError:
            print(f"File {url_file} does not exist; exiting.")
            quit()

    def img2pdf_from_url(self, url):
        self.folder_name = self.get_folder_name(url)
        self.__create_temporary_folder()
        images = self.scrape_webpage(url)
        rgb_images = self.convert_images_to_RGB(images)
        combined_images = self.combine_images(rgb_images)
        self.generate_pdf(combined_images)
        self.cleanup()

    def run(self) -> None:
        """
        A single method to download images, combine, and cleanup
        """
        if self.args.file:
            self.img2pdf_from_file(self.url_file)
        else:
            self.img2pdf_from_url(self.url)


    def cleanup(self) -> None:
        #Cleanup images in directory
        subprocess.run(['rm', '-rf', self.folder_name])
def main():
    imgdwnldr = ImageDownloader()
    imgdwnldr.set_url()
    imgdwnldr.run()

if __name__ == "__main__":
    main()
