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

class ScheduleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # get other modules for querying db and calendar
        # need ~/.pgpass
        self.cal = gcal_serviceAccount.LNCDcal()
        self.sql = lncdSql.lncdSql()

        # schedule and checkin data
        self.schedule_what_data = {'fullname': '', 'pid': None, 'date': None, 'time': None}
        self.checkin_what_data =  {'fullname': '', 'vid': None, 'datetime': None}
        

        # load gui (created with qtcreator)
        uic.loadUi('./mainwindow.ui',self)
        self.setWindowTitle('LNCD Scheduler')

        ## setup person search field
        # by name
        self.fullname.textChanged.connect(self.search_people_by_name)
        self.fullname.setText('%')
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

        self.show()

    ###### Generic
    # used for visit
    def generic_fill_table(self,table,res):
        table.setRowCount(len(res))
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                table.setItem(row_i,col_i,item)
        
        
    ###### PEOPLE


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
        # update visit table
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        self.generic_fill_table(self.visit_table,self.visit_table_data)
        # update contact table
        self.contact_table_data=self.sql.query.contact_by_pid(pid=pid)
        self.generic_fill_table(self.contact_table,self.contact_table_data)
        # update schedule text
        self.schedule_what_data['pid']=pid
        self.schedule_what_data['fullname']=d[1]
        self.update_schedule_what_label()

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
        selectedQdate=self.calendarWidget.selectedDate().toPyDate()
        dt=datetime.datetime.fromordinal( selectedQdate.toordinal() )
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

# actually launch everything
if __name__ == '__main__':
    app= QtWidgets.QApplication(sys.argv)
    window = ScheduleApp()
    sys.exit(app.exec_())
