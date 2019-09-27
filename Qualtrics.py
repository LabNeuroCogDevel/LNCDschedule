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
    baseUrl = "https://{0}.qualtrics.com/API/v3/surveys/{1}/export-responses/".format(dataCenter, surveyId)
    headers = {
    "content-type": "application/json",
    "x-api-token": apiToken,
    }

    # Step 1: Creating Data Export
    downloadRequestUrl = baseUrl
    downloadRequestPayload = '{"format":"' + fileFormat + '"}'
    downloadRequestResponse = requests.request("POST", downloadRequestUrl, data=downloadRequestPayload, headers=headers)
    progressId = downloadRequestResponse.json()["result"]["progressId"]
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
    
    # try:
    #   apiToken = os.environ['APIKEY']
    #   dataCenter = os.environ['DATACENTER']
    # except KeyError:
    #   print("set environment variables APIKEY and DATACENTER")
    #   sys.exit(2)

    # try:
    #     surveyId=sys.argv[1]
    #     fileFormat=sys.argv[2]
    # except IndexError:
    #     print ("usage: surveyId fileFormat")
    #     sys.exit(2)

    # if fileFormat not in ["csv", "tsv", "spss"]:
    #     print ('fileFormat must be either csv, tsv, or spss')
    #     sys.exit(2)
 
    #Read in the data form config
    apiToken, surveyID, dataCenter = connstr_from_config()
    print(apiToken, surveyID, dataCenter)

    # r = re.compile('^SV_.*')
    # m = r.match(surveyId)
    # if not m:
    #    print ("survey Id must match ^SV_.*")
    #    sys.exit(2)

    exportSurvey(apiToken, surveyID, dataCenter, "csv")
if __name__== "__main__":
    main()


