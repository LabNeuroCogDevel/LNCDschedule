"""
test we can reschedule
"""

import datetime
import sys
import os
import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from pyesql_helper import csv_none
from LNCDcal import LNCDcal


# initialize QT
APP = QApplication(sys.argv)


def test_gui_reschedule(qtbot, lncdapp):
    """
    try to reschedule
    """
    # load in a visit
    csv_none(lncdapp.pgtest, 'sql/visit_summary.csv', 'visit_summary')
    # 2=>Test Subj,2000-01-01 12:34,AStudy,Scan,1,ra1,control,2

    # remove isvalid check (which updates vtype with box value)
    lncdapp.ScheduleVisit.isvalid = lambda: {'valid': True, 'msg': 'OK'}

    # ## select test subject
    # attach tester to window
    qtbot.add_widget(lncdapp)  # attach qt testing robot
    # search by name - defined in person.csv and matching note.csv
    lncdapp.fullname.setText('Test Subj')
    # select the first row in the table
    index = lncdapp.people_table.model().index(0, 1)
    lncdapp.people_table.setCurrentIndex(index)
    # and in the visits table
    index = lncdapp.visit_table.model().index(0, 1)
    lncdapp.visit_table.setCurrentIndex(index)

    # button should be reschedule
    assert lncdapp.schedule_button.text() == 'Reschedule'


    # fake updating the visit model
    now = datetime.datetime.now()
    lncdapp.ScheduleVisit.setup(2, 'Test Subj', 'ra2', now, 'NONE', 1)
    lncdapp.ScheduleVisit.model = \
        {'vtimestamp': now, 'study': 'AStudy',
         'vtype': 'Behave',
         'visitno': 1, 'ra': 'ra2', 'pid': 2,
         'cohort': 'control', 'dur_hr': 2,
         'notes': ['Rescheduled!']}
    lncdapp.schedule_to_db(refresh_model=False)
    # qtbot.stop()  # to check out if selection changed

    # find values in gui
    index = lncdapp.visit_table.model().index(0, 1)
    lncdapp.visit_table.setCurrentIndex(index)
    ui_vtype = lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('vtype')).text()
    ui_vdate = lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('day')).text()

    assert ui_vtype == "Behave"
    assert ui_vdate == now.strftime('%Y-%m-%d')




@pytest.mark.skipif(not os.path.isfile('config_dev.ini'),
                    reason="need config_dev.ini to test config.ini")
def test_gui_reschedule_cal(qtbot, lncdapp):
    """
    try to reschedule
    """
    # add calendar
    lncdapp.cal = LNCDcal('config_dev.ini')

    # ## select test subject
    # attach tester to window
    qtbot.add_widget(lncdapp)  # attach qt testing robot
    # search by name - defined in person.csv and matching note.csv
    lncdapp.fullname.setText('NoNotes Subj')
    # select the first row in the table
    index = lncdapp.people_table.model().index(0, 1)
    lncdapp.people_table.setCurrentIndex(index)

    # remove isvalid check (which updates vtype with box value)
    lncdapp.ScheduleVisit.isvalid = lambda: {'valid': True, 'msg': 'OK'}

    # add visit -- should put visit on calendar
    now = datetime.datetime.now()
    newtime = now + datetime.timedelta(days=2)
    lncdapp.ScheduleVisit.model = \
        {'vtimestamp': now.strftime('%a %b %d %H:%M:%S %Y'),
         'study': 'AStudy', 'vtype': 'Scan',
         'visitno': 1, 'ra': 'ra1', 'pid': 3,
         'cohort': 'control', 'dur_hr': 2, 'notes': None}
    lncdapp.schedule_to_db()

    first_uri = lncdapp.ScheduleVisit.model['googleuri']
    assert first_uri

    # did we add it? have the correct one selected
    assert lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('vid')).text() == "1"
    assert lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('day')).text() == \
        now.strftime('%Y-%m-%d')

    # check inserted to calendar
    assert lncdapp.cal.get_event(first_uri)

    # select new visit
    index = lncdapp.visit_table.model().index(0, 1)
    lncdapp.visit_table.setCurrentIndex(index)

    # set schedule time
    lncdapp.schedule_what_data['date'] = newtime.date()
    lncdapp.schedule_what_data['time'] = newtime.time()

    # disable show and push button
    lncdapp.ScheduleVisit.show = lambda: None
    # set vid and googleuri: run reschedule_visit -> schedule_button_pushed
    qtbot.mouseClick(lncdapp.schedule_button, Qt.LeftButton)
    # update model with our own values
    lncdapp.ScheduleVisit.model = \
        {**lncdapp.ScheduleVisit.model,
         'vtimestamp': newtime.strftime('%a %b %d %H:%M:%S %Y'),
         'study': 'AStudy',
         'vtype': 'Behave',
         'visitno': 1, 'ra': 'ra2',
         'cohort': 'control', 'dur_hr': 2,
         'notes': ['Rescheduled!']}
    print(lncdapp.ScheduleVisit.model)
    # do db stuff
    lncdapp.schedule_to_db(refresh_model=False)
    # qtbot.stop()  # to check out if selection changed

    # find values in gui
    index = lncdapp.visit_table.model().index(0, 1)
    lncdapp.visit_table.setCurrentIndex(index)
    ui_vtype = lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('vtype')).text()
    ui_vdate = lncdapp.visit_table.\
        item(0, lncdapp.visit_columns.index('day')).text()

    assert ui_vtype == "Behave"
    assert ui_vdate == newtime.strftime('%Y-%m-%d')

    scnd_uri = lncdapp.ScheduleVisit.model['googleuri']
    assert scnd_uri
    assert lncdapp.cal.get_event(scnd_uri)['status'] != 'cancelled'
    assert lncdapp.cal.get_event(first_uri)['status'] == 'cancelled'

    # ## clean up test -- remove events from calendar
    lncdapp.cal.delete_event(scnd_uri)

    # remove rescheduled/moved
    from LNCDcal import time2g
    gtime = time2g(newtime)
    old_event = lncdapp.cal.events.\
        list(calendarId=lncdapp.cal.backCalID, singleEvents=True,
             timeMin=gtime, timeMax=gtime).execute()
    if len(old_event) == 1:
        lncdapp.cal.events().\
            delete(eventId=old_event[0]['id'],
                   calendarId=lncdapp.cal.calendarId).\
            execute()
