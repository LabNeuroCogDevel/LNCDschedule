import configparser
import psycopg2, psycopg2.sql
import pyesql

cfg = configparser.ConfigParser()
cfg.read("config.ini")
constr = 'dbname=%(dbname)s user=%(user)s host=%(host)s password=%(password)s'%cfg._sections['SQL']
conn = psycopg2.connect(constr)
conn.set_session(autocommit=True)
print("Connect successful");