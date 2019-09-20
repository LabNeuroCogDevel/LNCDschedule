import json
from PyQt5 import uic, QtWidgets
# from LNCDutils import  *


class AddRAWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding an RA
    """

    def __init__(self, parent=None):
        super(AddRAWindow, self).__init__(parent)
        self.study_data = {}
        uic.loadUi('./ui/add_RA.ui', self)
        self.setWindowTitle('Add RA')

        self.study_text.textChanged.connect(self.study)
        self.grantname_text.textChanged.connect(self.grantname)
        self.cohort_text.textChanged.connect(self.cohort)
        self.visit_type_text.textChanged.connect(self.visit_type)

    def study(self):
        self.study_data['study'] = self.study_text.text()

    def grantname(self):
        self.study_data['grantname'] = self.grantname_text.text()

    def cohort(self):
        self.study_data['cohorts'] = json.dumps(self.cohort_text.text().split(','))

    def visit_type(self):
        self.study_data['visit_types'] = json.dumps(self.visit_type_text.text().split(','))
