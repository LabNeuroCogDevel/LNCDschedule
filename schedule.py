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

class ScheduleApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # get other modules for querying db and calendar
        # need ~/.pgpass
        self.cal = gcal_serviceAccount.LNCDcal()
        self.sql = lncdSql.lncdSql()

        # load gui (created with qtcreator)
        uic.loadUi('./mainwindow.ui',self)
        self.setWindowTitle('LNCD Scheduler')

        # setup person search field
        self.fullname.textChanged.connect(self.search_people_by_name)
        self.fullname.setText('%')

        # setup search table "people_table"
        pep_columns=['fullname','lunaid','curagefloor','dob','sex','lastvisit','maxdrop','studies']
        self.people_table.setColumnCount(len(pep_columns))
        self.people_table.setHorizontalHeaderLabels(pep_columns)
        self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # setup search calendar "cal_table"
        cal_columns=['date','time','what']
        self.cal_table.setColumnCount(len(cal_columns))
        self.cal_table.setHorizontalHeaderLabels(cal_columns)
        self.cal_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # and hook up the calendar to a query
        self.calendarWidget.selectionChanged.connect(self.search_cal_by_date)

        self.show()

        
    ###### PEOPLE

    def search_people_by_id(self,lunaid):
        return
        if(len(fullname) != 5 ): return
        res = self.sql.query.id_search(lunaid=lunaid)
        self.fill_search_table(res)

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

    """
    fill the person search table
    expected columns are from pep_columns (8)
    res is a list of vectors(8) from sql query
    """ 
    def fill_search_table(self,res):
        self.people_table.setRowCount(len(res))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i,row in enumerate(res):
            for col_i,value in enumerate(row):
                item=QtWidgets.QTableWidgetItem(str(value))
                self.people_table.setItem(row_i,col_i,item)


    ###### CALENDAR
    
    def search_cal_by_date(self):
        selectedQdate=self.calendarWidget.selectedDate().toPyDate()
        dt=datetime.datetime.fromordinal( selectedQdate.toordinal() )
        print(dt)
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

# actually launch everything
if __name__ == '__main__':
    app= QtWidgets.QApplication(sys.argv)
    window = ScheduleApp()
    sys.exit(app.exec_())
