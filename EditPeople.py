from PyQt5 import uic, QtCore, QtWidgets
from LNCDutils import *


class EditPeopleWindow(QtWidgets.QDialog):
    """
    This class provides a window for editing person information
     * edit_model stores data
     * ui described by ui/edit_person.ui
     * edit_person updates the modal and initializates the popup
    """

    def __init__(self, parent=None):
        super(EditPeopleWindow, self).__init__(parent)
        # set default values for ui
        columns = ["ctype", "changes", "pid"]
        self.edit_model = {k: None for k in columns}

        # load xml definition
        uic.loadUi("./ui/edit_person.ui", self)
        self.setWindowTitle("Edit person")
        # disalbe editing the pid
        self.value_box_2.setDisabled(True)

        # what happens when the combo box is change?
        self.ctype_box.activated.connect(self.formatter)

        # wire up buttons and boxes
        self.ctype_box.activated.connect(lambda: self.allvals("ctype"))
        self.value_box.textChanged.connect(lambda: self.allvals("value"))

    def allvals(self, key="all"):
        """
        set all ui elements to match their corresponding data model
        """
        if key in ["ctype", "all"]:
            self.edit_model["ctype"] = self.ctype_box.currentText()
        if key in ["value", "all"]:
            self.edit_model["changes"] = self.value_box.text()

    def edit_person(self, data):
        """
        called from outside world to update the modal controller/data
        :param data: dict with keys: pid, dob, fname, lname
        """
        self.data = data
        print("Editing person with data like: %s" % data)
        self.value_box_2.setText(str(data["pid"]))
        self.edit_model["pid"] = data["pid"]

    def formatter(self):
        """
        populate edit box with default (previous) value
        """
        want_edit = str(self.ctype_box.currentText())
        default_value = self.data.get(want_edit, "")
        self.value_box.setText(default_value)
