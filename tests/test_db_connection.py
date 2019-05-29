import configparser
import psycopg2
import psycopg2.sql
# import pyesql


def test_read_config_and_connect():
    cfg = configparser.ConfigParser()
    cfg.read("config.ini")
    constr = 'dbname=%(dbname)s user=%(user)s ' + \
             'host=%(host)s password=%(password)s'
    conn = psycopg2.connect(constr % cfg._sections['SQL'])
    conn.set_session(autocommit=True)
    assert conn is not None
