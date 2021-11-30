from PyQt5 import uic, QtCore, QtWidgets
from LNCDutils import *

"""
This class provides a window for editing contact information
data in conact_model
"""


class EditContactWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):

        # Global variable to make things more convenient
        self.row_i = 0
        self.table = None

        columns = ["ctype", "changes", "cid"]
        self.edit_model = {k: None for k in columns}

        super(EditContactWindow, self).__init__(parent)
        uic.loadUi("./ui/edit_contact.ui", self)
        self.setWindowTitle("Edit Contact")
        ## wire up buttons and boxes
        self.ctype_box.activated.connect(self.formatter)
        self.ctype_box.activated.connect(self.autoPopulate)
        self.ctype_box.activated.connect(lambda: self.allvals("ctype"))
        self.value_box.textChanged.connect(lambda: self.allvals("value"))

    def autoPopulate(self):
        self.contact_columns = ["who", "cvalue", "relation", "status", "added"]
        currentText = self.ctype_box.currentText()

        # Get the current text based on the ctype_box value that's entered
        if currentText != "null":
            col_i = self.contact_columns.index(currentText)
        else:
            return

        data = self.table.item(self.row_i, col_i).text()
        # Populate the data to the value box
        self.value_box.setText(data)

    def allvals(self, key="all"):
        if key in ["ctype", "all"]:
            self.edit_model["ctype"] = self.ctype_box.currentText()
        if key in ["value", "all"]:
            self.edit_model["changes"] = self.value_box.text()

    def edit_contact(self, cid, table):

        self.value_box_2.setText(str(cid))
        self.value_box_2.setDisabled(True)
        self.edit_model["cid"] = cid

        # Get the current row
        self.table = table
        self.row_i = table.currentRow()

    def formatter(self):
        want_edit = str(self.ctype_box.currentText())
        default_value = self.edit_model.get(want_edit, "")
        self.value_box.setText(default_value)
