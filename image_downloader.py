from bs4 import BeautifulSoup
import requests
import urllib.request
import shutil
import subprocess
import os
from PIL import Image

url = str(input("Input a URL: "))

last_slash = url.rindex('/')
folder_name = url[last_slash + 1::]
print(folder_name)

response = requests.get(url)

soup = BeautifulSoup(response.text, "html.parser")

image_links = soup.find_all("img")
subprocess.run(['mkdir', folder_name])

images_to_convert = []
for image in image_links:

    image_to_download = image["src"]
    last_slash = image_to_download.rindex('/')
    file_name = image_to_download[last_slash + 1::]
    subprocess.run(['wget', '-O', folder_name + '/' + file_name, image_to_download])
    images_to_convert.append(file_name)

images_to_convert.remove('h-logo.png')

images = []
for f in images_to_convert:
    images.append(Image.open('./' + folder_name + '/' + f))

rgb_images = []
for image in images:
    rgb_images.append(image.convert('RGB'))
pdf_path = "./" + folder_name + ".pdf"

rgb_images[0].save(
        pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=rgb_images[1::]
)

subprocess.run(['rm', '-rf', folder_name + '/'])
