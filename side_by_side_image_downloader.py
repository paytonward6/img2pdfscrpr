from bs4 import BeautifulSoup
import requests
import subprocess
from PIL import Image
from PIL import UnidentifiedImageError
import re
import traceback
import sys

def main():
    """ refers to if the first page should be made a double spread or not

    Options are: 
        single, s -> for Single first Page
        double, d -> for doubled first page
    """
    offset = ""
    if len(sys.argv) < 2:
        print('Must provide option of \"single\" or \"double\"')
        quit()
    else:
        offset = str(sys.argv[1])
    
    url = str(input("Input a URL: "))
    url = re.sub('/$', '', url)
    """
    Get final path of the URL make that the name of the folder
    (also the name of the PDF later on)
    """
    last_slash = url.rindex('/')
    folder_name = url[last_slash + 1::]

    """
    Create a directory and a subdirectory to put the images to download in
    """
    subprocess.run(['mkdir', '-p', folder_name + '/' + "combined"])

    response = requests.get(url)

    soup = BeautifulSoup(response.text, "html.parser")
    
    
    #Obtain all img tags at the specified URL
    image_links = soup.find_all("img")

    images_to_convert = []
    for image in image_links:

        #Obtain the URL of the image on in each img tag
        image_to_download = image["src"]
        
        #Only want the URLs that begin with http or https
        if re.search('^http|^https', image_to_download):
            last_slash = image_to_download.rindex('/')
            file_name = image_to_download[last_slash + 1::]
            subprocess.run(['curl', '-o', folder_name + '/' + file_name, image_to_download])
            images_to_convert.append(file_name)

    #Create a list of single Image objects (not combined side by side)
    images = []
    for f in images_to_convert:
        try:
            images.append(Image.open('./' + folder_name + '/' + f))
        except UnidentifiedImageError: 
            traceback.print_exc()


    #Removes 'RGBA' warning
    rgb_images = []
    for image in images:
        rgb_images.append(image.convert('RGB'))
    
    iter_max = len(rgb_images)
    file_name = folder_name + '/combined/image_0.jpg'

    """ For for manga, oftentimes the first page, so we
        it on it's own page
    """

    i = 0
    combined_images = []
    if offset == 'single' or offset == 's':
        combined_images.append(file_name)
        if len(rgb_images) != 0:
            rgb_images[0].save(file_name)
        i = 1
    elif offset == 'double' or 'd':
        pass

    while i < iter_max:
        max_height = 0
        total_width = 0
        try:
            # If the width is greater than 1400, put that image on it's own page
            if rgb_images[i].size[0] > 1400 or i == iter_max - 1 or (rgb_images[i].size[0] < 1300 and rgb_images[i + 1].size[0] > 1400 and i != 1):
                file_name = folder_name + "/combined/image_" + str(i) + ".jpg"
                rgb_images[i].save(file_name)
                combined_images.append(file_name)
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
                file_name = folder_name + "/combined/image_" + str(i) + ".jpg"
                # Create a new image, combinding two images side by side
                for img in image_array:
                    new_img.paste(img, (current_width,0))
                    current_width += img.size[0]
                new_img.save(file_name)
                combined_images.append(file_name)
                i += 2
        except KeyboardInterrupt:
            traceback.print_exc()
            quit()
        except:
            traceback.print_exc()
    #Write the opened combined Images to a new list
    images = []
    for f in combined_images:
        images.append(Image.open(f))

    pdf_path = "./" + folder_name + ".pdf"
    
    #Save the combined images in a new pdf
    images[0].save(
            pdf_path, "PDF" ,resolution=100.0, save_all=True, append_images=images[1::]
    )

    #Cleanup images in directory
    subprocess.run(['rm', '-rf', folder_name])

if __name__ == '__main__':
    main()
