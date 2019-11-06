import json
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5 import uic, QtWidgets
# from LNCDutils import  *

    # Todo:
    # delete individual file from list if necessary

class AddTaskWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding a Task
    """

    def __init__(self, parent=None):
        super(AddTaskWindow, self).__init__(parent)
        self.task_data = {}
        self.file_dict = {}
        uic.loadUi('./ui/add_task.ui', self)
        self.setWindowTitle('Add Task')

        min, max, precision = 0, 1000, 2
        # self.double_validator = QDoubleValidator(min, max, precision)
        # self.col_range_text_1.setValidator(double_validator)
        # self.col_range_text_2.setValidator(double_validator)

        self.task_text.textChanged.connect(self.task)
        self.measures_text.textChanged.connect(self.measures)
        self.modes_text.textChanged.connect(self.modes)

        self.browse_button.clicked.connect(self.addFilePath)
        self.add_file_button.clicked.connect(self.addFile)

        self.surveyid_text.textChanged.connect(self.optional)
        self.col_range_text_1.textChanged.connect(self.optional)
        self.col_range_text_2.textChanged.connect(self.optional)

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
        self.file_dict[file_id] = file_loc
        self.task_data['files'] = self.file_dict
        self.file_loc_list.append(file_loc)
        self.file_loc_text.clear()

    # Display file paths when 'Browse' button is selected
    def addFilePath(self):
        file_loc = self.file_loc_text.text()
        file_path = str(QFileDialog.getOpenFileName(parent=self, directory=file_loc)[0])
        if file_path:
            self.file_loc_text.setText(file_path)

    # Handling optional surveyID and col range inputs
    def optional(self):
        self.temp_settings = {}

        self.temp_settings['survey'] = 'qualtrics'
        self.temp_settings['id'] = self.surveyid_text.text()
        self.temp_settings['range'] = [self.col_range_text_1.text(), self.col_range_text_2.text()]

        # Only set settings dict equal to the inputs if no fields are blank - otherwise don't set anything
        if self.temp_settings['id'] != "" and self.temp_settings['range'][0] != "" and self.temp_settings['range'][1] != "":

            # Won't be necessary if the QDoubleValidator can be used to check input instead
            self.temp_settings['range'] = [float(self.col_range_text_1.text()), float(self.col_range_text_2.text())]

            self.task_data['settings'] = self.temp_settings
        else:
            self.task_data['settings'] = None # Make sure this shows up correctly in db
