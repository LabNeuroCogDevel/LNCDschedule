#!/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
from PyQt5 import uic, QtWidgets
from LNCDutils import comboval, caltodate
from LNCDutils import mkmsg


class AddPersonWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding a person
    persondata should be used to modified data
    """

    def __init__(self, parent=None, sources=None):
        self.persondata = {
            "fname": None,
            "lname": None,
            "dob": None,
            "sex": None,
            "hand": None,
            "source": None,
        }
        super(AddPersonWindow, self).__init__(parent)
        uic.loadUi("./ui/add_person.ui", self)
        self.setWindowTitle("Add Person")

        # change this to true when validation works
        self._want_to_close = False

        # add sources to combo box
        if sources is not None:
            for p_src in sources:
                self.source_cbox.addItem(p_src, p_src)

        # wire up buttons and boxes
        self.dob_edit.selectionChanged.connect(lambda: self.allvals("dob"))
        self.hand_edit.activated.connect(lambda: self.allvals("hand"))
        self.sex_edit.activated.connect(lambda: self.allvals("sex"))
        self.fname_edit.textChanged.connect(lambda: self.allvals("fname"))
        self.lname_edit.textChanged.connect(lambda: self.allvals("lname"))
        # ## source
        # text either dropdown value or entered text (if 'Other' is selected)
        self.source_cbox.currentTextChanged.connect(self.update_cbox)
        self.source_text_edit.textChanged.connect(lambda: self.allvals("source"))

    def update_cbox(self, selected):
        """
        source is pulled from text field
        text field is set by dropdown, unless 'Other' is selected
        then text field is enabled and a new value can be typed in
        """
        if selected != "Other":
            self.source_text_edit.setText(selected)
            self.source_text_edit.setDisabled(True)
        else:
            self.source_text_edit.setText("")
            self.source_text_edit.setDisabled(False)

    def setpersondata(self, dict_in):
        """
        use provided dictionary d to set persondata
        remove '%' from inputs
        """
        print("set person data: %s" % str(dict_in))
        # add dict_in to persondata if we have info
        # remove '%' from any input
        for k in self.persondata.keys():
            if k in dict_in:
                self.persondata[k] = dict_in[k].replace("%", "")
        # set name text items
        self.fname_edit.setText(self.persondata["fname"])
        self.lname_edit.setText(self.persondata["lname"])

    def allvals(self, key="all"):
        """
        set data from gui edit value
        optionally be specific
        """
        print("updating %s" % key)
        if key in ["dob", "all"]:
            self.persondata["dob"] = caltodate(self.dob_edit)
        print(self.persondata["dob"])
        if key in ["hand", "all"]:
            self.persondata["hand"] = comboval(self.hand_edit)
        if key in ["sex", "all"]:
            self.persondata["sex"] = comboval(self.sex_edit)
        if key in ["fname", "all"]:
            self.persondata["fname"] = self.fname_edit.text()
        if key in ["lname", "all"]:
            self.persondata["lname"] = self.lname_edit.text()
        # todo, toggle visibility and pick combo or text
        if key in ["source", "all"]:
            self.persondata["source"] = self.source_text_edit.text()

    def isvalid(self):
        """do we have good data? just check that no key is null"""
        self.allvals("all")
        print("add person is valid?\n%s" % str(self.persondata))
        for k in self.persondata.keys():
            if self.persondata[k] is None or self.persondata[k] == "":
                msg = "%s is empty" % k
                print(msg)
                return (False, msg)

        # TODO: check dob is not today

        print(self.persondata["dob"])
        entered_year = str(self.persondata["dob"]).split("-")[0]
        # Error checking the age of created person
        now = datetime.datetime.now()
        if int(entered_year) >= now.year:
            return (False, "this person seems to be extraordinarily immature(age <= 1)")
        self._want_to_close = True
        return (True, "Valid!")

    def launch_with_name(self, fullname):
        name = fullname.split(" ")
        print("add person: spliting name at len %d" % len(name))
        fname = name[0] if len(name) >= 1 else ""
        lname = " ".join(name[1:]) if len(name) >= 2 else ""
        d = {"fname": fname, "lname": lname}
        self.setpersondata(d)
        self.show()

    def add_person_to_db(self, sql):
        """person to db"""
        print("add person to db persondata: %s" % self.persondata)
        # pop up window and return if not valid
        (valid, msg) = self.isvalid()
        if not valid:
            mkmsg("Person info not valid?! %s" % msg)
            return

        # put error into dialog box
        try:
            # self.sql.query.insert_person(**(self.persondata))
            data = self.persondata
            data["adddate"] = datetime.datetime.now()
            pidres = sql.insert("person", data)
        except Exception as err:
            mkmsg(str(err))
            return

        return self.persondata["fname"] + " " + self.persondata["lname"]
