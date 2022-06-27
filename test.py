from PIL import Image

# Open images and store them in a list
images = [Image.open(x) for x in ['./one-piece-chapter-1052/op_tcb_1052morning_01.png', './one-piece-chapter-1052/op_tcb_1052morning_003.png']]
total_width = 0
max_height = 0


# find the width and height of the final image
for img in images:
    total_width += img.size[0]
    print(img.size[0])
    max_height = max(max_height, img.size[1])
#
## create a new image with the appropriate height and width
#new_img = Image.new('RGB', (total_width, max_height))
#
## Write the contents of the new image
#current_width = 0
#for img in images:
#  new_img.paste(img, (current_width,0))
#  current_width += img.size[0]
#
## Save the image
#new_img.save('NewImage.jpg')
