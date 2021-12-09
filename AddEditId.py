#!/usr/bin/env python3
from lncdSql import lncdSql
from LNCDutils import *
from LNCDutils import sqlUpdateOrShowErr

from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QPushButton,
    QGridLayout,
    QLabel,
    QLineEdit,
    QDialog,
)
class AddEditIdWindow(QDialog):
    """
    window to add and edit ids
    """

    def __init__(self, parent=None, sql=None):

        super(AddEditIdWindow, self).__init__(parent)
        self.data = {"pid": None, "ids": []} 

        # load xml definition
        self.setWindowTitle("Edit/Add ID")
        # disalbe editing the pid
        self.pid = QtWidgets.QLineEdit()
        self.pid.setDisabled(True)
        self.new_etype = QtWidgets.QComboBox()


    def initUI(self, ids=[]):
        """place the widget in a main window"""
        #grid = QGridLayout()
        #print("here")  
        #
        #for i in range(1,5):
        #    for j in range(1,5):
        #        grid.addWidget(QPushButton("B"+str(i)+str(j)),i,j)
        #self.setLayout(grid)       


        #centralwidget = QtWidgets.QWidget()
        #lay = QtWidgets.QVBoxLayout(centralwidget)
        #lay.addWidget(self.pid)
        #lay.addWidget(self.new_etype)

        self.setGeometry(0, 0, 100, 200)

class AddEditApp(QtWidgets.QMainWindow):
    def __init__(self, sql):
        super().__init__()
        add_edit = AddEditIdWindow(self,sql)
        add_edit.show()

if __name__ == "__main__":
    import sys

    APP = QApplication(sys.argv)
    sql = lncdSql("config_dev.ini", gui=QtWidgets.QApplication.instance())
    win = AddEditApp(sql=sql)

    sys.exit(APP.exec_())
