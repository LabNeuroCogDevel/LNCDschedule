from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  mkmsg
from LNCDutils import  *
import simplejson as json
import pprint
from psycopg2 import IntegrityError
import lncdSql, sys
from PyQt5.QtWidgets import QLabel
from Q_retrieve import retrieve_name
from numpy import nan
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QVBoxLayout
from PyQt5.QtGui import QIcon
# from file_explorer import FileSearch

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
        self.file_search.clicked.connect(self.file_explorer)

    def setup(self,vid,sql):
        #Clear the tasks_list every time
        self.tasks_list.clear()
        self.list_view.clear()
        #Clear the table every time as well
        #self.info_table.clear()
        study_tasks = sql.query.get_tasks(vid = vid)
        self.sql = sql
        self.vid = vid
        # TODO: not called?
        self.table_fill
        #stuffs on the first column
        for item in study_tasks:
            self.tasks_list.insertItems(0,item)
    def file_explorer(self):
        # 20201222: unsure what this would do
        # ex = FileSearch()
        mkmsg("not implemented")

    def table_fill(self):
        """
        when task is clicked from left list. fill right list
        """

        # TODO: not all tasks will be Qualtrics tasks
        #       older tasks already in the DB shouldn't fail

        # check we have task
        if self.task is None:
            #Don't query for the measures of the task
            print("No tasks have been selected")
            return

        # check to see if we have in db already
        res = self.sql.query.get_measures(vid=self.vid, task=self.task)

        # res should always return something!
        # Otherwise there would be nothign to click
        if res is None:
            mkmsg('BUG: no db results for %s @ %s! but is still in display?!' %
                  (self.vid, self.task))
            return

        # if no measures, try Qualtrics
        if res[0][0] is None:
            data_df = retrieve_name(self.vid, self.task)
            if data_df.empty:
                mkmsg('No related qualtrics task for this person')
                return
            else:
                measures = data_df.to_dict('dict')
                data_db = json.loads(json.dumps(measures, ignore_nan=True))
                self.add_task(data_db, vtid=res[0][1])
                
        else:
            measures = res[0][0]
            if isinstance(measures, str):
                mkmsg("ERROR in data storage. measures should be objects not strings, consider:\n" +
                      "update visit_task set measures = NULL where vid = %s task like '%s'" % (self.vid, self.task))
                print(res[0][0])
                return
                # N.B. need single quotes for bad qualitrics?
                # TODO: remove \ escape characters?
                measures = json.loads('"%s"' % res[0][0])


        # Set up the list
        values = ["%s => %s" % (k, v) for k, v in measures.items()]
        self.list_view.insertItems(0, values)
        #print(pep_columns)

        #Set up the table
        #self.info_table.setColumnCount(len(pep_columns))
        #self.info_table.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        #self.info_table.setHorizontalHeaderLabels(pep_columns)
        #self.info_table.resizeColumnsToContents()
        #self.info_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

    def add_task(self, measures, vtid):
        self.sql.update('visit_task', 'measures', vtid,
                        new_value=measures, id_column='vtid')
        print('Successfully pushed to the database')

    #Function to get the task that has been clicked
    def task_clicked(self, item):
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

