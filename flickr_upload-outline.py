#OUTLINE OF flickr_upload.py

import json
import os
import shutil
import time
import flickrapi
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xml.etree.ElementTree as ET


class bcolors:
    """
    9 Colours for CLI printing
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
    """

if __name__ == '__main__':
    
    print_starting_prompt()

    input1 = input()
    while (input1 != "3"):
        if input1 == "1":
            print("Enter the name of the excel file in the data folder(e.g 'MineralData.xlsx'):")
            # not outlined yet
            # parses spreadsheet to generate tags and descriptions, then generates a new spreadsheet for uploading
            # NOTE - this could be skipped if spreadsheet is OK to begin with.
            # also counts specimen types and generates histogram image. Could be ignored if not needed.

        elif input1 == "2":
            #fetch *.xlsx filename and excel sheet to be uploaded

            df = load_excel_sheet(dataset_file_path, sheet)
            # Loads an excel file into a pandas dataframe. Fills in empty cell values with the empty string

            images, ids = load_images_and_ids(images_path)
            # Returns a list of image file paths and their filenames (which are also their ID's)

            parse_photo_info_and_upload(images, ids, df, sheet)
            # Given the image list, find image metadata of the corresponding ID then upload image & metadata
                def get_valid_api_token(api):
                # Start by fetching and authenticating the Flickr API key
                def upload_photo(api, image_info, image_path):
                # Upload photo and get the ID.
                def geotag_images(api, photo_id, image_info):
                # Geotag an image once it has been uploaded

            print("Complete!")
            # if successful - if error messages are printed where failed in methods above.

        else:
            print(f"{bcolors.FAIL}Invalid option, try again?{bcolors.ENDC}")

        print()
        print()
        print_starting_prompt()
        input1 = input()

    print(f"{bcolors.OKBLUE}Goodbye!{bcolors.ENDC}")






