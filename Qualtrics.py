# Python 3
import requests
import urllib.request as urllib2
import zipfile
import json
import io
import os
import sys
import re
import configparser
import pandas as pd
import shutil
import time


def exportSurvey(baseUrl, headers, apiToken, surveyId, dataCenter, fileFormat):

    # For Loop to print all the IDS
    for ID in surveyId:
        # Setting static parameters
        requestCheckProgress = 0.0
        progressStatus = "inProgress"
        # Step 1: Creating Data Export
        downloadRequestUrl = baseUrl
        downloadRequestPayload = '{"format":"' + \
            fileFormat + '","surveyId":"' + ID + '"}'
        downloadRequestResponse = requests.request(
            "POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)

        progressId = downloadRequestResponse.json()["result"]["id"]
        print(downloadRequestResponse.text)

        # Step 2: Checking on Data Export Progress and waiting until export is
        # ready
        while progressStatus != "complete" and progressStatus != "failed":
            print("progressStatus=", progressStatus)
            requestCheckUrl = baseUrl + progressId
            requestCheckResponse = requests.request(
                "GET", requestCheckUrl, headers=headers)
            requestCheckProgress = requestCheckResponse.json()[
                "result"]["percentComplete"]
            print("Download is " + str(requestCheckProgress) + " complete")
            progressStatus = requestCheckResponse.json()["result"]["status"]

        # step 2.1: Check for error
        if progressStatus is "failed":
            raise Exception("export failed")

        requestId = downloadRequestResponse.json()["result"]["id"]
       # Step 3: Downloading file
        requestDownloadUrl = baseUrl + requestId + '/file'
        requestDownload = requests.request(
            "GET", requestDownloadUrl, headers=headers, stream=True)

        for i in range(0, 200):
            print(str(requestDownload))
            if str(requestDownload) == '<Response [200]>':
                # Step 4: Unziping file
                with open("RequestFile.zip", "wb") as f:
                    for chunk in requestDownload.iter_content(chunk_size=1024):
                        f.write(chunk)
                    f.close()
                zipfile.ZipFile("RequestFile.zip").extractall('Exported')
                print('Completed Export for {}')  # .format(key))
                os.remove("./RequestFile.zip")
                break
            else:
                time.sleep(10)
                requestDownload = requests.request(
                    "GET", requestDownloadUrl, headers=headers, stream=True)

        for filename in os.listdir("Exported"):
            print(filename)
            os.rename(
                './Exported/' +
                filename,
                './Exported/' +
                filename.replace(
                    " ",
                    "_").replace(
                    "-",
                    "_").lower())

        # Create directory for the Qualtrics download
        create_dir("Qualtrics_test")
        # Format the downloaded file
        format_colnames("Qualtrics_test")

# Getting a list of Ids


def get_surveyId(baseUrl, headers):
    Id_list = {}
    # Create a list that only contains id
    Id = []
    # Create a list that only contains name
    name = []
    # list of creation data incase
    creationDate = []
    # List of last_modified incase
    lastModified = []
    # List of owner id incase
    ownerId = []

    survey_Id = requests.request(
        "GET",
        baseUrl.replace(
            "responseexports",
            "surveys"),
        headers=headers)
    # It's a list of dictionary
    Id_list = survey_Id.json()['result']['elements']

    for i in Id_list:
        Id.append(i.get('id'))
        name.append(i.get('name'))
        creationDate.append(i.get('creationData'))
        lastModified.append(i.get('lastModified'))
        ownerId.append(i.get('ownerId'))

    print(len(Id))
    return Id

# Read data from the config file


def connstr_from_config():
    cfg = configparser.ConfigParser()
    cfg.read('config.ini')

    data = dict(cfg.items('Qualtrics'))
    token = data['api_token']
    #ID = data['surveyid']
    center = data['datacenter']

    return token, center

# Create a folder


def create_dir(target_date):
    direc = "./" + target_date

    if not os.path.exists(direc):
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))
    else:
        shutil.rmtree(direc)
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))

# put file in the right folder


def format_colnames(output_dir):
    '''This function takes the file and rename its columns with the right format,
    and generate csv file with the right column names'''

    for filename in os.listdir("./Exported"):
        # (1) Read csv file
        df = pd.read_csv(
            "./Exported/" +
            filename,
            skiprows=[
                0,
                1],
            low_memory=False)

        columns = df.columns
        new_cols = []

        # (2) Reformat the column names
        for name in columns:
            new_name = name.replace('{', '').replace('}', '').split(':')[1].replace('\'', '').\
                replace('-', '_').replace(' ', '')
            new_cols.append(new_name)
        # print new_cols
        df.columns = new_cols
        # (3) Create CSV file into the output directory
        df.to_csv(
            './' +
            output_dir +
            '/' +
            filename,
            doublequote=True,
            sep='|',
            index=False)
        print('Reformateed and moved %s' % (filename))


def main():
    # Read in the data form config
    apiToken, dataCenter = connstr_from_config()

    # Define the header
    headers = {
        "Content-Type": "application/json",
        "X-API-TOKEN": apiToken,
        "Accept": "*/*",
        "accept-encoding": "gzip, deflate"
    }

    # Define the URL
    baseUrl = "{0}.qualtrics.com/API/v3/responseexports/".format(dataCenter)

    #print(apiToken, surveyId, dataCenter)
    # Survey as a list
    surveyId = get_surveyId(baseUrl, headers)

    try:
        exportSurvey(baseUrl, headers, apiToken, surveyId, dataCenter, "csv")
    except Exception as e:
        print("something went wrong in the Qualtrics")


if __name__ == "__main__":
    main()
