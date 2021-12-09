"""
test we can find a note in the main gui
"""

import sys
from PyQt5.QtWidgets import QApplication
from pyesql_helper import csv_none

# initialize QT
# APP = QApplication(sys.argv)
# 20211130 - removed to stop segfault


def test_notes_populate(qtbot, lncdapp):
    """
    simpelest note test: find a person, click them, check the note is there
      using pytest-qt and pytest-pgsql
      lncdapp is a fixuture defined in conftest.py
    """

    # attach tester to window
    qtbot.add_widget(lncdapp)  # attach qt testing robot
    # search by name - defined in person.csv and matching note.csv
    lncdapp.PromotedPersonTable.fullname.setText("Will Foran")
    # select the first row in the table
    index = lncdapp.PromotedPersonTable.people_table.model().index(0, 1)
    lncdapp.PromotedPersonTable.people_table.setCurrentIndex(index)
    # qtbot.stop() # to check out if selection changed

    # assert that we found the expected note
    nidx = lncdapp.note_columns.index("note")
    note = lncdapp.note_table_data[0][nidx]
    assert note == "Test Note"
