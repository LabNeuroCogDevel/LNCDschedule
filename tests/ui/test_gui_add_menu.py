import AddRA
import AddStudy
import AddTask
import AddVisitType
from PyQt5.QtWidgets import QApplication
import sys

# from pyesql_helper import pyesql_helper as phz

# initialize QT
# APP = QApplication(sys.argv)
# 20211130 - removed to stop segfault


def test_addra_returns(qtbot):
    """check ra_data"""
    w = AddRA.AddRAWindow()

    w.ra_text.setText("Test RA")
    assert w.ra_data["ra"] == "Test RA"

    w.abbr_text.setText("Test Abbr")
    assert w.ra_data["abbr"] == "Test Abbr"


def test_addstudy_returns(qtbot):
    """check study data"""
    w = AddStudy.AddStudyWindow()

    w.study_text.setText("Test Study")
    assert w.study_data["study"] == "Test Study"

    w.grantname_text.setText("Test Grant")
    assert w.study_data["grantname"] == "Test Grant"

    w.cohort_text.setText("Test Cohort 1    ,         Test Cohort 2")
    assert w.study_data["cohorts"] == '["Test Cohort 1", "Test Cohort 2"]'

    w.visit_type_text.setText("Test Visit 1   ,      Test Visit 2")
    assert w.study_data["visit_types"] == '["Test Visit 1", "Test Visit 2"]'


def test_addtask_returns(qtbot):
    """check task data"""
    w = AddTask.AddTaskWindow()

    w.task_text.setText("Test Task")
    assert w.task_data["task"] == "Test Task"

    w.measures_text.setText("Test Measures 1,Test Measures 2")
    assert w.task_data["measures"] == '["Test Measures 1", "Test Measures 2"]'

    w.modes_text.setText("Test Mode 1, Test Mode 2")
    assert w.task_data["modes"] == '["Test Mode 1", "Test Mode 2"]'


def test_addvisittype_returns(qtbot):
    """check visit type data"""
    w = AddVisitType.AddVisitTypeWindow()

    w.vid_text.setText("1")
    assert w.visit_type_data["vid"] == "1"

    w.pid_text.setText("2")
    assert w.visit_type_data["pid"] == "2"

    w.vtype_text.setText("Test Vtype 1,      Test Vtype 2")
    assert w.visit_type_data["vtype"] == '["Test Vtype 1", "Test Vtype 2"]'
