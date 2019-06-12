from schedule import ScheduleApp
import AddPerson
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys


# initialize QT
app = QApplication(sys.argv)


# using pytest-qt
# https://pytest-qt.readthedocs.io/en/latest/note_dialogs.html
def test_add_people_launch(qtbot, monkeypatch):
    """test that fullnames gets to addperson when buttons clicked"""
    # monkey patch add_erson_pushed to just capture the name passed to it
    def set_name(self):
        set_name.name = self.fullname.text()
    set_name.name = None
    monkeypatch.setattr("schedule.ScheduleApp.add_person_pushed", set_name)

    w = ScheduleApp()
    qtbot.add_widget(w)  # attach at testing robot
    w.fullname.setText('% Tian')
    qtbot.mouseClick(w.add_person_button, Qt.LeftButton)

    # did it work?!
    assert set_name.name == '% Tian'


def test_addperson_returns(qtbot):
    # persondata={'fname': None, 'lname': None, 'dob': None, 'sex': None,'hand': None, 'source': None}
    w = AddPerson.AddPersonWindow()
    # check we inheret fname
    w.setpersondata({'fname': 'Test'})
    assert w.fname_edit.text() == 'Test'

    # TODO: edit other widgets, check values are returned set in
    # w.AddPerson.persondata
