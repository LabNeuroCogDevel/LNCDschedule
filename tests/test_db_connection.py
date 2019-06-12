# see also
# https://technology.cloverhealth.com/better-postgresql-testing-with-python-announcing-pytest-pgsql-and-pgmock-d0c569d0602a
import configparser
import psycopg2
import psycopg2.sql
from lncdSql import lncdSql
import pytest
from pyesql_helper import check_column, pyesql_helper as ph


@pytest.fixture
def create_db(transacted_postgresql_db):
    """
    creates db when used as param in any 'test_fucntion'
    returns transacted_postgresql_db so it doesn't also have to be included
    """
    transacted_postgresql_db.run_sql_file('sql/03_mkschema.sql')
    return(transacted_postgresql_db)


def test_read_config_and_connect():
    """
    tests read db in config.ini
    useful to test where code will actually run
    """
    # TODO: if cannot read config.ini: pass
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
    """
    create_db.load_csv('sql/ra.txt', 'ra')  # contains rows for 'ra1' and 'ra2'
    ras = lncdSql(None, conn=ph(create_db.connection)).\
        query.list_ras()
    check_column(0, ras, ['ra1', 'ra2'])
