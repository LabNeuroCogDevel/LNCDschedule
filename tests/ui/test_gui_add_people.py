from schedule import ScheduleApp
import AddPerson
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys
#from pyesql_helper import pyesql_helper as ph


# initialize QT
app = QApplication(sys.argv)


def test_addperson_returns(qtbot):
    """ check setpersondata """
    # persondata={'fname': None, 'lname': None, 'dob': None, 'sex': None,'hand': None, 'source': None}
    w = AddPerson.AddPersonWindow()
    # check we inherit fname
    w.setpersondata({'fname': 'Test'})
    assert w.fname_edit.text() == 'Test'

    # TODO: edit other widgets, check values are returned set in
    # w.AddPerson.persondata


# using pytest-qt
# https://pytest-qt.readthedocs.io/en/latest/note_dialogs.html
def test_add_people_launch(qtbot, monkeypatch, create_db):
    """test that fullnames gets to addperson when buttons clicked"""

    # monkey patch add_erson_pushed to just capture the name passed to it
    def set_name(self):
        set_name.name = self.fullname.text()
    set_name.name = None

    # override default add_person_pushed function with our dummy version
    monkeypatch.setattr("schedule.ScheduleApp.add_person_pushed", set_name)

    # open app with fake db connection
    w = ScheduleApp(sql_obj=(create_db.connection), cal_obj='Not Used')
    qtbot.add_widget(w)  # attach at testing robot

    # change the text in the main window
    w.fullname.setText('% Tian')
    # pretend to open new window
    qtbot.mouseClick(w.add_person_button, Qt.LeftButton)

    # did add_person_button send the name along?
    # assert set_name.name == '% Tian'
