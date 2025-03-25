# FJ EXPERIMENTING TOWARDS CODE TO ADJUST METADATA ONLY (NOT UPLOADING IMAGES)

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


def geotag_images(api, photo_id, image_info):
    """
    Step 04.4
    Geotags an image once it has been uploaded to flickr using its associated
    photoID on flickr
    :param api:
    :param photo_id:
    :param image_info:
    :return:
    """
    geocoordinates = image_info["Geotag"].values[0].replace(" ", "").split(",")
    if geocoordinates[0] != "":
        response = api.photos.geo.setLocation(photo_id=photo_id,
                                              lat=geocoordinates[0],
                                              lon=geocoordinates[1],
                                              accuracy=image_info["Geotag Accuracy"].values[0],
                                              context=1)
        time.sleep(0.20)
        if response.get("stat") != "ok":
            print(f"{bcolors.FAIL}{response.text}{bcolors.ENDC}")
            return None
        else:
            return 1
    else:
        return 1


def add_image_to_album(api, photo_id, photoset_title):
    """
    Step 4.3
    Add photo to photoset. If the photoset doesn't exist, create it
    :param api: FlickrAPI object.
    :param photo_id: uploading photo's ID.
    :param photoset_title: adding the photo to this photoset.
    :returns bphotoset ID fot photo to be added.
    """

    response = api.photosets.getList()
    time.sleep(0.3)

    # Example Response
    # <photosets page="1" pages="1" perpage="30" total="2" cancreate="1">
    #   <photoset id="72157626216528324" primary="5504567858" photos="22" videos="0" date_create="1299514498" date_update="1300335009">
    #     <title>Avis Blanche</title>
    #     <description>My Grandma's Recipe File.</description>
    #   </photoset>
    #   <photoset id="72157624618609504" primary="4847770787" photos="43" videos="12" date_create="1280530593" date_update="1308091378">
    #     <title>Mah Kittehs</title>
    #     <description>Sixty and Niner. Born on the 3rd of May, 2010, or thereabouts. Came to my place on Thursday,</description>
    #   </photoset>
    # </photosets>
    # NOTE: This method will keep working until number of photosets/albums is less than 500, after that the response
    # will be paginated and this method will need to be updated to handle that.

    id_ = None
    
    photosets_rsp = list(response)[0]
    if photosets_rsp == None:
        print("Flickr list photos response not working")
        print(ET.tostring(response, encoding="utf-8").decode())
    for photosets in photosets_rsp.iter("photoset"):
        for photoset_attrib in photosets:
            if photoset_attrib.tag == "title" and photoset_attrib.text == photoset_title:
                id_ = photosets.get("id")
                break
        

    if id_ is not None:
        response = api.photosets.addPhoto(
            photoset_id=id_,
            photo_id=photo_id)
    else:
        response = api.photosets.create(
            title=photoset_title,
            description="",
            primary_photo_id=photo_id)

        id_ = response.find("photoset").get("id") if response.get("stat") == "ok" else None

    return id_


def parse_WithMinerals_for_title(with_string):
    # This complexe parsing would not be needed if "Description" was generated in the spreadsheet.
    """
    Step 04.2.2
    Given a comma separated list of words e.g "X, Y, Z", output the same with an "and" inserted
    :param with_string: Input string list of words
    :return: "X, Y, and Z"
    """
    if with_string == "":
        return ""
    spliced_string = with_string.replace(" ", "").split(",")
    if len(spliced_string) == 1:
        return " and " + spliced_string[0]
    last_word = spliced_string[-1]
    spliced_string[-1] = f"and {last_word}"
    result = ""
    for word in spliced_string:
        result = result + ", " + word
    return result


def reparse_tags_string(input_tags_string):
    """
    Step 04.2.1
    Adds whitespace and removes '[' and ']' characters from tags string

    :param input_tags_string:
    :return:
    """
    output_tags_string = ""
    input_tags_string = input_tags_string.replace(" ", "").replace("'", "").replace("[", "")
    input_tags_string = input_tags_string.replace("]", "").split(",")
    for x in input_tags_string:
        output_tags_string += x + " "
    return output_tags_string[0:-1]


def upload_photo(api, image_info, image_path):
    """
    Step 04.2
    Using the Flickr API, a dataframe row containing image info, and a file path to the image
    This function uploads the image with its associated info to flickr
    """
    # res is instance of xml.etree.ElementTree.Element.
    # This element has something like "<rsp><photoid>1234</photoid></rsp>".
    tag_string = reparse_tags_string(image_info["Tags"].values[0])
    title_string = image_info["Title"].values[0] + parse_WithMinerals_for_title(image_info["With Minerals"].values[0])
    response = api.upload(filename=image_path,
                          title=title_string,
                          tags=tag_string,
                          is_private=False,
                          description=image_info["Upload Description"].values[0],
                          content_type=1)
    # Wait to avoid overusing API
    time.sleep(0.20)
    if response.get("stat") != "ok":
        print(response)
        return None
    else:
        # Get the uploaded photo's ID.
        return response.find("photoid").text


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


def upload_image_to_album(image_info, image_path, album_name):
    '''
    Step 04
    Start by fetching and authenticating the Flickr API key

    '''
    # could this be removed from this method so it's not run for each and every image?
    with open("access_keys.json", "r") as file:
        file_json = json.load(file)
    api_key = file_json["api_key"]
    secret_key = file_json["secret_key"]
    api = flickrapi.FlickrAPI(api_key, secret_key, cache=True)
    flickrapi.cache = flickrapi.SimpleCache(timeout=3000, max_entries=400)
    # I think that api authorization happens only once on any computer since authorization is saved.

    if not api.token_valid():
        get_valid_api_token(api)

    # Upload photo and get the unique photo ID assigned by Flickr.
    upload_id = upload_photo(api, image_info, image_path)

    if not upload_id:
        print(f"{bcolors.FAIL}flickrapi.upload({image_path}) failed{bcolors.ENDC}")
        exit(1)
    else:
        print(f"{bcolors.OKGREEN}Uploaded {image_path} successfully!{bcolors.ENDC}")

    album_id = add_image_to_album(api, upload_id, album_name)

    if not album_id:
        print(f"{bcolors.FAIL}flickrapi.photosets failed? ({album_id}, {image_path}){bcolors.ENDC}")
    else:
        print(f"{bcolors.OKGREEN}Added {image_path} to {album_name} successfully!{bcolors.ENDC}")
        res = geotag_images(api, upload_id, image_info)
        if res == 1:
            print(f"{bcolors.OKGREEN}Geotagged {image_path} successfully!{bcolors.ENDC}")
        else:
            print(f"{bcolors.FAIL}Error in geotagging {image_path}{bcolors.ENDC}")


def parse_photo_info_and_upload(image_paths, image_ids, dataset, album_name):
    """
    Step  03
    Given a list of images in a folder, find the image metadata of the corresponding ID in the
    dataset, then upload the image along with its metadata
    """
    for index, image_id in enumerate(image_ids):
        image_info = dataset.loc[dataset['Specimen #'] == int(image_id)]
        upload_image_to_album(image_info, image_paths[index], album_name)

def load_image_paths_and_ids(images_file_path):
    """
    Step 02
    Return a list of image file paths and their filenames (i.e. their local -not Flickr- ID's)
    """
    image_paths = os.listdir(images_file_path)
    image_ids = []
    for index, image in enumerate(image_paths):
        image_ids.append(image.split("-")[-1].split(".")[0])
        image_paths[index] = f"uploadPhotos/{image_paths[index]}"

    return image_paths, image_ids


def load_excel_sheet(excel_file_path, sheet_name):
    """
    Step 01
    Load an excel file into a pandas dataframe. Fills in empty cell values with the empty string
    """
    dataframe = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype={"Specimen #": int})
    # print(dataframe['Specimen #'].unique())
    dataframe.fillna("", inplace=True)
    print(f"{bcolors.OKGREEN}Loaded Excel file: {excel_file_path} and sheet: {sheet_name}{bcolors.ENDC}\n")
    return dataframe


def update_metadata(dfrow):
    '''
    Upload new metadata to images defined by "Flickr-ID" given in the spreadsheet
    '''
    specimen = (dfrow["Spec-No_final"])
    print(f"Reading specimen number {specimen}")

    with open("access_keys.json", "r") as file:
        file_json = json.load(file)
    api_key = file_json["api_key"]
    secret_key = file_json["secret_key"]
    api = flickrapi.FlickrAPI(api_key, secret_key, cache=True)
    flickrapi.cache = flickrapi.SimpleCache(timeout=3000, max_entries=400)
    # I think that api authorization happens only once on any computer since authorization is saved.

    if not api.token_valid():
        get_valid_api_token(api)

    #post new name & description to the image defined by Flickr_id
    response = api.photos.setMeta(photo_id=dfrow["Flickr_ID"],
                                  title=dfrow["name"],
                                  description=dfrow["description"])
    time.sleep(0.20)
    if response.get("stat") != "ok":
        print(f"{bcolors.FAIL}{response.text}{bcolors.ENDC}")
        return 0

    #post new geolocation to the image defined by Flickr_id
    response = api.photos.geo.setLocation(photo_id=dfrow["Flickr_ID"],
                                          lat=dfrow["lat"],
                                          lon=dfrow["long"],
                                          accuracy=dfrow["accuracy"],
                                          context=0)  #was 1 - but API docs says it should be 0.
    time.sleep(0.20)
    if response.get("stat") != "ok":
        print(f"{bcolors.FAIL}{response.text}{bcolors.ENDC}")
        return 0

    #update tags
    response = api.photos.setTags(photo_id=dfrow["Flickr_ID"],
                                  tags=dfrow["tags"])
    time.sleep(0.20)
    if response.get("stat") != "ok":
        print(f"{bcolors.FAIL}{response.text}{bcolors.ENDC}")
        return 0

    #update permissions

    #update dates (including granularity - see flickr API docs)

    return 1

def Fix_all_image_metadata(df):
    '''
    Iterate through all images needing updated metadata
    '''
    #how many rows?
    nrows = len(df.index)

    for row in range(nrows):
        #specimen = (df["Spec-No_final"][row])
        #print(f"dummy step for specimen number {specimen}")
        response = update_metadata(df.loc[row])
        if response == 0:
           return response

    return 1


def print_starting_prompt():
    print("Hello, what would you like to do? Enter the corresponding number")
    print("1) Upload images")
    print("2) Update metadata for existing Flickr images. ASSUMES ALL Flickr ID's ARE KNOWN.")
    print("3) fetch metadata")
    print("4) Exit")


def fetch_metadata(photo_id):
    '''
    Fetch metadata for image specified by photo_id
    '''
    with open("access_keys.json", "r") as file:
        file_json = json.load(file)
    api_key = file_json["api_key"]
    secret_key = file_json["secret_key"]
    api = flickrapi.FlickrAPI(api_key, secret_key, cache=True, format='parsed-json')
    flickrapi.cache = flickrapi.SimpleCache(timeout=3000, max_entries=400)
    # I think that api authorization happens only once on any computer since authorization is saved.

    if not api.token_valid():
        get_valid_api_token(api)

    #fetch data for one image
    info = api.photos.getInfo(photo_id='47700366102')
    print(info['photo']['title']['_content'])
    print(info['photo']['location']['latitude'])
    print(info['photo']['location']['longitude'])

    #locn = api.photos.getInfo(photo_id='47700366102')
    #print(locn['photo']['location']['latitude'])
    #print(locn['photo']['location']['longitude'])

    return 1


if __name__ == '__main__':
    data_folder = "data"
    dataset_file_path = "data/MineralData.xlsx"
    sheet = "Cabinet 20"
    images_path = "uploadPhotos"

    print()
    print("^ The above beep boop is intended, please ignore ^")
    print()
    print_starting_prompt()

    input1 = input()
    while (input1 != "4"):
        if input1 == "1":
            # The upload images choice
            
            print("Enter the name of the excel file in the data folder(e.g MineralData.xlsx)")
            print("Make sure it is the file that has the autogenerated tags in it! :")
            dataset_file_path = f"{data_folder}/{input()}"
            print("Enter the name of the sheet you want to work with (e.g 'Cabinet 20')")
            sheet = input()

            df = load_excel_sheet(dataset_file_path, sheet)
            images, ids = load_image_paths_and_ids(images_path)
            parse_photo_info_and_upload(images, ids, df, sheet)

            print("Complete!")

        elif input1 == "2":
            # The update metadata for existing images choice.

            #print("Enter the name of the excel file containing Flickr ID's and corresponding new metadata.")
            #dataset_file_path = f"{data_folder}/{input()}"
            #print("Enter the name of the sheet in that excel file that you want to work from (e.g 'Cabinet 20')")
            #sheet = input()

            dataset_file_path = "data/FixMetadata.xlsx"
            sheet = "update"

            df = load_excel_sheet(dataset_file_path, sheet)
            response = Fix_all_image_metadata(df)

            if response == 1:
                print(f"{bcolors.OKGREEN}Updated successfully!{bcolors.ENDC}")
            else:
                print(f"{bcolors.FAIL}Error updating metadata.{bcolors.ENDC}")

        elif input1=="3":
            # fetch metadata - no data frame needed yet

            response = fetch_metadata('47700366102')

            if response == 1:
                print(f"{bcolors.OKGREEN}Metadata fetched successfully!{bcolors.ENDC}")
            else:
                print(f"{bcolors.FAIL}Error fetching metadata.{bcolors.ENDC}")

        else:
            print(f"{bcolors.FAIL}Invalid option, try again?{bcolors.ENDC}")
        
        print()
        print()
        print_starting_prompt()
        input1 = input()

    print(f"{bcolors.OKBLUE}Goodbye!{bcolors.ENDC}")

