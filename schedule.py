#!/usr/bin/env python3

import sys
import LNCDcal
import lncdSql
import AddNotes, AddContact, ScheduleVisit, AddPerson, CheckinVisit
from PyQt5 import uic, QtCore, QtGui, QtWidgets
import datetime
import subprocess, re  # for whoami
from LNCDutils import  *

# google reports UTC, we are EST or EDT. get the diff between google and us
launchtime=int(datetime.datetime.now().strftime('%s'))
tzfromutc = datetime.datetime.fromtimestamp(launchtime) - datetime.datetime.utcfromtimestamp(launchtime)


class ScheduleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # schedule and checkin data
        self.schedule_what_data = {'fullname': '', 'pid': None, 'date': None, 'time': None}
        self.checkin_what_data =  {'fullname': '', 'vid': None, 'datetime': None, 'pid': None,'vtype':None}
        

        # load gui (created with qtcreator)
        uic.loadUi('./ui/mainwindow.ui',self)
        self.setWindowTitle('LNCD Scheduler')

        # data store
        self.disp_model = {'pid': None, 'fullname': None, 'ndate': None, 'age': None,'sex': None}

        # get other modules for querying db and calendar
        try:
          self.cal = LNCDcal.LNCDcal('config.ini')
          self.sql = lncdSql.lncdSql('config.ini')
        except Exception as e:
          mkmsg("ERROR: app will not work!\n%s"%str(e))
          return

        ## who is using the app?
        self.RA = subprocess.check_output("whoami").decode().replace('\n','').replace('\r','')
        print("RA: %s"%self.RA)
        #if re.search('lncd|localadmin',self.RA,ignore.case=True):
        #    print("login: TODO: launch modal window")

        ## setup person search field
        # by name
        self.fullname.textChanged.connect(self.search_people_by_name)
        self.fullname.setText('%')
        self.search_people_by_name(self.fullname.text()) # doesnt already happens, why?

        # by lunaid
        self.subjid_search.textChanged.connect(self.search_people_by_id)
        # by attribute
        self.min_age_search.textChanged.connect(self.search_people_by_att)
        self.max_age_search.textChanged.connect(self.search_people_by_att)
        self.sex_search.activated.connect(self.search_people_by_att)
        self.study_search.activated.connect(self.search_people_by_att)

        ## people_talbe: setup search table "people_table"
        pep_columns=['fullname','lunaid','age','dob','sex','lastvisit','maxdrop','studies']
        self.people_table.setColumnCount(len(pep_columns))
        self.people_table.setHorizontalHeaderLabels(pep_columns)
        self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # wire up clicks
        self.people_table.itemClicked.connect(self.people_item_select)
        #people_table_menu = QtWidgets.QMenu(self)
        #self.people_table.contextMenuEvent(people_table_menu)

        ## cal_table: setup search calendar "cal_table"
        cal_columns=['date','time','what']
        self.cal_table.setColumnCount(len(cal_columns))
        self.cal_table.setHorizontalHeaderLabels(cal_columns)
        self.cal_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cal_table.itemClicked.connect(self.cal_item_select)
        # and hook up the calendar date select widget to a query
        self.calendarWidget.selectionChanged.connect(self.search_cal_by_date)
        self.search_cal_by_date() # update for current day
        # TODO: eventually want to use DB instead of calendar. need to update backend!

        ## note table
        note_columns=['note','dropcode','ndate','vtimestamp','ra','vid']
        self.note_table.setColumnCount(len(note_columns))
        self.note_table.setHorizontalHeaderLabels(note_columns)

        ## visit table
        self.visit_columns=['day', 'study', 'vstatus','vtype', 'vscore', 'age', 'note', 'dvisit','dperson','vid']
        self.visit_table.setColumnCount(len(self.visit_columns))
        self.visit_table.setHorizontalHeaderLabels(self.visit_columns)
        self.visit_table.itemClicked.connect(self.visit_item_select)

        # contact table
        contact_columns=['who','cvalue', 'relation', 'nogood', 'added', 'cid']
        self.contact_table.setColumnCount(len(contact_columns))
        self.contact_table.setHorizontalHeaderLabels(contact_columns)

        # schedule time widget
        self.timeEdit.timeChanged.connect(self.update_checkin_time)

        ## general db info
        # study list used for checkin and search
        self.study_list = [ r[0] for r in self.sql.query.list_studies() ]
        # populate search with results
        self.study_search.addItems(self.study_list)

        ## add person
        self.AddPerson = AddPerson.AddPersonWindow(self)
        self.add_person_button.clicked.connect(self.add_person_pushed)
        self.AddPerson.accepted.connect(self.add_person_to_db)

        ## add contact
        self.AddContact = AddContact.AddContactWindow(self)
        # autocomple stuffs
        self.AddContact.add_ctypes( [ r[0] for r in self.sql.query.list_ctype() ] )
        self.AddContact.suggest_relation([ r[0] for r in self.sql.query.list_relation() ] )
        # connect it up
        self.add_contact_button.clicked.connect(self.add_contact_pushed)
        self.AddContact.accepted.connect(self.add_contact_to_db)

        ## add notes and query for pid from visit_summary
        self.AddNotes = AddNotes.AddNoteWindow(self)
        self.add_notes_button.clicked.connect(self.construct_drop_down_box)
        self.add_notes_button.clicked.connect(self.query_for_pid)
        #Do the autocomplete later
        self.add_notes_button.clicked.connect(self.add_notes_pushed)
        self.AddNotes.accepted.connect(self.add_notes_to_db)
        self.AddNotes.accepted.connect(self.add_nid_vid_to_db)
        #connect it up

        ### Visit
        ## schedule
        # init
        self.ScheduleVisit = ScheduleVisit.ScheduleVisitWindow(self)
        self.ScheduleVisit.add_studies(self.study_list)
        self.ScheduleVisit.add_vtypes([ r[0] for r in self.sql.query.list_vtypes() ])
        # wire
        self.schedule_button.clicked.connect(self.schedule_button_pushed)
        self.ScheduleVisit.accepted.connect(self.schedule_to_db)

        ## checkin
        # init
        self.CheckinVisit = CheckinVisit.CheckinVisitWindow(self)
        all_tasks = self.sql.query.all_tasks() 
        self.CheckinVisit.set_all_tasks(all_tasks)
        # wire
        self.checkin_button.clicked.connect(self.checkin_button_pushed)
        self.CheckinVisit.accepted.connect(self.checkin_to_db)

        self.show()

    ###### Generic

    # check with isvalid method
    # used for ScheduleVisit and AddContact
    def useisvalid(self,obj,msgdesc):
        check=obj.isvalid()
        if(not check['valid']):
            mkmsg('%s: %s'%(msgdesc,check['msg']) )
            return(False)
        return(True)
        
        
    ###### PEOPLE
    def add_person_pushed(self):
        name = self.fullname.text().title().split(' ')
        print('spliting name at len %d'%len(name))
        fname=name[0] if len(name)>=1 else ''
        lname=" ".join(name[1:]) if len(name)>=2 else ''
        d = {'fname': fname, 'lname': lname}
        self.AddPerson.setpersondata(d)
        self.AddPerson.show()


    """
    connector for on text change of fullname textline search bar
    """
    def search_people_by_name(self,fullname):
        #print(fullname)
        # only update if we've entered 3 or more characters
        # .. but let wildcard (%) go through
        if(len(fullname) < 3 and fullname != '%' ): return
        res = self.sql.query.name_search(fullname=fullname)
        self.fill_search_table(res)

    # seach by id
    def search_people_by_id(self,lunaid):
        if(len(lunaid) != 5 ): return
        try:
          lunaid=int(lunaid)
        except:
            mkmsg("LunaID should only be numbers")
            return
        res = self.sql.query.lunaid_search(lunaid=lunaid)
        self.fill_search_table(res)

    # by attributes
    def search_people_by_att(self,*argv):
        d={ 'study': comboval(self.study_search), \
                     'sex': comboval(self.sex_search), \
                     'minage': self.min_age_search.text(), \
                     'maxage': self.max_age_search.text() }
        print(d)
        res = self.sql.query.att_search(**d)
        #res = self.sql.query.att_search(sex=d['sex'],study=d['study'], minage=d['minage'],maxage=d['maxage'])
        self.fill_search_table(res)
    """
    fill the person search table
    expected columns are from pep_columns (8)
    res is a list of vectors(8) from sql query
    """ 
    def fill_search_table(self,res):
        count = 0
        self.people_table_data = res
        self.people_table.setRowCount(len(res))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                self.people_table.setItem(row_i,col_i,item)

        #Change the color after the textes have been successfully inserted.
        for row_i,row in enumerate(res):
            if (row[6] == "subject"):
                for j in range(self.people_table.columnCount()):
                    self.people_table.item(count, j).setBackground(QtGui.QColor(240, 128, 128))
                     #Subject titled red

            if(row[6] == "visit"):
                for j in range(self.people_table.columnCount()):
                    self.people_table.item(count, j).setBackground(QtGui.QColor(240, 230, 140)) 
                    #visit titled yellow

            count = count + 1

    def people_item_select(self,thing):
        row_i =self.people_table.currentRow()
        d = self.people_table_data[row_i]
        pid=d[8]
        fullname=d[0]
        # main model
        self.disp_model['pid'] = pid
        self.disp_model['fullname'] = fullname
        self.disp_model['age'] = d[2]
        self.disp_model['sex'] = d[4]

        # update visit table
        self.update_visit_table()
        # update contact table
        self.update_contact_table()
        # update notes
        self.update_note_table()
        # update schedule text
        self.schedule_what_data['pid']=pid
        self.schedule_what_data['fullname']=fullname
        self.update_schedule_what_label()

    def visit_item_select(self,thing):
        row_i = self.visit_table.currentRow()
        d     = self.visit_table_data[row_i]
        vid   = d[self.visit_columns.index('vid')]
        study = d[self.visit_columns.index('study')]
        pid     = self.disp_model['pid']
        fullname= self.disp_model['fullname']

        self.checkin_what_data['vid'] = vid
        self.checkin_what_data['study'] = study
        self.checkin_what_data['pid'] = pid
        self.checkin_what_data['fullname'] = fullname
        self.checkin_what_data['vtype'] = d[self.visit_columns.index('vtype')]
        self.checkin_what_data['datetime'] = d[self.visit_columns.index('day')]
        self.update_checkin_what_label()



    def update_visit_table(self):
        pid=self.disp_model['pid']
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        generic_fill_table(self.visit_table,self.visit_table_data)

    def update_contact_table(self):
        self.contact_table_data=self.sql.query.contact_by_pid(pid=self.disp_model['pid'])
        generic_fill_table(self.contact_table,self.contact_table_data)

    def update_note_table(self):
        #pid=self.disp_model['pid']
        self.note_table_data = self.sql.query.note_by_pid(pid=self.disp_model['pid'])
        generic_fill_table(self.note_table,self.note_table_data)

    """
    person to db
    """
    def add_person_to_db(self):
        print(self.AddPerson.persondata)
        # pop up window and return if not valid
        if(not self.AddPerson.isvalid() ):
           mkmsg("Missing data must be provided before we can continue adding the person")
           return 

        self.fullname.setText( '%(fname)s %(lname)s'%self.AddPerson.persondata)
        # put error into dialog box
        try:
          #self.sql.query.insert_person(**(self.AddPerson.persondata))
          data=self.AddPerson.persondata
          data['adddate'] = datetime.datetime.now()
          self.sql.insert('person',data)
        except Exception as e:
          mkmsg(str(e))
          return

        self.search_people_by_name(self.fullname.text())

    ###### VISIT
    # see generic_fill_table
    def schedule_button_pushed(self):
        d=self.schedule_what_data['date'] 
        t=self.schedule_what_data['time']
        pid=self.disp_model['pid']
        fullname=self.disp_model['fullname']
        if d==None or t==None:
            mkmsg('set a date and time before scheduling')
            return()
        if pid == None or fullname == None:
            mkmsg('select a person before trying to schedule')
            return()
        dt=datetime.datetime.combine(d, t)
        self.ScheduleVisit.setup(pid,fullname,self.RA,dt)
        self.ScheduleVisit.show()

    def schedule_to_db(self):
        # valid?
        if not self.useisvalid(self.ScheduleVisit, "Cannot schedule visit"): return
        #todo: add to calendar or msgerr
        try :
          self.ScheduleVisit.add_to_calendar(self.cal,self.disp_model)
        except Exception as e:
          mkmsg('Failed to add to google calendar; not adding. %s'%str(e))
          return()
        # catch sql error
        # N.B. action(vstatus) intentionally empty -- will be set to 'sched'
        if not self.sqlInsertOrShowErr('visit_summary',self.ScheduleVisit.model):
            # todo: remove from calendar if sql failed
            return()
        
        # need to refresh visits
        self.update_visit_table()
        self.update_note_table()

    ## checkin
    def checkin_button_pushed(self):
        pid=self.checkin_what_data['pid']
        vid=self.checkin_what_data['vid']
        fullname=self.checkin_what_data['fullname']
        study = self.checkin_what_data['study']
        vtype = self.checkin_what_data['vtype']
        if study==None or vtype==None:
            mkmsg('pick a visit with a study and visit type')
            return()
        if pid == None or fullname == None:
            mkmsg('select a person before trying to checkin (howd you get here?)')
            return()

        # que up a new lunaid
        # N.B. we never undo this, but check is always for lunaid first
        if self.checkin_what_data.get('lunaid') == None:
           self.checkin_what_data['nextluna'] = (self.sql.query.next_luna())[0][0] + 1

        #(self,pid,name,RA,study,study_tasks)
        study_tasks = [ x[0] for x in self.sql.query.list_tasks_of_study_vtype(study=study,vtype=vtype) ]
        print("launching %(fullname)s for %(study)s/%(vtype)s"%self.checkin_what_data)
        # checkin_what_data sends: pid,vid,fullname,study,vtype
        self.CheckinVisit.setup(self.checkin_what_data,self.RA,study_tasks)
        self.CheckinVisit.show()

    """
    wrap CheckinVisit's own checkin_to_db to add error msg and refresh visits
    """
    def checkin_to_db(self):
        try:
          self.update_visit_table()
        except Exception as e:
          print(e)
          mkmsg('checkin failed!\n%s'%e)
        self.CheckinVisit.checkin_to_db(self.sql)
        # todo: update person search to get lunaid if updated

    ###### Notes
    # see generic_fill_table

    ###### Labels
    def update_schedule_what_label(self):
        text = "%(fullname)s: %(date)s@%(time)s"%(self.schedule_what_data)
        self.schedule_what_label.setText(text)
    def update_checkin_what_label(self):
        text = "%(fullname)s - %(datetime)s"%(self.checkin_what_data)
        self.checkin_what_label.setText(text)

    def update_checkin_time(self):
        time = self.timeEdit.dateTime().time().toPyTime()
        self.schedule_what_data['time'] = time
        self.update_schedule_what_label()

        
    ###### CALENDAR
    
    def search_cal_by_date(self):
        #selectedQdate=self.calendarWidget.selectedDate().toPyDate()
        #dt=datetime.datetime.fromordinal( selectedQdate.toordinal() )
        dt=caltodate(self.calendarWidget)
        print(dt)
        # update schedule 
        self.schedule_what_data['date']=dt.date()
        self.update_schedule_what_label()
        # update calendar table
        #now=datetime.datetime.now()
        delta =datetime.timedelta(days=5)
        dmin=dt - delta
        dmax=dt + delta
        res = self.cal.find_in_range(dmin, dmax)
        self.fill_calendar_table(res)
    """
    fill the calendar table with goolge calendar items from search result
    calres is list of dict with keys ['summary', 'note', 'calid', 'starttime', 'creator', 'dur_hr', 'start']
    """
    def fill_calendar_table(self, calres):
        self.cal_table_data = calres
        self.cal_table.setRowCount(len(calres))
        for row_i, calevent in enumerate(calres):
            # google uses UTC, but we are in EST or EDT
            #st   = str(calevent['starttime'] + tzfromutc)
            #st=str(calevent['starttime'])
            m_d=calevent['starttime'].strftime('%m-%d')
            tm=calevent['starttime'].strftime('%H:%M')
            self.cal_table.setItem(row_i, 0, QtWidgets.QTableWidgetItem(m_d) )
            self.cal_table.setItem(row_i, 1, QtWidgets.QTableWidgetItem(tm) )
            eventname = calevent['summary']
            self.cal_table.setItem(row_i, 2, QtWidgets.QTableWidgetItem(eventname) )

    """
    when we hit an item in the calendar table, update
     * potential checkin data and label
     * potental schedual data and srings
    """
    def cal_item_select(self):
        pass
        row_i =self.cal_table.currentRow()
        d = self.cal_table_data[row_i]


    ### CONTACTS
    # self.add_contact_button.clicked.connect(self.add_contact_pushed)
    def add_contact_pushed(self):
        # self.AddContact.setpersondata(d)
        self.AddContact.set_contact(self.disp_model['pid'],self.disp_model['fullname'])
        self.AddContact.show()

    def add_notes_pushed(self):
        #self.Addnotes.setpersondata(d)
        self.AddNotes.set_note(self.disp_model['pid'],self.disp_model['fullname'], self.disp_model['ndate'])
        self.AddNotes.show()

    # self.AddContact.accepted.connect(self.add_contact_to_db)
    def add_contact_to_db(self):
        # do we have good input?
        if not self.useisvalid(self.AddContact, "Cannot add contact"):
            return

        # catch sql error
        data = self.AddContact.contact_model
        data['added'] = datetime.datetime.now()
        #The contact is referring to the table in debeaver.
        self.sqlInsertOrShowErr('contact',data)
        self.update_contact_table()

    def add_notes_to_db(self):
        #Error check
         if not self.useisvalid(self.AddNotes, "Cannot add note"): return

         data = self.AddNotes.notes_model
          #Store the chosen value from the drop down box
         drop_down_option = self.AddNotes.visit 
         #Check if something other than None is selected.
         #if drop_down_option != 'None': 
         self.AddNotes.get_vid()
         if(self.AddNotes.ctype_box_2.currentText() == 'NULL'):
            return
         self.AddNotes.add_ndate()
         self.sqlInsertOrShowErr('note', data)
         self.update_note_table()
         self.query_for_nid()

    def add_nid_vid_to_db(self):
        nid_vid_data = self.AddNotes.nid_vid
        self.sqlInsertOrShowErr('visit_note', nid_vid_data)
        self.update_note_table()

    def query_for_pid(self):
        res = self.sql.query.get_vid(pid = self.disp_model['pid'])
        #vid should be an array that stores the same vid value of a person due to multiple visits.
        self.vid = res
        #print(vid[0]);

    def query_for_nid(self):
        data = self.AddNotes.notes_model
        nid = self.sql.query.get_nid(pid = data['pid'], note = data['note'], ndate = data['ndate'])
        self.AddNotes.nid_vid['nid'] = nid[0][0]


    def sqlInsertOrShowErr(self,table,d):
        try:
            # self.sql.query.insert_person(**(self.AddPerson.persondata))
            self.sql.insert(table, d)
            return(True)
        except Exception as e:
            mkmsg(str(e))
            return(False)


    def construct_drop_down_box(self):

        myList = list()
        for j in range(self.visit_table.rowCount()):
            #Append the vid onto the list
            myList.append(self.visit_table.item(j,9).text())
            for i in range(4):
                #Construct the list by using the value in the table
                myList.append(self.visit_table.item(j,i).text())
            #Pass the value to the array(drop_down_value) in the ArrayNotes file
            self.AddNotes.drop_down_value.append(str(myList).strip('[]'))
            myList.clear()

            #Get the vid from the table

# actually launch everything
if __name__ == '__main__':
    # paths relative to where files are
    import os
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    app = QtWidgets.QApplication(sys.argv)
    window = ScheduleApp()
    sys.exit(app.exec_())
