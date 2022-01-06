#!/usr/bin/env python3
from lncdSql import lncdSql

from LNCDutils import mkmsg, sqlUpdateOrShowErr
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
        self.data = {"pid": pid, "ids": {}}
        self.etypes = []  # poplated by set_etypes, from set_etype_options
        # get data
        self.set_new(initialize=True)
        # fixed settings
        self.setWindowTitle("Edit/Add ID")
        self.pid = QtWidgets.QLineEdit(text=pid)
        # always inputs
        self.new_etype = QtWidgets.QComboBox()
        self.new_id = QtWidgets.QLineEdit()
        self.new_button = QtWidgets.QPushButton(text="add new")
        # display
        self.centralwidget = QtWidgets.QWidget()
        self.grid = QGridLayout(self.centralwidget)
        self.widgets = {}  # id, etype submit

        self.wire_up()
        self.set_etype_options()

    def populate_known_ids(self):
        "add rows to grid to edit existing ids"
        # dict of eid, etype, id (see lncdsql.py NOT queries.sql)
        enrolls = self.sql.all_pid_enrolls(pid=self.data["pid"])
        for e in enrolls:
            self.update_grid(e)

    def wire_up(self):
        """
        pid always disabled -- here for reference
        button can be enabled if validation passes
        (just that everything is non-None)
        """
        self.pid.setDisabled(True)
        self.new_button.setDisabled(True)
        self.new_etype.currentIndexChanged.connect(self.validate_new)
        self.new_id.textChanged.connect(self.validate_new)
        self.new_button.clicked.connect(self.add_new_id)
        self.populate_known_ids()

    def eid_current_id(self, eid):
        widget = self.widgets[eid]["id"]
        return widget.text()

    def remove_id(self, eid):
        mkmsg("remove is not implemented!")

    def id_changed(self, eid):
        new_id = self.eid_current_id(eid)
        prev_id = self.data["ids"][eid]["id"]
        widget = self.widgets[eid]["update"]
        is_change = new_id != prev_id
        print(f"text is {new_id}, prev was {prev_id} this is a change? {is_change}")
        widget.setDisabled(not is_change)
        return is_change

    def update_id(self, eid):
        new_id = self.eid_current_id(eid)
        sqlUpdateOrShowErr(self.sql, "enroll", "id", eid, new_id, "eid")

    def update_grid(self, new_dict):
        # NB. eid is uniq int from DB
        eid: int = new_dict.get("eid")
        print(f"update_grid with {new_dict} at {eid}")
        self.data["ids"][eid] = new_dict
        row = len(self.data["ids"])
        self.widgets[eid] = {
            "etype": QtWidgets.QLineEdit(text=new_dict["etype"]),
            "id": QtWidgets.QLineEdit(text=new_dict["id"]),
            "update": QtWidgets.QPushButton(text="update"),
            "remove": QtWidgets.QPushButton(text="remove"),
        }

        # change and update
        self.widgets[eid]["etype"].setDisabled(True)
        self.widgets[eid]["update"].setDisabled(True)
        # change and update
        self.widgets[eid]["id"].textChanged.connect(lambda x: self.id_changed(eid))
        self.widgets[eid]["update"].clicked.connect(lambda x: self.update_id(eid))
        self.widgets[eid]["remove"].clicked.connect(lambda x: self.remove_id(eid))

        self.grid.addWidget(self.widgets[eid]["etype"], row, 1)
        self.grid.addWidget(self.widgets[eid]["id"], row, 2)
        self.grid.addWidget(self.widgets[eid]["update"], row, 3)
        self.grid.addWidget(self.widgets[eid]["remove"], row, 4)
        # TODO: wire up

    def add_new_id(self, event, eid="new"):
        # from validate_new(), like {"etype": etype, "id": id}
        new_dict = self.data["ids"][eid]

        # maybe when testing we wont have self.sql
        if not self.sql:
            print("WARNING: no sql, not adding")
            return

        if eid == "new":
            insert_as = {"pid": self.data["pid"], **new_dict}
            pidres_success = self.sql.insert("enroll", insert_as)
            if pidres_success:
                # lookup what we just added
                # could have used cursor to insert and fetched on that with "returning"
                # but insert w/sqla's table insert is more ergonomic (?)
                # dont want just last_value -- could have a race condition
                cur = self.sql.dict_cur()
                cur.execute(
                    "select eid from enroll where pid = %(pid)s and etype like %(etype)s and id like %(id)s",
                    insert_as,
                )
                new_eid = cur.fetchone()["eid"]
                new_dict["eid"] = new_eid
                self.update_grid(new_dict)
        else:
            # TODO update instead of insert
            pidres_success = False
        return pidres_success

    def set_etypes(self):
        "look to db to get all etypes"
        self.etypes = [x[0] for x in self.sql.query.all_etypes()]

    def only_missing_etypes(self):
        """when adding a new id, we only care about types we dont already have.
        actually this isn't true! we can have multiple of most types (MRID, 7TID, BIRC)
        TODO: probably need to encode if ID can be repeated in DB somewhere"""
        have = [enroll["etype"] for enroll in self.data["ids"]]
        return [x for x in self.etypes if x not in have]

    def set_etype_options(self):
        # for testing
        if not self.sql:
            self.new_etype.addItems([None, "LunaId"])
            return

        self.set_etypes()  # populate self.etypes with all known id types
        self.new_etype.addItems([None] + self.etypes)

    def launch(self, ids=[]):
        """setup and show"""

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
        self.setLayout(self.grid)

        # self.setGeometry(0, 0, 100, 400)
        self.show()

    def validate_new(self):
        if self.new_etype.currentText() and self.new_id.text():
            self.new_button.setDisabled(False)
            self.set_new(initialize=False)
        else:
            self.new_button.setDisabled(True)
            self.set_new(initialize=True)

    def set_new(self, initialize=False):
        if initialize:
            self.data["ids"]["new"] = {"etype": None, "id": None}
        else:
            self.data["ids"]["new"] = {
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
