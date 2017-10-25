#!/usr/bin/env python3

import sys
sys.path.append('../pull_from_sheets')
import gcal_serviceAccount 
import lncdSql
import AddContact, ScheduleVisit, AddPerson
from PyQt5 import uic,QtCore, QtWidgets
import datetime
import subprocess,re # for whoami
from LNCDutils import  *

# google reports UTC, we are EST or EDT. get the diff between google and us
launchtime=int(datetime.datetime.now().strftime('%s'))
tzfromutc = datetime.datetime.fromtimestamp(launchtime) - datetime.datetime.utcfromtimestamp(launchtime)

class ScheduleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # schedule and checkin data
        self.schedule_what_data = {'fullname': '', 'pid': None, 'date': None, 'time': None}
        self.checkin_what_data =  {'fullname': '', 'vid': None, 'datetime': None}
        

        # load gui (created with qtcreator)
        uic.loadUi('./ui/mainwindow.ui',self)
        self.setWindowTitle('LNCD Scheduler')

        # data store
        self.disp_model = {'pid': None, 'fullname': None}

        # message box for warnings/errors
        self.msg=QtWidgets.QMessageBox()

        # get other modules for querying db and calendar
        try:
          self.cal = gcal_serviceAccount.LNCDcal()
          self.sql = lncdSql.lncdSql() # need ~/.pgpass
        except Exception as e:
          self.mkmsg("ERROR: app will not work!\n%s"%str(e))
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
        visit_columns=['day', 'study', 'vtype', 'vscore', 'age', 'note', 'dvisit','dperson','vid']
        self.visit_table.setColumnCount(len(visit_columns))
        self.visit_table.setHorizontalHeaderLabels(visit_columns)

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

        ### Visit
        ## schedule
        self.ScheduleVisit = ScheduleVisit.ScheduleVisitWindow(self)
        self.ScheduleVisit.add_studies(self.study_list)
        self.ScheduleVisit.add_vtypes([ r[0] for r in self.sql.query.list_vtypes() ])
        self.schedule_button.clicked.connect(self.schedule_button_pushed)
        self.ScheduleVisit.accepted.connect(self.schedule_to_db)


        self.show()

    ###### Generic
    # message to warn about issues
    def mkmsg(self,msg,icon=QtWidgets.QMessageBox.Critical):
           self.msg.setIcon(icon)
           self.msg.setText(msg)
           self.msg.show()
    # used for visit, contact, and notes
    def generic_fill_table(self,table,res):
        table.setRowCount(len(res))
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                table.setItem(row_i,col_i,item)

    # check with isvalid method
    # used for ScheduleVisit and AddContact
    def useisvalid(self,obj,msgdesc):
        check=obj.isvalid()
        if(not check['valid']):
            self.mkmsg('%s: %s'%(msgdesc,check['msg']) )
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
            self.mkmsg("LunaID should only be numbers")
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
        self.people_table_data = res
        self.people_table.setRowCount(len(res))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                self.people_table.setItem(row_i,col_i,item)


    def people_item_select(self,thing):
        row_i =self.people_table.currentRow()
        d = self.people_table_data[row_i]
        pid=d[8]
        fullname=d[0]
        # main model
        self.disp_model['pid'] = pid
        self.disp_model['fullname'] = fullname

        # update visit table
        self.update_visit_table()
        # update contact table
        self.update_contact_table()
        # update schedule text
        self.schedule_what_data['pid']=pid
        self.schedule_what_data['fullname']=fullname
        self.update_schedule_what_label()
        # update notes
        self.note_table_data = self.sql.query.note_by_pid(pid=pid)
        self.generic_fill_table(self.note_table,self.note_table_data)

    def update_visit_table(self):
        pid=self.disp_model['pid']
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        self.generic_fill_table(self.visit_table,self.visit_table_data)

    def update_contact_table(self):
        self.contact_table_data=self.sql.query.contact_by_pid(pid=self.disp_model['pid'])
        self.generic_fill_table(self.contact_table,self.contact_table_data)

    """
    person to db
    """
    def add_person_to_db(self):
        print(self.AddPerson.persondata)
        # pop up window and return if not valid
        if(not self.AddPerson.isvalid() ):
           self.mkmsg("Missing data must be provided before we can continue adding the person")
           return 

        self.fullname.setText( '%(fname)s %(lname)s'%self.AddPerson.persondata)
        # put error into dialog box
        try:
          #self.sql.query.insert_person(**(self.AddPerson.persondata))
          self.sql.insert('person',self.AddPerson.persondata)
        except Exception as e:
          self.mkmsg(str(e))
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
            self.mkmsg('set a date and time before scheduling')
            return()
        if pid == None or fullname == None:
            self.mkmsg('select a person before trying to schedule')
            return()
        dt=datetime.datetime.combine(d, t)
        self.ScheduleVisit.setup(pid,fullname,self.RA,dt)
        self.ScheduleVisit.show()

    def schedule_to_db(self):
        # valid?
        if not self.useisvalid(self.ScheduleVisit, "Cannot schedule visit"): return
        #todo: add to calendar or msgerr
        # catch sql error
        if not self.sqlInsertOrShowErr('visit_summary',self.ScheduleVisit.model):
            # todo: remove from calendar if sql failed
            return()
        
        # need to refresh visits
        self.update_visit_table()

    ###### Notes
    # see generic_fill_table

    ###### Labels
    def update_schedule_what_label(self):
        text = "%(fullname)s: %(date)s@%(time)s"%(self.schedule_what_data)
        self.schedule_what_label.setText(text)
    def update_checkin_what_label(self):
        text = "%(fullname)s - %(datetime)s"%(self.checkin_what_data)
        self.schedule_checkin_label.setText(text)

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
        res = self.cal.find_in_range(dmin,dmax)
        self.fill_calendar_table(res)
    """
    fill the calendar table with goolge calendar items from search result
    calres is list of dict with keys ['summary', 'note', 'calid', 'starttime', 'creator', 'dur_hr', 'start']
    """
    def fill_calendar_table(self,calres):
        self.cal_table_data = calres
        self.cal_table.setRowCount(len(calres))
        for row_i,calevent in enumerate(calres):
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
        #self.AddContact.setpersondata(d)
        self.AddContact.set_contact(self.disp_model['pid'],self.disp_model['fullname'])
        self.AddContact.show()

    # self.AddContact.accepted.connect(self.add_contact_to_db)
    def add_contact_to_db(self):
        # do we have good input?
        if not self.useisvalid(self.AddContact, "Cannot add contact"): return

        # catch sql error
        self.sqlInsertOrShowErr('contact',self.AddContact.contact_model)
        self.update_contact_table()

    def sqlInsertOrShowErr(self,table,d):
        try:
          #self.sql.query.insert_person(**(self.AddPerson.persondata))
          self.sql.insert(table,d)
          return(True)
        except Exception as e:
          self.mkmsg(str(e))
          return(False)

# actually launch everything
if __name__ == '__main__':
    app= QtWidgets.QApplication(sys.argv)
    window = ScheduleApp()
    sys.exit(app.exec_())
