from bs4 import BeautifulSoup
import requests
import subprocess
from PIL import Image
from PIL import UnidentifiedImageError
import re
import traceback
import sys
from pathlib import Path

class ImageDownloader:
    def __init__(self):
        self.offset = self.__check_page_offset()
        self.url = self.get_url()
        self.folder_name = self.get_folder_name()
        self.__create_temporary_folder()

    def __check_page_offset(self, offset = 's'):
        """ refers to if the first page should be made a double spread or not

        Options are: 
            single, s -> for Single first Page
            double, d -> for doubled first page
        """
        valid_offsets = ['s', 'single', 'd', 'double']
        if len(sys.argv) >= 2:
            if sys.argv[1] in valid_offsets:
                return sys.argv[1]
            else:
                print('Must provide option of \"(s)ingle\" or \"(d)ouble\"')
                quit()
        else:
            print("Using default of setting separating first page (single)")
            return offset

    def get_url(self):
        url = str(input("Input a URL: "))
        url = re.sub('/$', '', url)
        return url

    def get_folder_name(self):
        """
        Get final path of the URL and make that the name of the temporary folder
        to store images in before combining into PDF 

        (i.e. foo.com/directories/bar will make 'bar' the folder name)
        (also the name of the PDF later on; bar.pdf)
        """
        last_slash = self.url.rindex('/')
        return self.url[last_slash + 1::]

    def __create_temporary_folder(self):
        """
        Create a directory and a subdirectory to put the images to download in
        """
        is_path_conflict = self.is_path_conflicts()
        if not is_path_conflict:
            subprocess.run(['mkdir', '-p', self.folder_name + '/' + "combined"])
        else:
            print(f"\nFile or directory '{self.folder_name}(.pdf)' already exists; Exiting.")
            quit()

    def is_path_conflicts(self):
        """
        Returns 'True' if there are conflicts; else False
        """
        folder_path = Path(f"./{self.folder_name}")
        file_path = Path(f"./{self.folder_name}.pdf")
        
        if folder_path.exists() or file_path.exists():
            return True
        else:
            return False

    def scrape_webpage(self):
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, "html.parser")

        #Obtain all img tags at the specified URL
        image_links = soup.find_all("img")
        self.images_to_convert = []
        i = 0
        for image in image_links:

            #Obtain the URL of the image on in each img tag
            image_to_download = image["src"]

            #Only want the URLs that begin with http or https
            if re.search('^http|^https', image_to_download):
                last_slash = image_to_download.rindex('/')
                file_name = f"{self.folder_name + '_' + str(i) + '.jpg'}"
                subprocess.run(['curl', '-o', self.folder_name + '/' + file_name, image_to_download])
                self.images_to_convert.append(file_name)
                i += 1
    
    def convert_images_to_RGB(self):
        images = []
        for f in self.images_to_convert:
            try:
                images.append(Image.open('./' + self.folder_name + '/' + f))
            except UnidentifiedImageError: 
                traceback.print_exc()
            except:
                traceback.print_exc()

        #Removes 'RGBA' warning
        self.rgb_images = []
        for image in images:
            self.rgb_images.append(image.convert('RGB'))

    # ISSUE IS IN COMBINE IMAGES
    def combine_images(self):

        iter_max = len(self.rgb_images)
        print(f"{iter_max=}")
        file_name = self.folder_name + '/combined/image_0.jpg'

        """ For for manga, oftentimes the first page, so we
            put it on it's own page
        """

        i = 0
        self.combined_images = []
        if self.offset == 'single' or self.offset == 's':
            self.combined_images.append(file_name)
            if len(self.rgb_images) != 0:
                self.rgb_images[0].save(file_name)
            i = 1

        while i < iter_max:
            max_height = 0
            total_width = 0
            try:
                # If the width is greater than 1400, put that image on it's own page
                if self.rgb_images[i].size[0] > self.rgb_images[i].size[1] or i == iter_max - 1 or (self.rgb_images[i].size[0] < self.rgb_images[i].size[1] and self.rgb_images[i + 1].size[0] > self.rgb_images[i+1].size[1] and i != 1):
                    file_name = self.folder_name + "/combined/image_" + str(i) + ".jpg"
                    self.rgb_images[i].save(file_name)
                    self.combined_images.append(file_name)
                    i += 1
                elif i < iter_max - 1 and self.rgb_images[i].size[0] < self.rgb_images[i].size[1] and self.rgb_images[i+1].size[0] < self.rgb_images[i + 1].size[1]:
                    image_array = [self.rgb_images[i + 1], self.rgb_images[i]]
                    total_width = 0
                    max_height = 0
                    # find the width and height of the final image
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
                    self.combined_images.append(file_name)
                    i += 2
                else:
                    print('oh no')
            except KeyboardInterrupt:
                traceback.print_exc()
                quit()
            except:
                traceback.print_exc()

    def generate_pdf(self):
        #Write the opened combined Images to a new list
        images = []
        for f in self.combined_images:
            images.append(Image.open(f))

        pdf_path = "./" + self.folder_name + ".pdf"
        
        #Save the combined images in a new pdf
        images[0].save(
                pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1::]
        )

    def cleanup(self):
        #Cleanup images in directory
        subprocess.run(['rm', '-rf', self.folder_name])

if __name__ == "__main__":
    imgdwnldr = ImageDownloader()
    imgdwnldr.scrape_webpage()
    imgdwnldr.convert_images_to_RGB()
    imgdwnldr.combine_images()
    imgdwnldr.generate_pdf()
    imgdwnldr.cleanup()

    

