from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *
#import json

"""
This class provides a window for adding a visit type
"""

class AddVisitTypeWindow(QtWidgets.QDialog):

    def __init__(self, parent=None):
        super(AddVisitTypeWindow, self).__init__(parent)
        self.visit_type_data = {}
        uic.loadUi('./ui/add_visit_type.ui', self)
        self.setWindowTitle('Add Visit Type')

        self.vid_text.textChanged.connect(self.vid)
        self.pid_text.textChanged.connect(self.pid)
        self.visit_type_data['vtype'] = self.vtype_text.connect(self.vtype) ###


        # Be able to select multiple visit types, including 'Other' - if other is selected bring up a text box

    def vid(self):
        self.visit_type_data['vid'] = self.vid_text.text()

    def pid(self):
        self.visit_type_data['pid'] = self.pid_text.text()

    def vtype(self):
        self.visit_type_data['vtype'] = self.vtype_text.text()

"""
    def vtype(self): # Trying to make this a radio button
        self.visit_type_data['vtype'] = self.vtype_text.checkedButton().text()
        # Button has .text() function - need to get selected button
"""
