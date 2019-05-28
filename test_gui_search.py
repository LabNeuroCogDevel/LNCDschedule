#!/usr/bin/env python
# -*- coding: utf-8 -*-
from schedule import ScheduleApp
from pytestqt import qtbot
from PyQt5 import Qt


# using pytest-qt
def test_search():
    app = ScheduleApp()
    qtbot.addWiget(app)
    app.fullname.setText('% Foran')
    res = app.people_table_data
    print(res[0])
    assert len(res) > 0
    assert res[0]['fname'] == 'Will'
