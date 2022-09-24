import click
from bs4 import BeautifulSoup
import requests
import subprocess
from PIL import Image
from PIL import UnidentifiedImageError
import re
import traceback
from pathlib import Path
import sys
from typing import Optional, List

class Img2PDFScrpr:
    _VALID_OFFSETS = [
        ['s', 'single'],
        ['d', 'double'],
        ['c', 'combo']
        ]
    _VALID_READING_DIRECTIONS = ["<-", "->"]

    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12.6; rv:105.0) Gecko/20100101 Firefox/105.0'

    def __init__(self, url: Optional[str]=None, offset:str = "s", direction:str = "<-", url_file: Optional[str]=None ): #, offset: str = "s"):
        self.offset = self._check_page_offset(offset)
        self._reading_direction = self._check_reading_direction(direction)

        # Optionals
        self.url = url
        self.url_file = url_file

    def _check_page_offset(self, offset: str) -> str:
        """ 
        refers to if the first should be made a double spread or not

        Options are: 
            single, s -> for Single first Page
            double, d -> for doubled first page
            combo, c -> combination (leaves first page by itself and combines 2nd/3rd image)
        """
        if (offset in 
           (item for sublist in self._VALID_OFFSETS for item in sublist)):
            return offset
        else:
            print(f"{offset} is not a valid offset. "
                   "Defaulting to (s)ingle offset")
            return 's'

    """
        Checks the specified reading direction
        Prioritizes right-to-left (<-) reading to defer to manga
    """
    def _check_reading_direction(self, reading_direction: str):
        if reading_direction in self._VALID_READING_DIRECTIONS:
            return reading_direction
        else:
            return "<-"

    def _clean_url(self, url: str) -> str:
        url = re.sub('/$', '', url)
        return url 
    
    def _get_folder_name(self, url) -> str:
        """
        get final path of the url and make that the name 
        of the temporary folder to store images in before 
        combining into pdf.

        (i.e. foo.com/directories/bar will make 'bar' the folder name)
        (also the name of the pdf later on; bar.pdf)
        """
        last_slash = url.rindex('/')
        return url[last_slash + 1::]

    def _is_path_conflicts(self) -> bool:
        """
        Returns 'True' if there are conflicts; else False
        """
        folder_path = Path(f"./{self.folder_name}")
        file_path = Path(f"./{self.folder_name}.pdf")
        
        if folder_path.exists() or file_path.exists():
            return True
        else:
            return False

    def _create_temporary_folder(self) -> None:
        """
        Create a directory and a subdirectory to put the images to download in
        """
        is_path_conflict = self._is_path_conflicts()
        if not is_path_conflict:
            subprocess.run(['mkdir', '-p', self.folder_name + '/' + "combined"])
        else:
            sys.exit(f"\nFile or directory '{self.folder_name}(.pdf)'"
                   " already exists; Exiting.")

    def scrape_webpage(self, url: str) -> List[str]:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "html.parser")

        #Obtain all img tags at the specified URL
        i = 0
        images_to_convert: List[str] = []
        try:
            image_links = soup.find_all("img")
            for image in image_links:

                #Obtain the URL of the image on in each img tag
                image_to_download = image["src"]

                #Only want the URLs that begin with http or https
                if re.search('^http|^https', image_to_download):
                    file_name = f"{self.folder_name + '_' + str(i) + '.jpg'}"
                    subprocess.run(
                        ['curl', '--user-agent',
                         self.USER_AGENT, '-o',
                         self.folder_name + '/' + file_name,
                         image_to_download])
                    images_to_convert.append(file_name)
                    i += 1
        except KeyboardInterrupt:
            sys.exit(f"Stopping download of {self.folder_name}")
        except Exception:
            traceback.print_exc()

        return images_to_convert

    def _open_images(self, images_to_convert: List[str]) -> List[Image.Image]:
        """
        Loops through each image downloaded and converts to RGB after 
        opening (PIL gets upset if not converted; need to look into it more)
        """
        opened_images: List[Image.Image] = []
        for f in images_to_convert:
            try:
                opened_images.append(Image.open('./' + self.folder_name + '/' + f)
                    .convert('RGB')) # Last method removes RGBA warning
            except UnidentifiedImageError: 
                traceback.print_exc()
            except:
                traceback.print_exc()
        return opened_images

    def _save_double_page(self, opened_images: List[Image.Image], combined_images: List[str], i: int):
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
        image_array = []
        if self._reading_direction == "<-":
            image_array = [opened_images[i + 1], opened_images[i]]
        else:
            image_array = [opened_images[i], opened_images[i + 1]]

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

    def _combine_images(self, rgb_images: List[Image.Image]) -> List[str]:

        iter_max = len(rgb_images)
        file_name = self.folder_name + '/combined/image_0.jpg'

        """ For for manga, oftentimes the first page, so we
            put it on it's own page
        """

        i = 0
        combined_images = []
        # To determine if the
        if self.offset in self._VALID_OFFSETS[0]: 
            if len(rgb_images) != 0:
                combined_images.append(file_name)
                rgb_images[0].save(file_name)
            i = 1
        elif self.offset in self._VALID_OFFSETS[1]:
            self._save_double_page(rgb_images, combined_images, i)
            i = 2
        elif self.offset in self._VALID_OFFSETS[2]:
            if len(rgb_images) > 2:
                combined_images.append(file_name)
                rgb_images[0].save(file_name)
            self._save_double_page(rgb_images, combined_images, i=1)
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
                    self._save_double_page(rgb_images, combined_images, i)
                    i += 2
            except KeyboardInterrupt:
                traceback.print_exc()
                sys.exit()
            except:
                traceback.print_exc()
        return combined_images

    def _generate_pdf(self, combined_images: List[str]) -> None:
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

    def run(self, url:Optional[str]=None, url_file:Optional[str]=None, cleanup: bool=True) -> None:
        if url is not None:
            self.img2pdf_from_url(url)
        elif url_file is not None:
            self.img2pdf_from_file(url_file)

    def cleanup(self) -> None:
        #Cleanup images in directory
        subprocess.run(['rm', '-rf', self.folder_name])

    def img2pdf_from_file(self, url_file: str, cleanup: bool=True) -> None:
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
            sys.exit(f"File {url_file} does not exist; exiting.")

    def img2pdf_from_url(self, url:str, cleanup: bool=True):
        self.folder_name = self._get_folder_name(url)
        self._create_temporary_folder()
        print(f"Downloading {self.folder_name}")
        images = self.scrape_webpage(url)
        rgb_images = self._open_images(images)
        combined_images = self._combine_images(rgb_images)
        self._generate_pdf(combined_images)
        if cleanup:
            self.cleanup()

        
@click.command()
@click.option('--offset', '-o', default="s", type=str, help="used to specify if the first page should "
         "be a (s)ingle, (d)ouble spread, or (c)ombo (leaves first page by itself and combines 2nd/3rd image)", required=False)
@click.option("--file", "-f", default=None, type=str,
    help='specify text file of URLs from which to download', required=False)
@click.option("--url", "-u", default=None, type=str,
              help="specifies the url whose images are to be fetched and converted")

def main(offset, file, url):
    obj = Img2PDFScrpr(offset)
    obj.run(url=url, url_file=file)

if __name__ == "__main__":
    main()

