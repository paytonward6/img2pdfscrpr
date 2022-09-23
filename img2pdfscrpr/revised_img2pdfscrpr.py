import click
import re
from typing import Optional

class Img2PDFScrpr:
    _VALID_OFFSETS = [
        ['s', 'single'],
        ['d', 'double'],
        ['c', 'combo']
        ]

    USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12.6; rv:105.0) Gecko/20100101 Firefox/105.0'

    def __init__(self, url: str, url_file: Optional[str]=None, offset:str = "s"): #, offset: str = "s"):
        self.url_file = url_file
        self.url = self._clean_url(url)
        self.offset = self._check_page_offset(offset)

        self.folder_name = self._get_folder_name(self.url)

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

    def _create_temporary_folder(self) -> None:
        """
        Create a directory and a subdirectory to put the images to download in
        """
        is_path_conflict = self.is_path_conflicts()
        if not is_path_conflict:
            subprocess.run(['mkdir', '-p', self.folder_name + '/' + "combined"])
        else:
            sys.exit(f"\nFile or directory '{self.folder_name}(.pdf)'"
                   " already exists; Exiting.")
        
#@click.command()
#@click.option('--offset', '-o', default="s", type=str, help="used to specify if the first page should "
#         "be a (s)ingle, (d)ouble spread, or (c)ombo (leaves first page by itself and combines 2nd/3rd image)")
#@click.option("--file", "-f", default=None, type=str,
#    help='specify text file of URLs from which to download')

def main():
    obj = Img2PDFScrpr("blah", offset="d")
    print(vars(obj))

if __name__ == "__main__":
    main()

