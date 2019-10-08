from schedule import ScheduleApp
import AddRA
import AddStudy
import AddTask
import AddVisitType
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
#from pyesql_helper import pyesql_helper as phz

# initialize QT
app = QApplication(sys.argv)

def test_addra_returns(qtbot):
    """ check ra_data """
    w = AddRA.AddRAWindow()

    w.ra_text.setText('RA Test')
    assert w.ra_data['ra'] == 'RA Test'

    w.abbr_text.setText('Abbr Test')
    assert w.ra_data['abbr'] == 'Abbr Test'

def test_addstudy_returns(qtbot):
    """ check study data """
    w = AddStudy.AddStudyWindow()

    w.study_text.setText('Study Test')
    assert w.study_data['study'] == 'Study Test'

    w.grantname_text.setText('Grant Test')
    assert w.study_data['grantname'] == 'Grant Test'

    w.cohort_text.setText('Cohort 1,         Cohort 2')
    assert w.study_data['cohorts'] == '["Cohort 1", "Cohort 2"]'

    w.visit_type_text.setText('Visit 1,      Visit 2')
    assert w.study_data['visit_types'] == '["Visit 1", "Visit 2"]'

def test_addtask_returns(qtbot):
    """ check task data """
    w = AddTask.AddTaskWindow()

    w.task_text.setText('Task Test')
    assert w.task_data['task'] == 'Task Test'

    w.measures_text.setText('Measures 1,Measures 2')
    assert w.task_data['measures'] == '["Measures 1", "Measures 2"]'

    w.modes_text.setText('Mode 1, Mode 2')
    assert w.task_data['modes'] == '["Mode 1", "Mode 2"]'

def test_addvisittype_returns(qtbot):
    """ check visit type data """
    w = AddVisitType.AddVisitTypeWindow()

    w.vid_text.setText("1")
    assert w.visit_type_data['vid'] == '1'

    w.pid_text.setText("2")
    assert w.visit_type_data['pid'] == '2'

    w.vtype_text.setText('Vtype 1,       Vtype 2')
    assert w.visit_type_data['vtype'] == '["Vtype 1", "Vtype 2"]'
