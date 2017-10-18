import psycopg2
import pyesql

class lncdSql():
    def __init__(self):
        self.conn = psycopg2.connect('dbname=lncddb user=lncd host=arnold.wpic.upmc.edu')

        sqls = pyesql.parse_file('./ids.sql')
        self.query = sqls(self.conn)
        #a=self.query.name_search(fullname='%Foran%')
