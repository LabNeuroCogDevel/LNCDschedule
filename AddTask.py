import json
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5 import uic, QtWidgets
# from LNCDutils import  *


class AddTaskWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding a Task
    """
    # Todo:
    # connect to database (add to self.task_data)
    # way to delete files after they are added to the list?
    # optional stuff outlined in issue #37

    def __init__(self, parent=None):
        super(AddTaskWindow, self).__init__(parent)
        self.task_data = {}
        uic.loadUi('./ui/add_task.ui', self)
        self.setWindowTitle('Add Task')

        self.task_text.textChanged.connect(self.task)
        self.measures_text.textChanged.connect(self.measures)
        self.modes_text.textChanged.connect(self.modes)

        self.browse_button.clicked.connect(self.addFilePath)
        self.add_file_button.clicked.connect(self.addFile)

    def task(self):
        self.task_data['task'] = self.task_text.text()

    def measures(self):
        measures_result = [x.strip() for x in self.measures_text.text().split(',')]
        self.task_data['measures'] = json.dumps(measures_result)

    def modes(self):
        modes_result = [x.strip() for x in self.modes_text.text().split(',')]
        self.task_data['modes'] = json.dumps(modes_result)

    def addFile(self):
        file_id = self.file_id_text.text()
        self.file_id_list.append(file_id)
        self.file_id_text.clear()

        file_loc = self.file_loc_text.text()
        self.file_loc_list.append(file_loc)
        self.file_loc_text.clear()

    def addFilePath(self):
        file_loc = self.file_loc_text.text()
        file_path = str(QFileDialog.getOpenFileName(parent=self, directory=file_loc)[0])
        if file_path:
            self.file_loc_text.setText(file_path)
