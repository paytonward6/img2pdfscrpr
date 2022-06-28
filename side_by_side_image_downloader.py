from bs4 import BeautifulSoup
import requests
import urllib.request
import shutil
import subprocess
import os
from PIL import Image
import re

def main():
    #url = str(input("Input a URL: "))
    url = "https://onepiecechapters.com/chapters/2305/one-piece-chapter-1052"

    last_slash = url.rindex('/')
    folder_name = url[last_slash + 1::]
    subprocess.run(['mkdir', folder_name])

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")

    image_links = soup.find_all("img")

    images_to_convert = []
    for image in image_links:

        image_to_download = image["src"]
        if re.search('^http|^https', image_to_download):
            last_slash = image_to_download.rindex('/')
            file_name = image_to_download[last_slash + 1::]
            #subprocess.run(['wget', '-O', folder_name + '/' + file_name, image_to_download])
            images_to_convert.append(file_name)


    images = []
    for f in images_to_convert:
        images.append(Image.open('./' + folder_name + '/' + f))

    rgb_images = []
    for image in images:
        rgb_images.append(image.convert('RGB'))

    pdf_path = "double_spread_testing" + ".pdf"

    iter_max = len(rgb_images)
    rgb_images[0].save(f"testing/image_0.jpg")
    i = 1
    combined_images = []
    while i < iter_max:
        print(i)
        max_height = 0
        total_width = 0
        try:
            if rgb_images[i].size[0] > 1400 or i == iter_max - 1:
                print('beep')
                #new_img = Image.new('RGB', (rgb_images[i].size[0], rgb_images[i].size[1]))
                #new_img.paste(rgb_images[i], (0,0))
                rgb_images[i].save(f"testing/image_{i}.jpg")
                i += 1
            elif i < iter_max - 1 and rgb_images[i].size[0] < 1300 and rgb_images[i+1].size[0] < 1300:
                image_array = [rgb_images[i + 1], rgb_images[i]]
                total_width = 0
                max_height = 0
                # find the width and height of the final image
                for img in image_array:
                    total_width += img.size[0]
                    max_height = max(max_height, img.size[1])

                new_img = Image.new('RGB', (total_width, max_height))
                current_width = 0
                for img in image_array:
                    new_img.paste(img, (current_width,0))
                    current_width += img.size[0]
                new_img.save(f"testing/image_{i}.jpg")
                combined_images.append(new_img)
                i += 2
        except:
            print('bad')


#    combined_images[0].save( pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=combined_images[1::])

    #subprocess.run(['rm', '-rf', folder_name + '/'])
if __name__ == '__main__':
    main()
