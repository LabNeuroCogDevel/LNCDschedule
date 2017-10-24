#!/usr/bin/env python3

import sys
sys.path.append('../pull_from_sheets')
import gcal_serviceAccount 
import lncdSql
from PyQt5 import uic,QtCore, QtWidgets
import datetime

# google reports UTC, we are EST or EDT. get the diff between google and us
launchtime=int(datetime.datetime.now().strftime('%s'))
tzfromutc = datetime.datetime.fromtimestamp(launchtime) - datetime.datetime.utcfromtimestamp(launchtime)

# get combobox value
def comboval(cb):
    return(cb.itemText(cb.currentIndex()))

# get date from qdate widge 
def caltodate(qdate_widget):
    ordinal = qdate_widget.selectedDate().toPyDate().toordinal()
    dt=datetime.datetime.fromordinal(ordinal)
    return(dt)

class ScheduleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # schedule and checkin data
        self.schedule_what_data = {'fullname': '', 'pid': None, 'date': None, 'time': None}
        self.checkin_what_data =  {'fullname': '', 'vid': None, 'datetime': None}
        

        # load gui (created with qtcreator)
        uic.loadUi('./mainwindow.ui',self)
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

        ## setup search table "people_table"
        pep_columns=['fullname','lunaid','age','dob','sex','lastvisit','maxdrop','studies']
        self.people_table.setColumnCount(len(pep_columns))
        self.people_table.setHorizontalHeaderLabels(pep_columns)
        self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # wire up clicks
        self.people_table.itemClicked.connect(self.people_item_select)

        ## setup search calendar "cal_table"
        cal_columns=['date','time','what']
        self.cal_table.setColumnCount(len(cal_columns))
        self.cal_table.setHorizontalHeaderLabels(cal_columns)
        self.cal_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cal_table.itemClicked.connect(self.cal_item_select)
        # and hook up the calendar date select widget to a query
        self.calendarWidget.selectionChanged.connect(self.search_cal_by_date)
        self.search_cal_by_date() # update for current day
        # TODO: eventually want to use DB instead of calendar. need to update backend!

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
        self.AddPerson = AddPersonWindow(self)
        self.add_person_button.clicked.connect(self.add_person_pushed)
        self.AddPerson.accepted.connect(self.add_person_to_db)

        ## add contact
        self.AddContact = AddContactWindow(self)
        # autocomple stuffs
        self.AddContact.add_ctypes( [ r[0] for r in self.sql.query.list_ctype() ] )
        self.AddContact.suggest_relation([ r[0] for r in self.sql.query.list_relation() ] )
        # connect it up
        self.add_contact_button.clicked.connect(self.add_contact_pushed)
        self.AddContact.accepted.connect(self.add_contact_to_db)

        self.show()

    ###### Generic
    # message to warn about issues
    def mkmsg(self,msg,icon=QtWidgets.QMessageBox.Critical):
           self.msg.setIcon(icon)
           self.msg.setText(msg)
           self.msg.show()
    # used for visit
    def generic_fill_table(self,table,res):
        table.setRowCount(len(res))
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                table.setItem(row_i,col_i,item)
        
        
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
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        self.generic_fill_table(self.visit_table,self.visit_table_data)
        # update contact table
        self.update_contact_table()
        # update schedule text
        self.schedule_what_data['pid']=pid
        self.schedule_what_data['fullname']=fullname
        self.update_schedule_what_label()

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
        check=self.AddContact.isvalid()
        if(not check['valid']):
            mkmsg('Cannot add contact: %s',check['msg'])
            return
        # catch sql error
        self.sqlInsertOrShowErr('contact',self.AddContact.contact_model)
        self.update_contact_table()

    def sqlInsertOrShowErr(self,table,d):
        try:
          #self.sql.query.insert_person(**(self.AddPerson.persondata))
          self.sql.insert(table,d)
        except Exception as e:
          self.mkmsg(str(e))
          return


"""
This class provides a window for adding a person
persondata should be used to modified data
"""
class AddPersonWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        self.persondata={'fname': None, 'lname': None, 'dob': None, 'sex': None,'hand': None, 'source': None}
        super(AddPersonWindow,self).__init__(parent)
        uic.loadUi('./addperson.ui',self)
        self.setWindowTitle('Add Person')

        # change this to true when validation works
        self._want_to_close = False

        ## wire up buttons and boxes
        self.dob_edit.selectionChanged.connect(lambda: self.allvals('dob'))
        self.hand_edit.activated.connect(lambda: self.allvals('hand'))
        self.sex_edit.activated.connect(lambda: self.allvals('sex'))
        self.fname_edit.textChanged.connect(lambda: self.allvals('fname'))
        self.lname_edit.textChanged.connect(lambda: self.allvals('lname'))
        # source
        # todo: toggle visitble of text edit if source is not other, use that value
        self.source_text_edit.textChanged.connect(lambda:self.allvals('source'))

    """
    use provided dictionary d to set persondata
    """
    def setpersondata(self,d):
        print("set person data: %s"%str(d))
        for k in self.persondata.keys():
            if k in d: self.persondata[k] = d[k]

        self.fname_edit.setText(self.persondata['fname'] )
        self.lname_edit.setText(self.persondata['lname'] )

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('updating %s'%key)
        if(key in ['dob','all']):   self.persondata['dob']   = caltodate(self.dob_edit)
        if(key in ['hand','all']):  self.persondata['hand']  = comboval(self.hand_edit)
        if(key in ['sex','all']):   self.persondata['sex']   = comboval(self.sex_edit)
        if(key in ['fname','all']): self.persondata['fname'] = self.fname_edit.text()
        if(key in ['lname','all']): self.persondata['lname'] = self.lname_edit.text()
        # todo, toggle visibility and pick combo or text
        if(key in ['source','all']):
            self.persondata['source']= self.source_text_edit.text()
        

    """
    do we have good data? just check that no key is null
    """
    def isvalid(self):
        self.allvals('all')
        print("add person is valid?\n%s"%str(self.persondata))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.persondata.keys():
            if self.persondata[k] == None or self.persondata[k] == '': return(False)
        # TODO: check dob is not today
        self._want_to_close = True
        return(True)
    
"""
This class provides a window for adding contact information
data in conact_model
"""
class AddContactWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        columns=['ctype','cvalue','relation','who','pid']
        self.contact_model = { k: None for k in columns }
        super(AddContactWindow,self).__init__(parent)
        uic.loadUi('./add_contact.ui',self)
        self.setWindowTitle('Add Contact')

        # change this to true when validation works
        self._want_to_close = False

        ## autocompelte?!
        self.suggestions = {'relation': ['Subject']}

        ## wire up buttons and boxes
        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.who_edit.textChanged.connect(lambda: self.allvals('who'))
        self.relation_edit.textChanged.connect(lambda: self.allvals('relation'))
        self.cvalue_edit.textChanged.connect(lambda: self.allvals('cvalue'))

    def add_ctypes(self,vals): self.ctype_box.addItems(vals)
    def suggest_relation(self,vals): self.suggestions['relation']=vals
    def set_contact(self,pid,name):
        print('updating contact with %s and %s'%(pid,name))
        self.contact_model['pid'] = pid
        self.contact_name.setText(name)
        self.relation_edit.setText('Subject')
        self.who_edit.setText(name)

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('contact: updating %s'%key)
        if(key in ['ctype'   ,'all']): self.contact_model['ctype']    = comboval(self.ctype_box)
        if(key in ['who'     ,'all']): self.contact_model['who']      = self.who_edit.text()
        if(key in ['relation','all']): self.contact_model['relation'] = self.relation_edit.text()
        if(key in ['cvalue'  ,'all']): self.contact_model['cvalue']   = self.cvalue_edit.text()
        

    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("add contact is valid?\n%s"%str(self.contact_model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.contact_model.keys():
            if self.contact_model[k] == None or self.contact_model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid':True,'msg':'OK'})
    
        

# actually launch everything
if __name__ == '__main__':
    app= QtWidgets.QApplication(sys.argv)
    window = ScheduleApp()
    sys.exit(app.exec_())
