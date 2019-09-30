import json
from PyQt5 import uic, QtWidgets
from datetime import datetime
# from LNCDutils import  *


class AddRAWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding an RA
    """

    def __init__(self, parent=None):
        super(AddRAWindow, self).__init__(parent)
        self.ra_data = {}
        uic.loadUi('./ui/add_ra.ui', self)
        self.setWindowTitle('Add RA')

        self.ra_text.textChanged.connect(self.ra)
        self.abbr_text.textChanged.connect(self.abbr)
        self.ra_data['start_date'] = datetime.now()

    def ra(self):
        self.ra_data['ra'] = self.ra_text.text()

    def abbr(self):
        self.ra_data['abbr'] = self.abbr_text.text()
