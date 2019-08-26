from pyesql_helper import pyesql_helper as ph
from lncdSql import lncdSql
import datetime as dt


def test_db_visit_and_update(create_db):
    """this is the same as test_00_insert_update
    but using visit_summary triggers"""
    lsql = lncdSql(None, conn=ph(create_db.connection))
    time = dt.datetime.now()
    newtime = time + dt.timedelta(days=3)
    fake_visit = {'pid': 1,
                  'study': 'AStudy',
                  'vtimestamp': time,
                  'vtype': 'Scan',
                  'cohort': 'control',
                  'ra': 'ra1',
                  'notes': None}
    lsql.insert('visit_summary', fake_visit)
    assert create_db.connection.\
        execute('select vtimestamp from visit where vid = 1').\
        scalar() == time

    lsql.update(table_name='visit', new_column='vtimestamp',
                id_value=1, new_value=newtime, id_column='vid')

    assert create_db.connection.\
        execute('select vtimestamp from visit where vid = 1').\
        scalar() == newtime


def test_db_visit_and_note(create_db):
    """ add a note with visit_summary
    tests json insert with sqlalchemy"""
    lsql = lncdSql(None, conn=ph(create_db.connection))
    time = dt.datetime.now()
    fake_visit = {'pid': 1,
                  'study': 'AStudy',
                  'vtimestamp': time,
                  'vtype': 'Scan',
                  'cohort': 'control',
                  'ra': 'ra1',
                  'notes': ['test Note']}
    lsql.insert('visit_summary', fake_visit)

    # added visit
    assert create_db.connection.\
        execute('select vtimestamp from visit where vid = 1').\
        scalar() == time

    # added note
    assert create_db.connection.\
        execute('select vid from note where vid = 1').\
        scalar() == 1
