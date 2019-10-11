import sys
import pytest
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from datetime import datetime


APP = QApplication(sys.argv)


def test_add_ra_insertion(lncdapp, qtbot):
    import AddRA
    win = lncdapp.AddRAWindow()

    win.ra_data['ra'] = "RA Test 1"
    win.ra_data['abbr'] = "Abbr Test 1"
    current_date_time = datetime.now()
    win.ra_data['start_date'] = current_date_time

    lncdapp.add_ra_to_db(win)
    ra_assigned = lncdapp.pgtest.connection.execute().fetchall()
    print(ra_assigned)
