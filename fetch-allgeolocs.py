# FETCH GEOLOCATIONS WITH IMAGE URL FOR IAMGES LISTED IN SPREADSHEET.

import json
import os
import time
import flickrapi
import pandas as pd
import xml.etree.ElementTree as ET

class bcolors:
    """
    Colours for CLI printing
    https://stackoverflow.com/questions/287871/how-to-print-colored-text-to-the-terminal
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_excel_sheet(excel_file_path, sheet_name):
    """
    Load an excel file into a pandas dataframe. Fills in empty cell values with the empty string
    """
    dataframe = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype={"Specimen #": int})
    # print(dataframe['Specimen #'].unique())
    dataframe.fillna("", inplace=True)
    print(f"{bcolors.OKGREEN}Loaded Excel file: {excel_file_path} and sheet: {sheet_name}{bcolors.ENDC}\n")
    
    return dataframe

def get_valid_api_token(api):
    """
    Step 04.1
    Using the flickr api, it verifies the user using a request token, and then authenticates using the
    access token
    :param api:
    :return:
    """
    # OOB: out of band
    api.get_request_token(oauth_callback="oob")
    verifier = str(input(f"Get verifier code from {api.auth_url(perms='write')} and enter it here.\n: "))
    # Get access token and store it as ${HOME}/.flickr/oauth-tokens.sqlite.
    # If you want to remove the cache, call api.token_cache.forget().
    api.get_access_token(verifier)

if __name__ == '__main__':
    data_folder = "data"
    with open("access_keys.json", "r") as file:
        file_json = json.load(file)
    api_key = file_json["api_key"]
    secret_key = file_json["secret_key"]
    api = flickrapi.FlickrAPI(api_key, secret_key, cache=True, format='parsed-json')
    flickrapi.cache = flickrapi.SimpleCache(timeout=3000, max_entries=400)

    if not api.token_valid():
        get_valid_api_token(api)

    #open blank CSV file
    outf = open("geolocns.csv", "w", encoding="utf-16") #re-write, NOT appending.

    #NOTE: use tabs not commas to avoid confusion when Excel opens the CSV file
    toprow = "Flickr-ID\tFlickr-URL\taccuracy\tlat\tlong\n"

    outf.write(toprow)
    #file is now open, don't forget to close it.

    dataset_file_path = "data/Fetch-Geolocns.xlsx"
    sheet = "sheet1"

    df = load_excel_sheet(dataset_file_path, sheet)
    #print(df.info())
    #print(df["Flickr-ID"].head())

    imagelist = df['Flickr-ID'].values.tolist()
    nrows = len(imagelist)
    #print(nrows)
    #print(imagelist[0])

    #range hard wired to suit the needs of this fetch.
    for row in range(1060, 8063):  #first fetch stoped at row 1063 - this one starts a few back to check consistncy.
        #fetch data for one image
        info = api.photos.getInfo(photo_id=imagelist[row])

        url = f"https://www.flickr.com/photos/pmeubc/{imagelist[row]}"
        fid = imagelist[row]

        #handling blank data fields - from https://labex.io/tutorials/python-how-to-handle-keyerror-when-accessing-nested-keys-in-a-python-json-object-395073
        try:
             acc = info['photo']['location']['accuracy']
        except KeyError as e:
               acc = 0
        try:
             lat = info['photo']['location']['latitude']
        except KeyError as e:
             lat = 0
        try:
             lon = info['photo']['location']['longitude']
        except KeyError as e:
             lon = 0

        #print(f"ID = {fid} lat = {lat}, lon = {lon}, acc = {acc}")

        string = f"{fid}\t{url}\t{acc}\t{lat}\t{lon}\n"
        outf.write(string)

        if row%50 == 0:
           print(f"Image number {row} done, out of {nrows}.")
           time.sleep(0.20)

    print(f"{bcolors.OKBLUE}All {row} images done; goodbye!{bcolors.ENDC}")

    #save and close the file
    outf.close()
