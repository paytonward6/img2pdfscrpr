from tkinter import *     
#from tkinter.ttk import * 
from PIL import Image, ImageTk
from tkinter import filedialog
import os
import subprocess
from pdf2image import convert_from_path

filename = str(input("Input a PDF path to view: "))
filename.strip()
    
root = Tk()
root.current_image = -1
screen_width, screen_height = root.maxsize()

#filename = 'one-piece-chapter-1052.pdf'

directory = "./" + str(filename).replace(".pdf", "")
if not os.path.isfile(filename):
    print("Must specify valid PDF to view")
    quit()

photos = []
def init(photos):
    print('init')
    pages = convert_from_path(filename)
    print(pages)
    # opens the image
    # resize the image and apply a high-quality down sampling filter
    #btn.update()
    size_adjustment = 32 #btn.winfo_reqheight()
    for i in range(len(pages)):
        width, height = pages[i].size[0], pages[i].size[1]
        pages[i] = pages[i].resize((int(width * ((screen_height - size_adjustment)/height)), int(screen_height - size_adjustment)), Image.ANTIALIAS)

        # PhotoImage class is used to add image to widgets, icons etc
        photos.append(ImageTk.PhotoImage(pages[i]))

def reload_photos(photos):
    print("reload")
    photos = []
    pages = convert_from_path(filename)
    # opens the image
    # resize the image and apply a high-quality down sampling filter
    #btn.update()
    size_adjustment = 32 #btn.winfo_reqheight()
    for i in range(len(pages)):
        width, height = pages[i].size[0], pages[i].size[1]
        pages[i] = pages[i].resize((int(width * ((screen_height - size_adjustment)/height)), int(screen_height - size_adjustment)), Image.ANTIALIAS)

        # PhotoImage class is used to add image to widgets, icons etc
        photos.append(ImageTk.PhotoImage(pages[i]))
init(photos)
def new_page():
    # create a label
    root.current_image += 1
    print(root.current_image)
    panel = Label(bottomframe, image = photos[root.current_image])
    
    # set the image as img
    panel.image = photos[root.current_image]
    panel.pack()#.grid(column = 1, row = 2)

def next_image(event):
    print('left')
    root.current_image += 1
    if root.current_image < len(photos):
        for widget in bottomframe.winfo_children():
            widget.destroy()
        panel = Label(bottomframe, image = photos[root.current_image])
        panel.image = photos[root.current_image]
        panel.focus()
        panel.pack()#.grid(column = 1, row = 2)

def previous_image(event):
    print('left')
    for widget in bottomframe.winfo_children():
        widget.destroy()
    root.current_image -= 1
    if root.current_image < 0:
        root.current_image = 0
    panel = Label(bottomframe, image = photos[root.current_image])
    panel.image = photos[root.current_image]
    panel.focus()
    panel.pack()#.grid(column = 1, row = 2)

#def printInput(event):
#    inp = inputtxt.get(1.0, "end-1c")
#    lbl.config(text = "Provided Input: "+inp)   
# Create a window

frame = Frame(root)
bottomframe = Frame(root)
frame.pack(side = TOP)
root.bind('<Left>', next_image)
root.bind('<Right>', previous_image)
bottomframe.pack(side = BOTTOM)

# Set Title as Image Loader
root.title(filename)

# Set the resolution of window
root.geometry(f"{screen_width}x{screen_height}")

# Allow Window to be resizable
root.resizable(width = True, height = True)

# Create a button and place it into the window using grid layout
btn = Button(frame, text ='open pdf', command = (lambda: new_page()))
btn.pack(side = LEFT)#grid(row = 1, columnspan = 1, sticky="NSEW")

reload_btn = Button(frame, text ='reload pdf', command = (lambda: reload_photos(photos)))
reload_btn.pack(side = LEFT)#grid(row = 1, columnspan = 1, sticky="NSEW")

#url_field = Text(frame, height = 5, width = 20)
#url_field.pack(side = LEFT)
#
#printButton = Button(frame,
#                        text = "Print",
#                        command = (lambda: printInput()))
#printButton.pack()
#lbl = Label(frame, text = "")
#lbl.pack()
root.mainloop()
