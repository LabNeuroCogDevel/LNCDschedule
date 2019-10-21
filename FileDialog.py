#!/usr/bin/python
import sys
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon

class FileDialogWindow(QWidget):


    def __init__(self):
        super().__init__()

        # maybe use these to embed
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480

    def initUI(self):

        self.openFileNameDialog()

        self.show()

    # Don't want to be able to open files, just want to select them
    # Find out where file structure starts
    def openFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "", "Python Files (*.py)", options=options)
        if fileName:
            print(fileName)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = FileDialogWindow()
    sys.exit(app.exec_())
