import json
from PyQt5 import uic, QtWidgets
# from LNCDutils import  *


class AddTaskWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding a Task
    """

    def __init__(self, parent=None):
        super(AddTaskWindow, self).__init__(parent)
        self.task_data = {}
        uic.loadUi('./ui/add_task.ui', self)
        self.setWindowTitle('Add Task')

        self.task_text.textChanged.connect(self.task)
        self.measures_text.textChanged.connect(self.measures)
        self.modes_text.textChanged.connect(self.modes)


    def task(self):
        self.task_data['task'] = self.task_text.text()

    def measures(self):
        measures_result = [x.strip() for x in self.measures_text.text().split(',')]
        self.task_data['measures'] = json.dumps(measures_result)

    def modes(self):
        modes_result = [x.strip() for x in self.modes_text.text().split(',')]
        self.task_data['modes'] = json.dumps(modes_result)
