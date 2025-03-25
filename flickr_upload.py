# ORIGINAL PME's CODE WITH OPTIONS FOR IMAGE UPLOAD OR MAKE HISTOGRAM
# AUGMENTED WITH EXTRA COMMENTS TO HELP DECIFER THE SEQUENCE OF STEPS
# Image upload was successfully tested by FJ in Feb 2025. Histogram code NOT tested at that time.

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


def upload_photo(api, image_info, image_path):
    """
    Step 04.2
    Using the Flickr API, a dataframe row containing image info, and a file path to the image
    This function uploads the image with its associated info to flickr
    """
    # res is instance of xml.etree.ElementTree.Element.
    # This element has something like "<rsp><photoid>1234</photoid></rsp>".
    tag_string = reparse_tags_string(image_info["Tags"].values[0])
    title_string = image_info["Title"].values[0] + parse_with_minerals_for_title(image_info["With Minerals"].values[0])
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


def add_image_to_album(api, photo_id, photoset_title):
    """
    Step 07
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


def geotag_images(api, photo_id, image_info):
    """
    Steo 04.3
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


def upload_image_to_album(image_info, image_path, album_name):
    '''
    Step 04
    Start by fetching and authenticating the Flickr API key
    '''
    with open("access_keys.json", "r") as file:
        file_json = json.load(file)
    api_key = file_json["api_key"]
    secret_key = file_json["secret_key"]
    api = flickrapi.FlickrAPI(api_key, secret_key, cache=True)
    flickrapi.cache = flickrapi.SimpleCache(timeout=3000, max_entries=400)

    if not api.token_valid():
        get_valid_api_token(api)

    # Upload photo and get the ID.
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


def parse_tags(mineral_data):
    """
    Tags = Title + with minerals + location + special features
    :param mineral_data:
    :return:
    """
    # print(mineral_data["Specimen #"])
    tags = ["pacific museum of earth", "pmeubc", "ubc", mineral_data["Title"]]
    if mineral_data["With Minerals"] != "":
        tags.extend(mineral_data["With Minerals"].replace(" ", "").split(","))
    if mineral_data["Location"] != "":
        tags.extend(mineral_data["Location"].replace(" ", "").split(","))
    if mineral_data["Special Features"] != "":
        tags.extend(mineral_data["Special Features"].replace(" ", "").split(","))
    return tags


def reparse_tags_string(input_tags_string):
    """
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


def parse_with_minerals_for_title(with_string):
    """
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


def create_upload_description(mineral_data):
    """
    Creates a text string that is used as the description body for the flickr upload
    The contents of the text string are extracted and formatted from the mineral's row entry.
    The string is formatted as such:

    'Text description
    Location
    Special Features
    Sample Number'

    :param mineral_data:
    :return: description string
    """

    description = ""
    # print(mineral_data["Specimen #"])
    if mineral_data["Text Description"] != "":
        description += mineral_data["Text Description"] + "\n\n"
    if mineral_data["Location"] != "":
        description += mineral_data["Location"] + "\n\n"
    if mineral_data["Special Features"] != "":
        description += "Special Features: " + mineral_data["Special Features"] + "\n\n"
    description += str(mineral_data["Specimen Prefix"]) + "-" + str(mineral_data["Specimen #"])
    # print(description)
    return description


def update_tags_and_description(dataset_row):
    """
    Creates a string list of tags and string description used on flickr for each mineral

    :param dataset_row: Pandas dataframe row
    :return:
    """
    if dataset_row["Upload Description"] not in ["EB", "M"] and dataset_row["Unnamed"] != True:
        # print(dataset_row["Specimen #"])
        tags = parse_tags(dataset_row)
        description = create_upload_description(dataset_row)
        dataset_row["Upload Description"] = description
        dataset_row["Tags"] = tags
        return dataset_row
    else:
        return dataset_row


def load_images_and_ids(images_file_path):
    """
    Step 02
    Returns a list of image file paths and their filenames (which are also their ID's)
    """
    image_paths = os.listdir(images_file_path)
    image_ids = []
    for index, image in enumerate(image_paths):
        image_ids.append(image.split("-")[-1].split(".")[0])
        image_paths[index] = f"uploadPhotos/{image_paths[index]}"

    return image_paths, image_ids


def parse_photo_info_and_upload(image_paths, image_ids, dataset, album_name):
    """
    Step  03
    Given a list of images in a folder, it finds the image metadata of the corresponding ID in the
    dataset, then uploads the image along with its metadata
    """
    for index, image_id in enumerate(image_ids):
        image_info = dataset.loc[dataset['Specimen #'] == int(image_id)]
        upload_image_to_album(image_info, image_paths[index], album_name)


def load_excel_sheet(excel_file_path, sheet_name):
    """
    Step 01
    Loads an excel file into a pandas dataframe. Fills in empty cell values with the empty string
    """
    dataframe = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype={"Specimen #": int})
    # print(dataframe['Specimen #'].unique())
    dataframe.fillna("", inplace=True)
    print(f"{bcolors.OKGREEN}Loaded Excel file: {excel_file_path} and sheet: {sheet_name}{bcolors.ENDC}\n")
    return dataframe


def fill_up_dataset_tags_and_description(dataset, dataset_path, sheet_name):
    """
    Given a pandas dataset, path to an excel file, and an output sheet name
    It writes the dataset to the given sheet name.
    A copy of the original excel sheet is made
    """
    shutil.copyfile(dataset_path, "data/UpdatedMineralDataset.xlsx")
    dataset = dataset.apply(func=update_tags_and_description, axis="columns", result_type="broadcast")

    with pd.ExcelWriter('data/UpdatedMineralDataset.xlsx', mode='a', if_sheet_exists="replace") as writer:
        dataset.to_excel(writer, sheet_name=sheet_name, index=False)
        print("v Ignore the message below and wait a few seconds for the new file to save v")
        writer.save()

    print(f"{bcolors.OKGREEN}Finished saving updated {sheet_name} to new excel file!{bcolors.ENDC}\n")


def get_mineral_histogram(dataset, yes_print, hist, sheet_name):
    """
    Filters the datasheet by removing empty box, missing and unnamed rows.
    Then returns histogram objects of numpy format
    """
    len1 = dataset.shape[0]
    dataset = dataset[dataset['Upload Description'] != "EB"]
    dataset = dataset[dataset['Upload Description'] != "M"]
    dataset = dataset[dataset['Unnamed'] != True]
    len2 = dataset.shape[0]
    print(f"{bcolors.OKGREEN}Filtered {len1 - len2} unnamed, missing and empty mineral box entries{bcolors.ENDC}")
    titles = np.asarray(dataset["Title"])
    with_minerals = []
    for value in dataset["With Minerals"]:
        if value != "":
            with_minerals.extend(value.replace(" ", "").split(","))

    minerals = np.append(titles, np.asarray(with_minerals))
    bins, counts = np.unique(minerals, return_counts=True)

    if yes_print: print_mineral_counts(bins, counts)
    if hist: print_mineral_histogram(bins, counts, sheet_name)


def print_mineral_counts(bins, counts):
    """
    Helper for print_mineral_histogram, only prints counts
    """
    for i in range(len(counts)):
        print(f"{bcolors.OKCYAN}{bins[i]}: {counts[i]}{bcolors.ENDC}")
    print(f"\n{bcolors.OKCYAN}Number of unique minerals: {len(counts)}{bcolors.ENDC}")


def print_mineral_histogram(bins, counts, sheet_name):
    """
    Saves a histogram of minerals appearing more than 5 times, and prints the entire counts for all minerals in the
    cabinet sheet
    """
    modded_bins = []
    modded_counts = []
    for i in range(len(counts)):
        if counts[i] > 5:
            modded_bins.append(bins[i])
            modded_counts.append(counts[i])
        # else:
        #     modded_counts[0] += counts[i]
    plt.figure(figsize=(10, 10))
    plt.title('Minerals with more than 5 samples')
    plt.hist(modded_bins, modded_bins, weights=modded_counts, orientation='horizontal', align='left', rwidth=0.5)
    plt.savefig(f'data/{sheet_name} Mineral Histogram.png')


def print_prior_data_histogram(path, sheet_name, output_file):
    """
    This function was made to read the format of the older Cabinet sheets (prior to Cabinet 14)
    to get their summary statistics
    """
    dataframe = pd.read_excel(path, sheet_name=sheet_name)
    dataframe.fillna("", inplace=True)
    dataframe = dataframe[dataframe["Title"] != ""]
    titles = np.asarray(dataframe["Title"])

    mineral_array = []

    with open(output_file, "w") as file:
        for title in titles:
            if " and " in title or " with " in title or "," in title or " in " in title:
                word_array = []
                parsed1 = []
                parsed2 = []
                parsed3 = []
                final_parsed = []

                if " and " in title:
                    word_array = title.split(" and ")
                else:
                    word_array = [title]
                # print(word_array)
                for index, subtitle in enumerate(word_array):
                    if " with " in title:
                        parsed1.extend(subtitle.split(" with "))
                    else:
                        parsed1.append(subtitle)

                for index, subtitle in enumerate(parsed1):
                    if " with " in title:
                        parsed2.extend(subtitle.split(" with "))
                    else:
                        parsed2.append(subtitle)

                for index, subtitle in enumerate(parsed2):
                    if " in " in title:
                        parsed3.extend(subtitle.split(" in "))
                    else:
                        parsed3.append(subtitle)

                for index, subtitle in enumerate(parsed3):
                    if "," in title:
                        csw = subtitle.split(",")
                        for w in csw:
                            final_parsed.append(w.replace(" ", ""))
                    else:
                        final_parsed.append(subtitle)

                for i in final_parsed:
                    if i == "":
                        final_parsed.remove("")

                # file.write(f"{final_parsed}\n")
                mineral_array.extend(final_parsed)
                word_array.clear()
                parsed1.clear()
                parsed2.clear()
                final_parsed.clear()
            else:
                pass
                mineral_array.extend([title])
                # file.write(f"['{title}']\n")

    bins, counts = np.unique(mineral_array, return_counts=True)

    print_mineral_counts(bins, counts)
    print_mineral_histogram(bins, counts, sheet_name)

def print_starting_prompt():
    print("Hello, what would you like to do? Enter the corresponding number")
    print("1) Generate tags and histogram")
    print("2) Upload images")
    print("3) Exit")


if __name__ == '__main__':
    data_folder = "data"
    dataset_file_path = "data/MineralData.xlsx"
    sheet = "Cabinet 20"
    images_path = "uploadPhotos"

    print()
    print()
    print("^ The above beep boop is intended, please ignore ^")
    print()
    print()
    print_starting_prompt()

    input1 = input()
    while (input1 != "3"):
        if input1 == "1":
            print("Enter the name of the excel file in the data folder(e.g 'MineralData.xlsx'):")
            dataset_file_path = f"{data_folder}/{input()}"
            print("Enter the name of the sheet you want to work with (e.g 'Cabinet 20'):")
            sheet = input()

            df = load_excel_sheet(dataset_file_path, sheet)
            get_mineral_histogram(df, True, True, sheet)
            fill_up_dataset_tags_and_description(df, dataset_file_path, sheet)

            print(f"{bcolors.OKBLUE}Complete! A new excel file and histogram image has been generated in the {data_folder} folder{bcolors.ENDC}")
        elif input1 == "2":
            print("Enter the name of the excel file in the data folder(e.g MineralData.xlsx)")
            print("Make sure it is the file that has the autogenerated tags in it! :")
            dataset_file_path = f"{data_folder}/{input()}"
            print("Enter the name of the sheet you want to work with (e.g 'Cabinet 20')")
            sheet = input()

            df = load_excel_sheet(dataset_file_path, sheet)
            images, ids = load_images_and_ids(images_path)
            parse_photo_info_and_upload(images, ids, df, sheet)

            print("Complete!")

        else:
            print(f"{bcolors.FAIL}Invalid option, try again?{bcolors.ENDC}")
        
        print()
        print()
        print_starting_prompt()
        input1 = input()

    print(f"{bcolors.OKBLUE}Goodbye!{bcolors.ENDC}")
    # print_prior_data_histogram('data/CompData.xlsx', 'Cabinet 13', "data/titles8.txt")

