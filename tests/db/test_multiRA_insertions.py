import sys
import pytest
from pyesql_helper import csv_none
from PyQt5.QtWidgets import QApplication

# initialize QT
# -- otherwise we get "Aborted" when running just this file
APP = QApplication(sys.argv)

# N.B.
#  run and get debugger shell when fails
#   python3 -m pytest --pdb tests/db/test_multiRA_insertions.py
# use qtbot.stop() to look at gui


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
