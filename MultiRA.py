from PyQt5 import uic, QtCore, QtWidgets
from LNCDutils import *

"""
This class provides a window for adding contact information
data in conact_model
"""


class ChosenMultipleRAWindow(QtWidgets.QDialog):
    def __init__(self, parent=None):

        super(ChosenMultipleRAWindow, self).__init__(parent)
        uic.loadUi("./ui/multi_RA.ui", self)
        self.setWindowTitle("MultipleRA selection")

        self.ras.itemActivated.connect(self.itemActivated_event)
        self.choices.itemActivated.connect(self.undo_adding)

        # Create a list to add all the items in the list
        self.item_list = []

    def setup(self, ra):

        # Refresh
        self.ras.clear()
        self.choices.clear()

        # Set the ra to the list widget
        for a in ra:
            self.ras.addItem(a)

    # Funciton to add the double-clicked item to the choices list
    def itemActivated_event(self, item):
        # Remove items from the first list and add to the second list
        self.ras.takeItem(self.ras.row(item))
        self.choices.addItem(item.text())

    def undo_adding(self, item):
        # Remove items from the second list and add to the fist list
        self.choices.takeItem(self.choices.row(item))
        self.ras.addItem(item.text())

    def get_data(self):
        for index in range(self.choices.count()):
            self.item_list.append(self.choices.item(index).text())
        return self.item_list
