

from schedule import ScheduleApp
from PyQt5.QtWidgets import QApplication
import sys


#initialize QT
app = QApplication(sys.argv)

#using pytest-qt
def test_add_people(qtbot):
    w = ScheduleApp()
    qtbot.add_widget(w) #attach at testing robot
    w.name.setText('% Tian')
    qtbot.mouseClick(w.add_person_button,QtCore.Qt.LeftButton)


