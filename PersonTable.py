#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from lncdSql import lncdSql
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from LNCDutils import comboval, mkmsg, background_drop_color


class PersonTable(QtWidgets.QWidget):
    """table specificly for holding people"""

    # when a new person is selected emit row that changed
    person_changed = QtCore.pyqtSignal(dict) #NB dict=QvarationMap string keys only

    def __init__(self, parent=None, sql=None):
        """expects to get a QtTable widget to reuse"""
        #QtWidgets.__init__(self, parent)
        super().__init__(parent)
        self.sql = sql
        uic.loadUi("./ui/person_widget.ui", self)
        self.person_columns = [
            "fullname",
            "lunaid",
            "age",
            "dob",
            "sex",
            "lastvisit",
            "maxdrop",
            "studies",
        ]
        self.people_table.setColumnCount(len(self.person_columns))
        self.people_table.setHorizontalHeaderLabels(self.person_columns)
        self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # wire up clicks
        self.people_table.itemSelectionChanged.connect(self.people_item_select)
        self.people_table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # current selection
        self.row_i = -1
        # TODO: this must be wired to menu
        self.NoDropCheck = False
        # if self.NoDropCheck.isChecked():
        #    search['maxdrop'] = 'nodrop'

        # ## setup person search field
        # by name
        self.fullname.textChanged.connect(self.search_people_by_name)
        self.fullname.setText("")
        # doesnt already happens, why?
        # self.search_people_by_name(
        #     self.fullname.text() + "%"
        # ) 

        # by lunaid
        self.subjid_search.textChanged.connect(self.search_people_by_id)
        # by attribute
        self.min_age_search.textChanged.connect(self.search_people_by_att)
        self.max_age_search.textChanged.connect(self.search_people_by_att)
        self.sex_search.activated.connect(self.search_people_by_att)
        self.study_search.activated.connect(self.search_people_by_att)

    def add_studies(self, study_list):
        self.study_search.addItems(study_list)

    def search_people_by_att(self, *argv):
        # Error check
        if (
            self.max_age_search.text() == ""
            or self.min_age_search.text() == ""
            or not self.max_age_search.text().isdigit()
            or not self.min_age_search.text().isdigit()
        ):
            mkmsg(
                "One of the input on the input box is either "
                + "empty or not a number, nothing will work. "
                + "Please fix it and try again"
            )
            return

        d = {
            "study": comboval(self.study_search),
            "sex": comboval(self.sex_search),
            "minage": self.min_age_search.text(),
            "maxage": self.max_age_search.text(),
        }
        print("search attr: %s" % d)
        res = self.sql.query.att_search(**d)
        # res = self.sql.query.att_search(
        #  sex=d['sex'],study=d['study'],
        #  minage=d['minage'],maxage=d['maxage'])
        self.fill_search_table(res)

    def search_people_by_name(self, fullname=None):
        if fullname is None:
            fullname = self.fullname.text()

        # only update if we've entered 3 or more characters
        # .. but let wildcard (%) go through
        if len(fullname) < 3 and not re.search("%", fullname):
            return

        # use maxdrop and lunaid range to add exclusions
        search = {
            "fullname": fullname,
            "maxlunaid": 99999,
            "minlunaid": -1,
            "maxdrop": "family",
        }

        # exclude dropped?
        if self.NoDropCheck:
            search["maxdrop"] = "nodrop"

        # luna id status (all/without/only)
        # TODO: wire to menu
        # setting = self.luna_search_settings.checkedAction()
        setting = None
        if setting is not None:
            setting = re.sub("&", "", setting.text())
            if re.search("LunaIDs Only", setting):
                search["minlunaid"] = 1
            elif re.search("Without LunaIDs", setting):
                search["maxlunaid"] = 1

        # finally query and update table
        res = self.sql.query.name_search(**search)
        self.fill_search_table(res)

    # seach by id
    def search_people_by_id(self, lunaid):
        if lunaid == "" or not lunaid.isdigit():
            mkmsg("LunaID should only be numbers")
            return
        if len(lunaid) != 5:
            try:
                res = self.sql.query.lunaid_search_all(lunaid=lunaid)
            except ValueError:
                mkmsg("LunaID should only be numbers")
            self.fill_search_table(res)
            return
        try:
            lunaid = int(lunaid)
        except ValueError:
            mkmsg("LunaID should only be numbers")
            return
        res = self.sql.query.lunaid_search(lunaid=lunaid)
        self.fill_search_table(res)

    def fill_search_table(self, res):
        self.people_table_data = res
        self.people_table.setRowCount(len(res))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i, row in enumerate(res):
            for col_i, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.people_table.setItem(row_i, col_i, item)
        if res:
            self.changing_color(row_i, res)

    def changing_color(self, row_i, res):
        """
        Change the color after the textes have been successfully inserted.
        based on drop level
        """
        # drop_j = self.person_columns.index('maxdrop')
        drop_j = 6
        drop_colors = {
            "subject": QtGui.QColor(249, 179, 139),
            "visit": QtGui.QColor(240, 230, 140),
            "future": QtGui.QColor(240, 240, 240),
            "unknown": QtGui.QColor(203, 233, 109),
        }

        # N.B. this could go in previous for loop. left here for clarity
        for row_i, row in enumerate(res):
            droplevel = row[drop_j]
            # don't do anything if we don't have a color for this drop level
            if droplevel is None or droplevel == "nodrop":
                continue
            drop_color = drop_colors.get(droplevel, drop_colors["unknown"])
            # go through each column of the row and color it
            for j in range(self.people_table.columnCount()):
                self.people_table.item(row_i, j).setBackground(drop_color)

    def people_item_select(self):
        """
        when person row is selected, update the person model
        """
        # Whenever the people table subjects have been selected
        #  grey out the checkin button
        self.row_i = self.people_table.currentRow()
        self.person_changed.emit(self.current_person())

        # Color row when clicked -- indicate action target for right click
        self.click_color(self.row_i)

    def current_person(self):
        """return info about selected person"""
        d = self.people_table_data[self.row_i]

        #"fullname", "lunaid", "age", "dob", "sex", "lastvisit", "maxdrop", "studies",
        info = dict(zip(self.person_columns,d))
        info['pid'] = d[8] # pid not shown
        return info
        # # main model
        # self.checkin_button.setEnabled(False)
        # print('people table: subject selected: %s' % d[8])
        # self.render_person(pid=d[8], fullname=d[0], age=d[2],
        #                    sex=d[4], lunaid=d[1])
        # self.render_schedule(ScheduleFrom.PERSON)

    def bg_reset(self):
        """repaint background for all cells. drop rows colored differently
        also see: LNCDutils.background_reset (does not do drops)
        """
        drop_column_idx = 6
        for row_i in range(self.people_table.rowCount()):
            drop_type = self.people_table.item(row_i, drop_column_idx).text()
            bg_qtcolor = background_drop_color(drop_type)
            for col_i in range(self.people_table.columnCount()):
                self.people_table.item(row_i, col_i).setBackground(bg_qtcolor)

    def click_color(self, row_i):
        """
        change color of all cells in a row.
        not tracking what was previusly clicked.
        insetad resetting all colors"""
        self.bg_reset()
        select_rgb = (191, 243, 228)
        select_color = QtGui.QColor(*select_rgb)
        for col_i in range(self.people_table.columnCount()):
            # when table changes row_i may no longer exist (None)
            if self.people_table.item(row_i, col_i):
                self.people_table.item(row_i, col_i).setBackground(select_color)

    def embed(self, sql):
        self.sql = sql
        self.search_people_by_name("%")
        #self.setGeometry(0, 0, self.width() + 20, self.height() + 20)


class PersonOnlyApp(QtWidgets.QMainWindow):
    """wrap widget up for testing it out"""

    def __init__(self, sql):
        super().__init__()
        self.sql = sql
        self.initUI()

    def initUI(self):
        """place the widget in a main window"""
        centralwidget = QtWidgets.QWidget()
        self.setCentralWidget(centralwidget)
        lay = QtWidgets.QVBoxLayout(centralwidget)
        # Box Layout to organize our GUI
        # labels
        person_table = PersonTable(self, self.sql)
        lay.addWidget(person_table)
        self.setGeometry(0, 0, person_table.width() + 20, person_table.height() + 20)
        self.person_table = person_table
        self.show()


if __name__ == "__main__":
    # for LNCDutils
    #  PYTHONPATH="$PYTHONPATH:$(pwd)" ./table/PersonTable.py
    import sys

    APP = QtWidgets.QApplication(sys.argv)
    sql = lncdSql("config_dev.ini", gui=QtWidgets.QApplication.instance())
    WIN = PersonOnlyApp(sql=sql)

    study_list = [r[0] for r in sql.query.list_studies()]
    WIN.person_table.add_studies(study_list)

    sys.exit(APP.exec_())
