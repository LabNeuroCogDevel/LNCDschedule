import json
import FileDialog
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
        self.FileDialog = FileDialog.FileDialogWindow()


        self.task_text.textChanged.connect(self.task)
        self.measures_text.textChanged.connect(self.measures)
        self.modes_text.textChanged.connect(self.modes)

        self.add_file_button.clicked.connect(self.addFile)
        self.add_file_button.clicked.connect(self.addFileTree) # This should be embedded in the AddTask window


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

        # Backup way to add file locations if QFileDialog does not work
        """
        file_loc = self.file_loc_text.text()
        self.file_loc_list.append(file_loc)
        self.file_loc_text.clear()
        """
    def addFileTree(self):
        self.FileDialog.initUI()
