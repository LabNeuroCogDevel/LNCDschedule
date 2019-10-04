from schedule import ScheduleApp
import AddRA
import AddStudy
import AddTask
import AddVisitType
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
# from pyesql_helper import pyesql_helper as ph


# initialize QT
app = QApplication(sys.argv)


# So far just testing that everything returns
# Will next do similar to test_add_people_launch

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


def test_addtask_returns(qtbot):
    """ check task data """
    w = AddTask.AddTaskWindow()

    w.task_text.setText('Task Test')
    assert w.task_data['task'] == 'Task Test'
