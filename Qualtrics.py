#!/usr/bin/env python3

"""
Functions for qualtrics survey list and downloading
N.B. surveys are downloaded as zipped csv files
     can query a url for qualtrics servers zip building percent
API calls:
   GET  /API/v3/surveys                 - get list of all surveys
   POST /API/v3/responseexports/        - start qualtircs bulding zip
   GET  /API/v3/responseexports/id      - get status of zip building
   GET  /API/v3/responseexports/id/file - get zipped csv file

TODO:
 * Class Survey to include last modified, column data, and 'export' dataframe?
 * single responses!  https://api.qualtrics.com/reference#getresponse-1
   GET API/v3/surveys/surveyId/responses/responseId
     maybe no way to get list of new responseIds?
"""

import warnings
import zipfile
import io
import os
import configparser
import shutil
import requests
import pandas as pd
from anytree import Node, RenderTree



def get_json_result(req):
    """get 'result' from request response
    return {} if error or missing"""
    jsn = req.json()
    if jsn is None:
        warnings.warn('no json in request!')
        return {}
    return jsn.get('result', {})


def connstr_from_config(inifile='config.ini'):
    """read from config like:
    [Qualtrics]
     api_token=
     datacenter=https://yourorganizationid.yourdatacenterid (no .qualtrics.com)
    """
    cfg = configparser.ConfigParser()
    cfg.read(inifile)

    data = dict(cfg.items('Qualtrics'))
    token = data['api_token']
    center = data['datacenter']
    return token, center


class DlStatus:
    """parse qualtircs download status results
    provide __bool__ to report "finished" (useful for while not loop)"""
    __slots__ = ['done', 'status', 'percent', 'file']

    def __init__(self, req):
        # check we still have values
        print(req.json())
        res = get_json_result(req)
        self.status = res.get('status', 'NoSurvey')
        self.percent = res.get('percentComplete', 0)
        self.file = res.get('file', None)
        if self.status in ['NoSurvey', 'failed', 'complete']:
            self.done = True
        else:
            self.done = False

    def __bool__(self):
        return self.done

    def is_success(self):
        """finished and complete, ready to download csv file"""
        return self and self.status == 'complete'

class Survey:
#Survey class
#class with data, modified time, column breakdown(Tasks in battery)
    def __init__(self, modified_time = None, survey_id = None):
        #list that contains stuffs
        self.collection = []
        self.responseID = []
        self.name = []
        self.email = []


        #Dict that contains individual stuffs

        self.modified_time = modified_time
        self.survey_id = survey_id

        self.q_api = Qualtrics()

    
    #Get data form the survey dowmloaded
    def set_data(self, survey):
        #First extract modified time and ID from the surveys
        self.modified_time = survey['lastModified']
        self.survey_id = survey['id']

    def fetch_data(self):
        #Fetch_data based on the id chose
        s_df = self.q_api.get_survey(survey['id'])
        #Get all personal data and put them into a dictionary
        self.ResponseID = s_df['ResponseID']
        self.name = s_df['RecipientLastName']+' '+s_df['RecipientFirstName']      
        self.email = s_df['RecipientEmail']   

        survey_id = Node("survey_id") 
        for n in name:
            n = Node(n, parent = survey_id)









class Qualtrics:
    """
    fetch Qualtrics survey list and data
    see `connstr_from_config` for api config setup (`config.ini`)
    """
    def __init__(self, cfgini="config.ini"):
        token, center = connstr_from_config(cfgini)
        self.apiurl = "{0}.qualtrics.com/API/v3/".format(center)
        self.header = {
            "Content-Type": "application/json",
            "X-API-TOKEN": token,
            "Accept": "*/*",
            "accept-encoding": "gzip, deflate"
        }

    def apiget(self, url_part, **kargs):
        """GET request on with stored qualtircs api settings"""
        url = self.apiurl + url_part
        print(url)
        res = requests.request("GET", url, headers=self.header, **kargs)
        return res

    def apipost(self, url_part, data):
        """POST request on with stored qualtircs api settings"""
        url = self.apiurl + url_part
        res = requests.request("POST", url, headers=self.header, data=data)
        return res

    def extract_survey(self, fileid):
        """download and extract a zipped csv file
        returns pandas dataframe"""
        file_url = "responseexports/" + fileid + "/file"
        # N.B. file url is also returned by "responseexports/" + fileid

        res = self.apiget(file_url)
        # read zip
        unzip = zipfile.ZipFile(io.BytesIO(res.content))
        files = unzip.infolist()
        if len(files) != 1:
            warnings.warn('qualtircs zip: not one file: %s' % files)
            return pd.DataFrame()
        content = unzip.open(files[0])
        df = pd.read_csv(content, encoding='utf-8')
        # TODO: clean up columns a la format_colnames
        # consider making survey class to store info in discared rows
        return df

    def all_surveys(self):
        """return json list of all surveys"""
        req = self.apiget('surveys')
        res = get_json_result(req)
        return res.get('elements', None)
        # TOOD: next page
        # https://github.com/ropensci/qualtRics/blob/master/R/all_surveys.R#L63

    def get_survey(self, sid):
        """retrieve single survey
        qualtircs give zipped csv. extract as temp file"""
        data = '{"format":"csv", "surveyId":"%s"}' % sid

        # tell qualtrics to start making the zip file of the survey
        req = self.apipost('responseexports/', data)
        info = get_json_result(req)
        print("first pass: %s" % info)

        # look up % comlete until download is finished building on their side
        export_id = info.get('id')
        checkurl = 'responseexports/' + export_id
        dlstatus = False
        while not dlstatus:
            dlstatus = DlStatus(self.apiget(checkurl))

        if not dlstatus.is_success():
            warnings.warn('download status reports failure')
            return pd.DataFrame()

        return self.extract_survey(export_id)


# Create a folder
def create_fresh_dir(target_date):
    """ removes current directory and recreates
    """
    direc = "./" + target_date

    if not os.path.exists(direc):
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))
    else:
        shutil.rmtree(direc)
        os.makedirs(direc)
        print('New directory %s has been created' % (target_date))


def format_colnames(infile, outfile):
    '''This function takes the file and rename its columns with the right format,
    and generate csv file with the right column names'''
    # TODO: do this without needing to read from a file

    df = pd.read_csv(infile, skiprows=[0, 1], low_memory=False)

    columns = df.columns
    new_cols = []

    # (2) Reformat the column names
    for name in columns:
        try:
            new_name = name.replace('{', '').replace('}', '').\
                       split(':')[1].\
                       replace('\'', '').\
                       replace('-', '_').replace(' ', '')
            new_cols.append(new_name)
        except IndexError:
            print("Outliers, name = 1")
            new_cols.append(1)
            continue
    # print new_cols
    df.columns = new_cols
    # (3) Create CSV file into the output directory
    df.to_csv(outfile, doublequote=True, sep='|', index=False)
    print('Reformateed and moved %s' % (outfile))

def filtering(survey):
    for s in survey:
        if 'Screening' not in s['name'] or 'Battery' not in s['name']:
            survey.remove(s)

def download_all():
    """ get all surveys and download them (Orig)
    resave with first two rows removed (Export)
    N.B. REMOVES directories: 'Qaultrics/Orig' and 'Qualtrics/Export'
         before re-creating
    """
    import re
    q_api = Qualtrics()

    #This function get all the surveys
    surveys = q_api.all_surveys()
   
    #Filtering out the survey without screening or barrtey
    surveys = filtering(surveys)
    # remove old folders if they exist, create again
    create_fresh_dir('Qualtrics/Orig')
    create_fresh_dir('Qualtrics/Export')
    for survey in surveys:
        #Get the whole survey from id
        s_df = q_api.get_survey(survey['id'])

        print(s_df)
        exit()

        #Pass  the surveys to 
        if not s_df.empty:
            # orig has original data
            # export has junk rows removed
            name = re.sub(r'[/ \t\\]+', '_', survey['name'])
            origfile = "./Qualtrics/Orig/%s.csv" % name
            exportfile = "./Qualtrics/Export/%s.csv" % name
            # save files
            s_df.to_csv(origfile, index = False, header = False)
            format_colnames(origfile, exportfile)


if __name__ == "__main__":
    download_all()
