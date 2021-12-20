#!/usr/bin/env python3
from lncdSql import lncdSql
#from LNCDutils import sqlUpdateOrShowErr
import PyQt5.QtWidgets as QtWidgets
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

    def __init__(self, parent=None, sql=None, pid=None):

        super(AddEditIdWindow, self).__init__(parent)
        # data model
        self.sql = sql
        self.data = {"pid": pid, "ids": []}
        self.set_new(from_input=False)
        # fixed settings
        self.setWindowTitle("Edit/Add ID")
        self.pid = QtWidgets.QLineEdit(text=pid)
        # always inputs
        self.new_etype = QtWidgets.QComboBox()
        self.new_id = QtWidgets.QLineEdit()
        self.new_button = QtWidgets.QPushButton(text="add new")
        self.wire_up()
        self.set_etype_options()

    def wire_up(self):
        """
        pid always disabled -- here for reference
        button can be enabled if validation passes
        (just that everything is non-None
        """
        self.pid.setDisabled(True)
        self.new_button.setDisabled(True)
        self.new_etype.activated.connect(self.validate_new)
        self.new_id.textChanged.connect(self.validate_new)
        self.new_button.clicked.connect(self.new_id)
        
    def update_grid(self, new_dict):
        self.data['ids'] += [new_dict]
        row = len(self.data['ids'])
        #self.grid.addWidget(self.new_etype, row, 1)
        #self.grid.addWidget(self.new_id, row, 2)
        #self.grid.addWidget(self.new_button, row, 3)

    def add_new_id(self):
        new_dict = self.data['new']  # from validate_new(), like {"etype": etype, "id": id}
        pidres = sql.insert("enroll", {"pid": self.data['pid'], **new_dict})
        if pidres:
            self.update_grid(new_dict)
        return pidres

    def set_etype_options(self):
        # for testing
        if not self.sql:
            self.new_etype.addItems([None, "LunaId"])
            return

        etypes = [x[0] for x in self.sql.query.all_etypes()]
        self.new_etype.addItems([None] + etypes)

    def launch(self, ids=[]):
        """setup and show"""

        centralwidget = QtWidgets.QWidget()
        # new
        self.grid = QGridLayout(centralwidget)
        self.grid.addWidget(self.new_etype, 1, 1)
        self.grid.addWidget(self.new_id, 1, 2)
        self.grid.addWidget(self.new_button, 1, 3)
        # edit old
        # TODO: for each id,etype pair
        # create a checkbox to enable edit
        # and edit box
        # and a submit button (change "$etype")

        # lay = QtWidgets.QVBoxLayout(centralwidget)
        # lay.addWidget(self.pid)
        # lay.addWidget(grid)
        self.setLayout(grid)

        # self.setGeometry(0, 0, 100, 400)
        self.show()

    def validate_new(self):
        if self.new_etype.currentText() and self.new_id.text():
            self.new_button.setDisabled(False)
            self.set_new(False)
        else:
            self.new_button.setDisabled(True)
            self.set_new()

    def set_new(self, from_input=True):
        if not from_input:
            self.data["new"] = {"etype": None, "id": None}
        else:
            self.data["new"] = {
                "etype": self.new_etype.currentText(),
                "id": self.new_id.text(),
            }


class AddEditApp(QtWidgets.QMainWindow):
    def __init__(self, sql):
        super().__init__()
        add_edit = AddEditIdWindow(self, sql, pid="1")
        add_edit.launch()


if __name__ == "__main__":
    import sys

    APP = QApplication(sys.argv)
    sql = lncdSql("config_dev.ini", gui=QtWidgets.QApplication.instance())
    win = AddEditApp(sql=sql)

    sys.exit(APP.exec_())
