# Python 3
import requests
import zipfile
import json
import io, os
import sys
import re
import configparser
import pandas as pd
import shutil
import time
def exportSurvey(apiToken,surveyId, dataCenter, fileFormat):

    surveyId = surveyId
    fileFormat = fileFormat
    dataCenter = dataCenter 

    # Setting static parameters
    requestCheckProgress = 0.0
    progressStatus = "inProgress"
    baseUrl = "{0}.qualtrics.com/API/v3/responseexports/".format(dataCenter)
    headers = {
    "Content-Type": "application/json",
    "X-API-TOKEN": apiToken,
    "Accept": "*/*",
    "accept-encoding": "gzip, deflate"
    }


    # Step 1: Creating Data Export
    downloadRequestUrl = baseUrl
    downloadRequestPayload = '{"format":"' + fileFormat + '","surveyId":"' + surveyId + '"}'
    downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
    print(downloadRequestResponse.json())
    progressId = downloadRequestResponse.json()["result"]["id"]
    print(downloadRequestResponse.text)

    # Step 2: Checking on Data Export Progress and waiting until export is ready
    while progressStatus != "complete" and progressStatus != "failed":
        print ("progressStatus=", progressStatus)
        requestCheckUrl = baseUrl + progressId
        requestCheckResponse = requests.request("GET", requestCheckUrl, headers=headers)
        requestCheckProgress = requestCheckResponse.json()["result"]["percentComplete"]
        print("Download is " + str(requestCheckProgress) + " complete")
        progressStatus = requestCheckResponse.json()["result"]["status"]

    #step 2.1: Check for error
    if progressStatus is "failed":
        raise Exception("export failed")

    requestId = downloadRequestResponse.json()["result"]["id"]
    print('++++++++++++++++++++')
    print(downloadRequestResponse.json())
   #Step 3: Downloading file
    requestDownloadUrl = baseUrl + requestId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True) 

    for i in range(0, 200):
        print(str(requestDownload))
        if str(requestDownload) == '<Response [200]>':
            # Step 4: Unziping file
            with open("RequestFile.zip", "wb") as f:
                for chunk in requestDownload.iter_content(chunk_size=1024):
                    f.write(chunk)
                f.close()
            zipfile.ZipFile("RequestFile.zip").extractall('Exported')
            print('Completed Export for {}')#.format(key))
            os.remove("./RequestFile.zip")
            break
        else:
            time.sleep(10)
            requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

    for filename in os.listdir("Exported"):
        print(filename)
        os.rename('./Exported/'+filename, './Exported/'+filename.replace(" ", "_").replace("-", "_").lower())
           
    #Create directory for the Qualtrics download
    create_dir("Qualtrics_test")
    #Format the downloaded file
    format_colnames("Qualtrics_test")

#Read data from the config file
def connstr_from_config():
    cfg = configparser.ConfigParser()
    cfg.read('config.ini')

    data = dict(cfg.items('Qualtrics'))
    token = data['api_token']
    ID = data['surveyid']
    center = data['datacenter']

    return token, ID, center

#Create a folder
def create_dir(target_date):
    direc = "./" + target_date

    if not os.path.exists(direc):
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))
    else:
        shutil.rmtree(direc)
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))

#put file in the right folder
def format_colnames(output_dir):
    '''This function takes the file and rename its columns with the right format,
    and generate csv file with the right column names'''

    for filename in os.listdir("./Exported"):
        # (1) Read csv file
        df = pd.read_csv("./Exported/" + filename, skiprows=[0,1], low_memory=False)

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
        df.to_csv('./' + output_dir + '/' + filename, doublequote=True, sep='|', index=False)
        print('Reformateed and moved %s' % (filename))




def main():
    
    #Read in the data form config
    apiToken, surveyId, dataCenter = connstr_from_config()
    print(apiToken, surveyId, dataCenter)

    exportSurvey(apiToken, surveyId, dataCenter, "csv")
if __name__== "__main__":
    main()


