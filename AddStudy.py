from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *
import json

"""
This class provides a window for adding a person
persondata should be used to modified data
"""
class AddStudyWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        super(AddStudyWindow, self).__init__(parent)
        self.study_data = {}
        uic.loadUi('./ui/add_study.ui',self)
        self.setWindowTitle('Add Person')

        self.study_text.textChanged.connect(self.study)
        self.grantname_text.textChanged.connect(self.grantname)
        self.cohort_text.textChanged.connect(self.cohort)
        self.visit_type_text.textChanged.connect(self.visit_type)

    def study(self):
        self.study_data['study'] = self.study_text.text()

    def grantname(self):
        self.study_data['grantname'] = self.grantname_text.text()

    def cohort(self):
        cohort_result = [x.strip() for x in self.cohort_text.text().split(',')]
        self.study_data['cohorts'] = json.dumps(cohort_result)

    def visit_type(self):
        visit_type_result = [x.strip() for x in self.visit_type_text.text().split(',')]
        self.study_data['visit_types'] = json.dumps(visit_type_result)
