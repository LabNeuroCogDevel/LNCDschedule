import sys
import pytest
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from datetime import datetime


APP = QApplication(sys.argv)


def test_add_ra_insertion(lncdapp, qtbot):
    import AddRA
    win = AddRA.AddRAWindow()

    win.ra_data['ra'] = "RA Test 1"
    win.ra_data['abbr'] = "RT1"
    current_date_time = datetime.now()
    win.ra_data['start_date'] = current_date_time

    # pretend win was part of lncdapp, make ra_data match
    lncdapp.AddRA.ra_data = win.ra_data
    lncdapp.add_ra_to_db()

    # did we insert the ra we wanted to
    ra_assigned = lncdapp.pgtest.connection.execute("select * from ra where ra like 'RA Test 1'").fetchall()
    # assert 0==1 # uncomment and use pytest --pdb to inspect env
    assert len(ra_assigned) == 1
    assert ra_assigned[0][0] == win.ra_data['ra']
    assert ra_assigned[0][2] == win.ra_data['abbr']
    assert ra_assigned[0][3] == current_date_time


def test_add_study_insertion(lncdapp, qtbot):
    import AddStudy
    win = AddStudy.AddStudyWindow()

    win.study_data['study'] = "Test Study"
    win.study_data['grantname'] = "Test Grantname"
    win.study_data['cohorts'] = "['Test Cohort 1', 'Test Cohort 2']"
    win.study_data['visit_types'] = "['Visit Type 1', 'Visit Type 2']"

    lncdapp.AddStudy.study_data = win.study_data
    lncdapp.add_study_to_db()

    study_assigned = lncdapp.pgtest.connection.execute("select * from study where study like 'Test Study'").fetchall()

    assert len(study_assigned) == 1
    assert study_assigned[0][0] == win.study_data['study']
    assert study_assigned[0][1] == win.study_data['grantname']
    assert study_assigned[0][2] == win.study_data['cohorts']
    assert study_assigned[0][3] == win.study_data['visit_types']


def test_add_task_insertion(lncdapp, qtbot):
    import AddTask
    win = AddTask.AddTaskWindow()

    win.task_data['task'] = "Test Task"
    win.task_data['measures'] = "['Test Measure 1', 'Test Measure 2']"
    win.task_data['modes'] = "['Test Mode 1', 'Test Mode 2']"

    lncdapp.AddTask.task_data = win.task_data
    lncdapp.add_task_to_db()

    task_assigned = lncdapp.pgtest.connection.execute("select * from task where task like 'Test Task'").fetchall()

    assert len(task_assigned) == 1
    assert task_assigned[0][0] == win.task_data['task']
    assert task_assigned[0][2] == win.task_data['measures']
    assert task_assigned[0][5] == win.task_data['modes']


def test_add_visit_type_insertion(lncdapp, qtbot):
    """adding a visit type"""
    import AddVisitType
    win = AddVisitType.AddVisitTypeWindow()

    current_date_time = datetime.now()
    win.visit_type_data['vid'] = "1"
    win.visit_type_data['pid'] = "2"
    win.visit_type_data['vtype'] = "Scan"
    win.visit_type_data['vtimestamp'] = current_date_time

    lncdapp.AddVisitType.visit_type_data = win.visit_type_data
    lncdapp.add_visit_type_to_db()

    visit_type_assigned = lncdapp.pgtest.connection.\
        execute("select * from visit where vid = 1").fetchall()

    assert len(visit_type_assigned) == 1
    assert visit_type_assigned[0][0] == int(win.visit_type_data['vid'])
    assert visit_type_assigned[0][1] == int(win.visit_type_data['pid'])
    assert visit_type_assigned[0][2] == win.visit_type_data['vtype']
    assert visit_type_assigned[0][6] == current_date_time


def test_add_multiple_visit_type_insertion(lncdapp, qtbot):
    """ visit type with mlutple vtype """
    pytest.skip("TODO: support multiple vtypes?? is this misguided?")
    import AddVisitType
    import simplejson as json
    win = AddVisitType.AddVisitTypeWindow()

    current_date_time = datetime.now()
    win.visit_type_data['vid'] = "1"
    win.visit_type_data['pid'] = "2"
    win.visit_type_data['vtype'] = '["Scan", "eeg"]'
    win.visit_type_data['vtimestamp'] = current_date_time

    lncdapp.AddVisitType.visit_type_data = win.visit_type_data
    lncdapp.add_visit_type_to_db()

    visit_type_assigned = lncdapp.pgtest.connection.\
        execute("select * from visit where vid like '1'").fetchall()

    assert len(visit_type_assigned) == 1
    vtypelist = json.loads(win.visit_type_data['vtype'])
    assert visit_type_assigned[0][2] == vtypelist
