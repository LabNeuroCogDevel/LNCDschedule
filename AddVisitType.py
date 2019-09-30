from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *
from datetime import datetime
import json

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
        self.vtype_text.textChanged.connect(self.vtype)
        self.visit_type_data['vtimestamp'] = datetime.now()

    def vid(self):
        self.visit_type_data['vid'] = self.vid_text.text()

    def pid(self):
        self.visit_type_data['pid'] = self.pid_text.text()

    # Alternatively
    def vtype(self):
        self.visit_type_data['vtype'] = json.dumps(self.vtype_text.text().split(','))


"""
    # Ideally would like to involve a checkbox with the ability to add text if 'Other' option is selected
    def vtype(self):
        self.visit_type_data['vtype'] = self.vtype_text.buttonPressed()
        print(self.visit_type_data['vtype'])
"""
