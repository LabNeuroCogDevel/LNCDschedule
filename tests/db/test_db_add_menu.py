import sys
import pytest
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from datetime import datetime


APP = QApplication(sys.argv)


def test_add_ra_insertion(lncdapp, qtbot):
    import AddRA
    win = AddRA.AddRAWindow()

    win.ra_data['ra'] = "RA Test 1"
    win.ra_data['abbr'] = "RT1"
    current_date_time = datetime.now()
    win.ra_data['start_date'] = current_date_time

    # pretend win was part of lncdapp, make ra_data match
    lncdapp.AddRA.ra_data = win.ra_data
    lncdapp.add_ra_to_db()

    # did we insert the ra we wanted to
    ra_assigned = lncdapp.pgtest.connection.execute("select * from ra where ra like 'RA Test 1'").fetchall()
    # assert 0==1 # uncomment and use pytest --pdb to inspect env
    assert len(ra_assigned) == 1
    assert ra_assigned[0][0] == win.ra_data['ra']
    assert ra_assigned[0][2] == win.ra_data['abbr']
    assert ra_assigned[0][3] == current_date_time
