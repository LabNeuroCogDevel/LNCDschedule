from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  *
import json
import pprint
from psycopg2 import IntegrityError
import lncdSql, sys
from PyQt5.QtWidgets import QLabel
"""
This class provides a window for demonsting data in visit table based on the wild-cards typed in 
"""

class VisitsCardsWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):

        super(VisitsCardsWindow, self).__init__(parent)
        uic.loadUi('./ui/visit_table_cards.ui', self)
        self.setWindowTitle('More Information')

    
    def setup(self, pid, sql):
        #Query the database for the wildcard selected
        self.sql = sql
        print(self.value_box.text())
        self.data = self.sql.search(pid, 'visit_summary', self.options.currentText(), self.value_box.text())
        print(self.data)


