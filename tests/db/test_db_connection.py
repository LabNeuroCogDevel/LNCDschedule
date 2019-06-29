# see also
# https://technology.cloverhealth.com/better-postgresql-testing-with-python-announcing-pytest-pgsql-and-pgmock-d0c569d0602a
import configparser
import os.path
import psycopg2
import psycopg2.sql
import pytest
from lncdSql import lncdSql
from pyesql_helper import check_column, pyesql_helper as ph


@pytest.mark.skipif(not os.path.isfile('config.ini'),
                    reason="need config.ini to test config.ini")
def test_read_config_and_connect():
    """
    tests read db in config.ini
    useful to test where code will actually run
    """
    cfg = configparser.ConfigParser()
    cfg.read("config.ini")
    constr = 'dbname=%(dbname)s user=%(user)s ' + \
             'host=%(host)s password=%(password)s'
    conn = psycopg2.connect(constr % cfg._sections['SQL'])
    conn.set_session(autocommit=True)
    assert conn is not None


def test_list_ras(create_db):
    """
    check query.list_ras()
     -- by itself, not that useful. But guide for testing other sql tests
    (create_db in conftest.py, autoloaded by pytest)
    """
    create_db.load_csv('sql/ra.txt', 'ra')  # contains rows for 'ra1' and 'ra2'
    ras = lncdSql(None, conn=ph(create_db.connection)).\
        query.list_ras()
    check_column(0, ras, ['ra1', 'ra2'])
