from zipfile import ZipFile
import pathlib

from PIL import Image

import pytesseract
import cv2 as computer_vision
import numpy as np


def find_faces(source_image):
    ''' detect faces on each page and returns list of location coordinates for every face found

    :param:
        source_image (PIL image): image being scanned for faces

    :return:
        faces (list): list of tuples containing coordinates of each face found on image
    '''

    # loading the face detection classifier
    face_cascade = computer_vision.CascadeClassifier('readonly/haarcascade_frontalface_default.xml')

    # convert image into color array
    cv_image = np.array(source_image)

    # convert RGB into gray scale
    gray_image = computer_vision.cvtColor(cv_image, computer_vision.COLOR_RGB2GRAY)

    # scan image for faces and store all 4-tuple coordinates into list
    faces = face_cascade.detectMultiScale(gray_image, 1.15, minNeighbors=11, minSize=(45, 45))

    return faces


def query_found(page_image, query):
    ''' search image for given word and return true if found

    :param:
        page_image (PIL image): image being searched for given word

        query (str): word we are looking for

    :return:
        (True) if query found else (False)
    '''

    # convert image into black and white before searching for words
    binary_image = page_image.convert('1')

    # search image for text and store all recognized text into string
    text = pytesseract.image_to_string(binary_image)


    # we will store all recognized words into a set to filter duplicate words
    word_set = set()
    # make string lowercase to keep letter case consistent,
    # and then split string into separate words so we can compare them to our search word
    word_set.update(text.lower().split())

    # search for "name" in page text
    search_word = query

    # check set for our search word and return if found or not
    if search_word in word_set:
        return True
    else:
        return False


def create_contact_sheet(source_image, face_coordinates):
    ''' create contact sheet from image pulled from source image using all face coordinates

    :param:
        source_image (PIL image): image we are pulling faces from and placing together into a contact sheet

        face_coordinates (list): list of 4-tuple coordinates of faces in source image
    '''

    face_image_list = []

    # sizes of individual images in the contact sheet
    grid_image_width = 100
    grid_image_height = 100

    for face in face_coordinates:
        # copy image to avoid destroying original image, because crop function alters the image calling it
        copy_image = source_image.copy()

        ## couldnt figure out how to get image format to fit for resize()
        ## and use box parameter to crop image so,
        ## temporarily using this hackneyed solution, with extra steps:

        # convert image into color array
        color_array = np.array(copy_image)

        # so we can use array slicing to crop out face image
        cropped_image = color_array[face[1]:face[1] + face[3], face[0]:face[0] + face[2]]

        # convert color array into RGB image
        RGB_image = Image.fromarray(cropped_image, mode="RGB")

        # resizing each image to fit contact sheet before adding it to face image list
        face_image_list.append(RGB_image.resize((grid_image_width, grid_image_height)))

    # get number of rows for contact sheet:
    contact_sheet_rows = (len(face_image_list) // 5)
    # add new row if we have more than 5 images
    if (len(face_image_list) % 5) > 0:
        contact_sheet_rows += 1

    # create new contact sheet
    contact_sheet = Image.new("RGB", (grid_image_width * 5, grid_image_height * contact_sheet_rows))
    x = 0
    y = 0

    for image in face_image_list:
        # add images from list into contact sheet
        contact_sheet.paste(image, (x, y))

        # if we reach the right edge of contact sheet,
        # reset x to 0 and move down a row
        if x + grid_image_width >= contact_sheet.width:
            x = 0
            y += grid_image_height

        # otherwise, we move to the right of the newly added image
        else:
            x += grid_image_width

    contact_sheet.show()
    # display(contact_sheet)


# retrieve zipfile
with ZipFile(pathlib.Path.cwd() / "readonly/images.zip", 'r') as zipfile:

    # get list of file names inside zip file
    list_of_files = zipfile.namelist()

    # retrieve images from zip file
    image_list = []
    for file_name in list_of_files:
        image_file = zipfile.open(file_name)
        image = Image.open(image_file)
        image_list.append(image)


# get search word from user input
query = input("Enter search word: ").lower()

page_number = 0
for page_image in image_list:

    # go through each page image and searching for our query,
    # and if found displaying any faces on the page
    if query_found(page_image, query) is True:
        list_of_faces = find_faces(page_image)
        print("Results found in file {}".format(list_of_files[page_number]))

        # display faces if any found
        if len(list_of_faces) > 0:
            create_contact_sheet(page_image, list_of_faces)

        # or report if no faces were found on page
        else:
            print("But there were no faces in that file!")
    page_number += 1
