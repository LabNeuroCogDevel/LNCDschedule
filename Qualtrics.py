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
import difflib
import re
import requests
import pandas as pd


def demo():
    surveys = get_all()
    pet_7t = [s for s in surveys if s.study and s.minage >= 0]
    len(pet_7t)
    names = sorted([s.survey_name for s in pet_7t])
    print(names)


def match_db(study, age, sex, timepoint, subjid):
    surveys = get_all()
    matches = [s for s in surveys
               if s.study == study
               and s.minage <= age
               and s.maxage >= age
               and (s.timpepoint == 0 or s.timepoint == timepoint)
               ]
    if len(matches) == 0:
        raise Exception("No results!")
    print(matches)


def get_all():
    q_api = Qualtrics()
    surveys = [LNCDSurvey(q_api, info) for info in q_api.all_surveys_info()]
    return surveys


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

def set_chosen_data(self, name = None):

    if name != None:
    	#Name should be a dictionary when parsed in
        li = ['type', 'sex', 'study', 'age', 'timepoint']
        #Assume that name is already a dictionary
        #Check if all keys needed is there
        if all(c in name for c in li):
            s_id = word_matching(name['study'], name['sex'], name['age'], name['timepoint'], name['type'] )
            #Able to get the dataframe from the Qualtrics
            f_survey = q_api.get_survey(s_id)
            return f_survey

        else:
            print('data not intact')
            exit()

    else:
        print('data not within Battery or Screening')
        return

    #Study either PET or BrainMechR01
    #Sex wither Male or Female
def word_matching(study, sex, age, timepoint, typ):
    ##############################
    #For now must get all the survey first
    if surveys is None: #Or could just read it all over again in later implementation
        print("No survey")
        return
    
    #List that stores all the names
    name_list = []
    search_key = study
    dictionary_study = {'BrainMechR01':'7T', 'PET/FMRI': 'PET/FMRI'}
    dictionary_age_Battery= {
    '(18, 33)': range(18, 33),
    '(14, 17)': range(14, 17),
    '(11, 13)': range(11, 13)

    }
    #Transform the study
    study = [val for key, val in dictionary_study.items() if search_key in key] 
    #Transform the sex
    #sex could be used directly?
    #Transform the age
    search_age = age
    age = [key for key, val in dictionary_age_Battery .items() if search_age in val]

    #Create a fuzzy string first
    if 'Battery' in typ:
        fuzzy = study +' '+ sex +' '+ age +' '+ typ
    else:
        fuzzy = study +' '+ typ +' '+ sex +' '+ age
    
    #Get all the name from the survey
    for survey in surveys:
        name_list.append(survey['name'])

    result_name = difflib.get_close_matches(fuzzy, name_list, 1)[0]

    #Evaluate the score of the sentence found
    score = difflib.SequenceMatcher(None, fuzzy, result_name).ratio()
    
    #Then use the name to find the ID
    survey_id = [survey['id'] for survey in surveys if survey.get('name') == result_name]
    #Use the id to get the data from Qualtrics
    return survey_id


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
    """Survey class
     class with data, modified time, column breakdown(Tasks in battery)
    """
    def __init__(self, api=None, info=None, survey_id=None):
        """ initilize with either a surevey_id or info"""

        # place holder, filled by 'data' function
        self._data = None

        # if we don't have a qaultrics api reference, try to get one using
        # default settings
        if not api:
            api = Qualtrics()
        self.q_api = api

        if not info and not survey_id:
            raise Exception("Survey needs either id or info dictionary." +
                            "see Qualtrics.all_surveys_info()")

        # set id from info, or get info from id
        if info is not None:
            survey_id = info.get('id')
        else:
            # not optimal. get info by fetching and searching all surveys
            all_surv = self.q_api.all_surveys_info()
            this = [s for s in all_surv if s.get('id') == survey_id]
            if not this:
                raise Exception("could not find %s in all surveys" % survey_id)
            info = this[0]

        self.sid = survey_id
        self.info = info
        self.survey_name = info.get('name')

    def data(self):
        """ fetch (from web or cache) survey data"""
        if not self._data:
            self._data = self.q_api.get_survey(self.sid)
        return self._data

    def get_row(self, participant, idcol=""):
        """get a participants data by finding"""
        sdf = self.data()
        row = sdf[idcol] == participant
        if not row:
            return {}
        else:
            return sdf.iloc[row].to_dict()


class LNCDSurvey(Survey):
    """extends Survey with LNCD particulars"""
    def __init__(self, *args, **kargs):
        """
        extend survey to get age range, study type, and sex when aviable
        for checking/searching
        >>> q=Qualtrics.Qualtrics()
        >>> s=Qualtrics.LNCDSurvey(q, survey_id='SV_bdejyV7MRgmOhuZ')
        >>> assert s.survey_name == '7T Y2 Screening: Adults'
        >>> assert s.study == 'BrainMechR01' and s.minage == 18
        """
        # pass all args to the actual Survey class
        super().__init__(*args, **kargs)
        # # survey info extracted from name
        # set defaults
        self.type = None
        self.study = None
        self.sex = None
        self.minage = -999
        self.maxage = 999
        self.timepoint = 0

        # and classify base on name

        stype = re.search('Battery|Screening', self.survey_name)
        if stype:
            stype = stype.group()

        # find study. None if not PET or 7T.
        # rewrite 7T as BrainMechR01 for db lookup
        study = re.search('7T|PET', self.survey_name)
        if study:
            self.study = study.group().replace('7T', 'BrainMechR01')

        # Male or Female only survey?
        sex = re.search('Male|Female', self.survey_name)
        if sex:
            self.sex = sex.group()

        timepoint = re.search('Y(\d)', self.survey_name)
        if timepoint:
            self.timepoint = timepoint.group()

        # find age range like 18-33, extract min and max
        # use 'named groups' in regular expression
        ages = re.search('\((?P<min>\d+) *- *(?P<max>\d+)\)', self.survey_name)
        if ages:
            self.minage = int(ages.group('min'))
            self.maxage = int(ages.group('max'))
        else:
            # age range could be stored in group name
            # only check this if no specfic range given
            lookup = {'Adult': (18, 99), 'Hybrid': (18, 99),
                      'Teen':  (13, 17),  'Child': (0, 12)}
            agegrp = re.search('Adult|Teen|Adol|Child', self.survey_name)
            if agegrp:
                grp = agegrp.group().replace('Adol', 'Teen')
                self.minage = lookup.get(grp)[0]
                self.maxage = lookup.get(grp)[1]


    ################################################################
    #User Friendly functions to read each detailed data form the big datastructure
    #Parameters should be 'Battery'or'Screening', and Better with an ID
    def get_all_identity(self, type=None, ID=None):
        #Get people with ID
        print('Still; Implementing')
        

    def get_all_questions(self):
        #Get all the test question and may be catagorize them
        print('Still Implementing')

    ################################################################
    ################################################################
    #Function to read in all the data and creat a big data structure
    #Get data form the survey dowmloaded

    #Structure looks like(generic_set{Battery{{id:dataframe}, .....}, Screening{{id:dataframe},.....})
    #Function to push each s_df (dataframe to the lowest branch)
    def appending_data(self, dictionary):
        #Data set will just be dictionary + dataframe, because there are multiple, so just use a dictionary
        dictionary[self.survey_id] = self.s_df
        return dictionary
    ###################################################################


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

    def all_surveys_info(self):
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
    df = pd.read_csv(infile) # skiprows=[0, 1], low_memory=False)

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
        new_survey = [x for x in survey if ('Battery' in x['name'] or 'Screening' in x['name'])]    

    return new_survey
#The function that links to the outer world

#def download_s(name):
    


def download_all():
    """ get all surveys and download them (Orig)
    resave with first two rows removed (Export)
    N.B. REMOVES directories: 'Qaultrics/Orig' and 'Qualtrics/Export'
         before re-creating
    """
    q_api = Qualtrics()
    q_survey = Survey()

    #This function get all the surveys
    surveys = q_api.all_surveys_info()
    #Filtering out the survey without screening or barrtey
    surveys = filtering(surveys)
    print(len(surveys))
    # remove old folders if they exist, create again
    create_fresh_dir('Qualtrics/Orig')
    create_fresh_dir('Qualtrics/Export')
    for survey in surveys:
        #Get the whole survey from id
        s_df = q_api.get_survey(survey['id'])
        #Set that contains everything
        set_all = q_survey.set_all_data(survey)

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
