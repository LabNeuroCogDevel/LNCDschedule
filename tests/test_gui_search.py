#!/usr/bin/env python
# -*- coding: utf-8 -*-
# to run tests without silengly capturing output:
#   python3 -m pytest test_gui_search.py -s

from schedule import ScheduleApp
from PyQt5.QtWidgets import QApplication
import sys

# initialize QT
app = QApplication(sys.argv)


# using pytest-qt
def test_search_by_name(qtbot):
    w = ScheduleApp()    # initialize widget
    qtbot.add_widget(w)  # attach qt testing robot
    # search by name
    #   test assumes there is only one 'Foran', first name 'Will'
    w.fullname.setText('% Foran')
    res = w.people_table_data
    # assert that we found
    assert len(res[0]) > 1
    assert w.people_table.rowCount() >= 1
    assert res[0][0] == 'Will Foran'


def test_search_by_id(qtbot):
    w = ScheduleApp()    # initialize widget
    qtbot.add_widget(w)  # attach qt testing robot
    # search by name
    #   test assumes there is only one 'Foran', first name 'Will'
    w.subjid_search.setText('10931')
    res = w.people_table_data
    # assert that we found
    assert w.people_table.rowCount() >= 1
    assert res[0][0] == 'Will Foran'


def test_error_bad_age(qtbot, monkeypatch):
    """
    error when age is not a number.
    monkeypatch 'mkmsg' to capture error message
    see https://pytest-qt.readthedocs.io/en/latest/note_dialogs.html
    """
    # patch to fake mkmsg function
    # sets internal variable to message received (should be error msg)
    def set_actual_msg(*args):
        set_actual_msg.msg = args[0]
    set_actual_msg.msg = None
    # patch mkmsg as imported by schedule (N.B. not patching LNCDutils.mkmsg)
    monkeypatch.setattr("schedule.mkmsg", set_actual_msg)

    # startup app
    w = ScheduleApp()    # initialize widget
    qtbot.add_widget(w)  # attach qt testing robot

    # make the error
    w.max_age_search.setText("one")
    # pause here to see whats going on
    # qtbot.stopForInteraction()

    # test against expected
    expect_msg = "One of the input on the input box is either empty or " + \
                 "not a number, nothing will work. Please fix it and try again"
    assert set_actual_msg.msg == expect_msg
