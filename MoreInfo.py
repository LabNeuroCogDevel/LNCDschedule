from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  *
import json
import pprint
from psycopg2 import IntegrityError
import lncdSql, sys
"""
This class provides a window for demonstrating information
data in checkin
"""
class MoreInfoWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):

        super(MoreInfoWindow,self).__init__(parent)

        #sql = lncdSql.lncdSql() # need ~/.pgpass
        uic.loadUi('./ui/more_info.ui',self)
        self.setWindowTitle('More Informaiton')

    def setup(self,vid,sql):

        study_tasks = sql.query.get_tasks(vid = vid)
        self.tasks_list.itemClicked.connect(self.tasks_choice)
        measures = sql.query.get_measures(vid = vid, task = task)
        #stuffs on the first column
        for item in study_tasks:
            self.tasks_list.insertItems(0,item)

        #Change it to the dictionary from a list
        measures = measures[0][0]
        #Add rhe task as one columns before adding all the keys
        pep_columns = measures.keys()
        self.info_table.setColumnCount(len(pep_columns))
        self.info_table.setHorizontalHeaderLabels(pep_columns)
        self.info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def tasks_choice(self):
        task = item
        print(task)

    #pep_columns=['fullname','lunaid','age','dob','sex','lastvisit','maxdrop','studies']
    #self.people_table.setColumnCount(len(pep_columns))
    #self.people_table.setHorizontalHeaderLabels(pep_columns)
    #self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
    # wire up clicks
    #self.people_table.itemClicked.connect(self.people_item_select)
    #self.people_table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

