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

    # Ideally would have non-exclusive check box that, when 'Other' is selected, will take text entered
    # This is alternative approach to check box
    def vtype(self):
        vtype_result = [x.strip() for x in self.vtype_text.text().split(',')]
        self.visit_type_data['vtype'] = json.dumps(vtype_result)
