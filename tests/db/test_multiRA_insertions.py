import sys
import pytest
import time
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication
from pyesql_helper import csv_none

# initialize QT
# -- otherwise we get "Aborted" when running just this file
APP = QApplication(sys.argv)

# N.B.
#  run and get debugger shell when fails
#   python3 -m pytest --pdb tests/db/test_multiRA_insertions.py
#   python3 -m pip install pdbpp --user # for a better debugger
# use qtbot.stop() to look at gui


def test_multi_ra_gui(qtbot):
    pytest.skip("keyboard doesn't follow 'selected'!")
    # TODO: maybe don't care about going out of order
    # just enter the first 2 and always go 1 then 2 ?

    import MultiRA
    win = MultiRA.ChosenMultipleRAWindow()
    win.setup(['ra1', 'ra2', 'ra3'])
    win.show()

    # select one
    assert False
    qtbot.mouseDClick(win.choices, Qt.LeftButton)

    win.ras.item(2).setSelected(True)
    time.sleep(.100)
    win.ras.setFocus()
    qtbot.keyClick(win.ras, Qt.Key_Enter, delay=100)  # 100ms to let signal hit
    assert win.get_data() == ['ra3']

    # unselect it
    win.ras.setFocus()
    qtbot.keyClick(win.choices, Qt.Key_Enter, delay=100)  # 100ms to let signal hit
    assert win.get_data() == []

    # TODO: select more than one
    print(win.get_data())



def test_db_multi_ra_insertion(lncdapp, qtbot):
    """ can we assign more than one RA to a visit? """

    # Test the function of assing multi_RA
    # RAs defined in sql/ra.txt (ra1 to ra4)
    fake_ra_selected = ['ra1', 'ra2', 'ra4']

    # ## setup visit ##
    vid = 1
    # create vid 1 with sql/visit_summary.csv
    # not done by lncdapp in conftest.py fixture. so load it here
    csv_none(lncdapp.pgtest, 'sql/visit_summary.csv', 'visit_summary')

    # not needed because gcal part fails silently.
    # maybe a problem for other things?
    # # but no googleuri in csv file. this is needed
    # lncdapp.pgtest.connection.execute(
    #     "update visit set googleuri='http://junk' where vid=%d" % vid)

    # actually run the thing we want to test!
    lncdapp.multira_to_db_operaiton(fake_ra_selected, vid)
    # qtbot.stop()  # DEBUG: stop GUI and see what messags have poped up

    # Check whether the data is successfully inserted in the database
    # execute returns a sqlalchemy.engine.result.ResultProxy
    # get as a familiar list of tuples using fetchall()
    ra_assigned = lncdapp.pgtest.connection.execute(
        """select ra from visit_action
         where vid = vid and action = 'assigned'"""
        ).fetchall()

    # ## check all are RAs are assigned in db ##
    # same length
    assert len(ra_assigned) == len(fake_ra_selected)
    # same values
    for db_ra in ra_assigned:
        assert db_ra[0] in fake_ra_selected


def test_db_multi_ra_change_assigned(lncdapp):
    """ mutli ra also re-assigns prevously assigned """

    csv_none(lncdapp.pgtest, 'sql/visit_summary.csv', 'visit_summary')
    lncdapp.multira_to_db_operaiton(['ra1', 'ra2'], 1)
    lncdapp.multira_to_db_operaiton(['ra3', 'ra4'], 1)

    pytest.skip()
    # TODO: remove skip and
    # query assigned ras, make sure there are only 2 and that they are ra3+4
