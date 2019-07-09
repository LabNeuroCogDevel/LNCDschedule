#!/usr/bin/env python
# -*- coding: utf-8 -*-
# to run tests without silengly capturing output:
#   python3 -m pytest test_gui_search.py -s

from schedule import ScheduleApp
from PyQt5.QtWidgets import QApplication
import sys

# initialize QT
app = QApplication(sys.argv)


# using pytest-qt and pytest-pgsql
# lncdapp is a fixuture defined in conftest.py
def test_search_by_name(qtbot, lncdapp):
    # attach tester to window
    qtbot.add_widget(lncdapp)  # attach qt testing robot
    # search by name
    #   test assumes there is only one 'Foran', first name 'Will'
    lncdapp.fullname.setText('% Foran')
    res = lncdapp.people_table_data
    # assert that we found
    assert len(res[0]) > 1
    assert lncdapp.people_table.rowCount() >= 1
    assert res[0][0] == 'Will Foran'


def test_search_by_id(qtbot, lncdapp):
    qtbot.add_widget(lncdapp)  # attach qt testing robot
    # search by name
    #   test assumes there is only one 'Foran', first name 'Will'
    lncdapp.subjid_search.setText('10931')
    res = lncdapp.people_table_data
    # assert that we found
    assert lncdapp.people_table.rowCount() >= 1
    assert res[0][0] == 'Will Foran'


def test_error_bad_age(qtbot, monkeypatch, lncdapp):
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
    # initialize widget
    qtbot.add_widget(lncdapp)  # attach qt testing robot

    # make the error
    lncdapp.max_age_search.setText("one")
    # pause here to see whats going on
    # qtbot.stopForInteraction()

    # test against expected
    expect_msg = "One of the input on the input box is either empty or " + \
                 "not a number, nothing will work. Please fix it and try again"
    assert set_actual_msg.msg == expect_msg
