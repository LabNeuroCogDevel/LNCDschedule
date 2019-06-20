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

    
    def setup(self):
        #Clear the entered data everytime
        self.value_box.clear()
        
        #Query the database for the wildcard selected
        print(self.value_box.text())

