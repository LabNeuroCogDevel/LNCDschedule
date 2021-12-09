#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from lncdSql import lncdSql
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from LNCDutils import comboval, mkmsg, background_drop_color, CMenuItem
import AddPerson
import EditPeople


class PersonTable(QtWidgets.QWidget):
    """table specificly for holding people"""

    # when a new person is selected emit new person info
    person_changed = QtCore.pyqtSignal(dict)  # NB dict=QvarationMap string keys only

    def __init__(self, parent=None, sql=None):
        """expects to get a QtTable widget to reuse"""
        # QtWidgets.__init__(self, parent)
        super().__init__(parent)
        self.sql = sql
        uic.loadUi("./ui/person_widget.ui", self)

        # returns table has 9 columns but not showing last (pid)
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

        # current selection
        self.row_i = -1
        self.NoDropCheck = None  # maybe menu checkbox
        self.luna_search_settings = None  # will be actiongroup

        self.setup_table()
        self.setup_textboxes()
        self.setup_right_click()
        self.setup_add_person()

        # trigger model for editting person info
        self.EditPeople = EditPeople.EditPeopleWindow(self)
        self.EditPeople.accepted.connect(self.change_person_to_db)

    def setup_table(self):
        self.people_table.setColumnCount(len(self.person_columns))
        self.people_table.setHorizontalHeaderLabels(self.person_columns)
        self.people_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # wire up clicks
        self.people_table.itemSelectionChanged.connect(self.people_item_select)

    def setup_textboxes(self):
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

    def setup_add_person(self):
        if self.sql:
            all_sources = [r[0] for r in self.sql.query.list_sources()]
        else:
            all_sources = []
        self.AddPerson = AddPerson.AddPersonWindow(self, sources=all_sources)
        self.add_person_button.clicked.connect(self.add_person_pushed)
        self.AddPerson.accepted.connect(self.add_person_to_db)

    def add_person_pushed(self, fullname):
        "when 'Add' is pushed"
        self.AddPerson.launch_with_name(self.fullname.text())

    def add_person_to_db(self):
        """accepted add person modal"""
        fullname = self.AddPerson.add_person_to_db(self.sql)
        if fullname:
            self.fullname.setText(fullname)
            # likely same name as before so no triggered search
            self.search_people_by_name()

    def setup_right_click(self):
        self.people_table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)
        # ## people context menu
        def select_and_note():
            # right click alone wont populate person
            self.people_item_select()
            raise Exception("not implemented")
            # TODO: emit signal to update note
            # self.add_notes_pushed()

        CMenuItem("Add Note/Drop", self.people_table, select_and_note)
        CMenuItem("Add ID", self.people_table)
        CMenuItem("Edit Person", self.people_table, self.change_person)

    def setup_search_menu_opts(self, menubar):
        "add search menu wiht drops and lunaid settings. used by main app"
        # search settings
        searchMenu = menubar.addMenu("&Search")

        # add items to searchMenu
        # any selection reruns search by name. new settings will be applied
        def mkbtngrp(text):
            return CMenuItem(
                text, searchMenu, lambda x: self.search_people_by_name(), True
            )

        self.NoDropCheck = mkbtngrp("&Drops removed")
        # set up as exclusive (radio button like)
        lany = mkbtngrp("&All")
        lonly = mkbtngrp("&LunaIDs Only")
        lno = mkbtngrp("&Without LunaIDs")
        # create group
        self.luna_search_settings = QtWidgets.QActionGroup(searchMenu)
        self.luna_search_settings.addAction(lonly)
        self.luna_search_settings.addAction(lno)
        self.luna_search_settings.addAction(lany)
        # add to menu
        searchMenu.addAction(lany)
        searchMenu.addAction(lonly)
        searchMenu.addAction(lno)

    def change_person_to_db(self):
        """
        submitted edit from edit_person
        send update to db and refresh display
        """
        self.EditPeople.update_sql(self.sql)
        info = self.EditPeople.updated_info()
        self.fullname.setText(info["fullname"])
        # self.search_people_by_name(info['fullname'])

    def change_person(self):
        """
        edit person from person_table right click
        use current row info stored in 'disp_model'
        """
        # TODO:
        # if render_person is none: throw error message to click first

        info = self.current_person()
        info["dob"] = str(info["dob"])
        # launch module
        self.EditPeople.edit_person(info)
        self.EditPeople.show()

    def add_studies(self):
        study_list = [r[0] for r in self.sql.query.list_studies()]
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
        search = self.update_search_params(search)

        # finally query and update table
        res = self.sql.query.name_search(**search)
        self.fill_search_table(res)

    def update_search_params(
        self,
        search={
            "fullname": "%",
            "maxlunaid": 99999,
            "minlunaid": -1,
            "maxdrop": "family",
        },
    ):
        "search settings optionally from menus in NoDropCheck and luna_search_settings"
        # exclude dropped?
        if self.NoDropCheck and self.NoDropCheck.isChecked():
            search["maxdrop"] = "nodrop"

        # luna id status (all/without/only)
        # TODO: wire to menu
        # setting = self.luna_search_settings.checkedAction()
        setting = None
        if self.luna_search_settings:
            setting = self.luna_search_settings.checkedAction()

        if setting is not None:
            setting = re.sub("&", "", setting.text())
            if re.search("LunaIDs Only", setting):
                search["minlunaid"] = 1
            elif re.search("Without LunaIDs", setting):
                search["maxlunaid"] = 1
        return search

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
        # TODO: okay to return DF of empty?
        # might want to clear other things when no results
        if self.row_i > -1:
            self.person_changed.emit(self.current_person())

        # Color row when clicked -- indicate action target for right click
        self.click_color(self.row_i)

    def current_person(self):
        """return info about selected person"""
        d = self.people_table_data[self.row_i]

        # "fullname", "lunaid", "age", "dob", "sex", "lastvisit", "maxdrop", "studies",
        info = dict(zip(self.person_columns, d))
        info["pid"] = d[8]  # pid not shown

        # dont get fname and lname from table
        # could word split, but need to be accurate at least for edit module
        if self.sql:
            res = self.sql.query.get_name(pid=info["pid"])
            info["fname"] = res[0][0]
            info["lname"] = res[0][1]
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
        self.add_studies()


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

        person_table = PersonTable(self)
        person_table.embed(self.sql)

        # Box Layout to organize our GUI
        lay = QtWidgets.QVBoxLayout(centralwidget)
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

    menubar = WIN.menuBar()
    WIN.person_table.setup_search_menu_opts(menubar)

    sys.exit(APP.exec_())
