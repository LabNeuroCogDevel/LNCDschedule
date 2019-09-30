# Python 3
import requests
import zipfile
import json
import io, os
import sys
import re
import configparser
def exportSurvey(apiToken,surveyId, dataCenter, fileFormat):

    surveyId = surveyId
    fileFormat = fileFormat
    dataCenter = dataCenter 

    # Setting static parameters
    requestCheckProgress = 0.0
    progressStatus = "inProgress"
    baseUrl = "{0}.qualtrics.com/API/v3/surveys/{1}".format(dataCenter, surveyId)
    headers = {
    "Content-Type": "application/json",
    "X-API-TOKEN": apiToken,
    "Accept": "*/*",
    "accept-encoding": "gzip, deflate"
    }

    # Step 1: Creating Data Export
    downloadRequestUrl = baseUrl
    downloadRequestPayload = '{"format":"' + fileFormat + '"}'
    downloadRequestResponse = requests.request("GET", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
    progressId = downloadRequestResponse.json()["result"]#["progressId"]
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

    fileId = requestCheckResponse.json()["result"]["fileId"]

    # Step 3: Downloading file
    requestDownloadUrl = baseUrl + fileId + '/file'
    requestDownload = requests.request("GET", requestDownloadUrl, headers=headers, stream=True)

    # Step 4: Unzipping the file
    zipfile.ZipFile(io.BytesIO(requestDownload.content)).extractall("MyQualtricsDownload")
    print('Complete')

def connstr_from_config():
    cfg = configparser.ConfigParser()
    cfg.read('config.ini')

    data = dict(cfg.items('Qualtrics'))
    token = data['api_token']
    ID = data['surveyid']
    center = data['datacenter']

    return token, ID, center


def main():
    
       #Read in the data form config
    apiToken, surveyId, dataCenter = connstr_from_config()
    print(apiToken, surveyId, dataCenter)

    # r = re.compile('^SV_.*')
    # m = r.match(surveyId)
    # if not m:
    #    print ("survey Id must match ^SV_.*")
    #    sys.exit(2)

    exportSurvey(apiToken, surveyId, dataCenter, "csv")
if __name__== "__main__":
    main()


