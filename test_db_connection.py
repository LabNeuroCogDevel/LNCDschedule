import configparser
import psycopg2
import psycopg2.sql
import lncdSql
# import pyesql


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


def test_fakedb(transacted_postgresql_db):
    # conn = postgresql_db.engine.connect()

    # AttributeError: 'Connection' object has no attribute 'cursor'
    conn = transacted_postgresql_db.connection
    sql = lncdSql.lncdSql(None, conn=conn)
    sql.query.list_ras()

