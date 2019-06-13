from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  *
import json
import pprint
from psycopg2 import IntegrityError
import lncdSql, sys
from PyQt5.QtWidgets import QLabel
"""
This class provides a window for demonstrating information
data in checkin
"""

#Task as a global variable
class MoreInfoWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
    
        super(MoreInfoWindow,self).__init__(parent)
        self.task = None
        self.sql = None
        self.vid = None

        #sql = lncdSql.lncdSql() # need ~/.pgpass
        uic.loadUi('./ui/more_info.ui',self)
        self.setWindowTitle('More Informaiton')
        #Task that has been selected
        self.tasks_list.itemClicked.connect(self.task_clicked)
        self.tasks_list.itemClicked.connect(self.table_fill)

    def setup(self,vid,sql):
        #Clear the tasks_list every time
        self.tasks_list.clear()
        self.list_view.clear()
        #Clear the table every time as well
        #self.info_table.clear()
        study_tasks = sql.query.get_tasks(vid = vid)
        self.sql = sql
        self.vid = vid
        self.table_fill
        #stuffs on the first column
        for item in study_tasks:
            self.tasks_list.insertItems(0,item)
    
    def table_fill(self):
        if self.task is None:
            #Don't query for the measures of the task
            print("No tasks have been selected")
        else:
            measures = self.sql.query.get_measures(vid = self.vid, task = self.task)
            #Change it to the dictionary from a list
            measures = measures[0][0]
            #Measures contain all the measured data of one task that has been selected.
            #Add rhe task as one columns before adding all the keys
            if(measures is not None):
                pep_columns = measures.keys()
                pep_values = measures.values()
            else:
                mkmsg('measures is none')

            #Set up the list
            value = []
            try:
                for key, val in measures.items():
                    if val is None:
                        value.append(str(key)+'=>'+'None')
                    else:
                        value.append(str(key)+'=>'+str(val))
                    self.list_view.insertItems(0,value)
            except AttributeError:
                print('Nontype')
            #print(pep_columns)

            #Set up the table
            #self.info_table.setColumnCount(len(pep_columns))
            #self.info_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
            #self.info_table.setHorizontalHeaderLabels(pep_columns)
            #self.info_table.resizeColumnsToContents()
            #self.info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    #Function to get the task that has been clicked
    def task_clicked(self,item):
        print("item has been selected")
        row_i = self.tasks_list.row(item)
        self.task = self.tasks_list.item(row_i).text()
        print(self.task)
        



    #pep_columns=['fullname','lunaid','age','dob','sex','lastvisit','maxdrop','studies']
    #self.people_table.setColumnCount(len(pep_columns))
    #self.people_table.setHorizontalHeaderLabels(pep_columns)
    #self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    # wire up clicks
    #self.people_table.itemClicked.connect(self.people_item_select)
    #self.people_table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

