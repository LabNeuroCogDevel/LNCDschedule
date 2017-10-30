import psycopg2, psycopg2.sql
import pyesql
import configparser

class lncdSql():
    def __init__(self,config):
        # read config.ini file like
        # [SQL]
        #  host=...
        #  dbname=...
        #  ..
        cfg = configparser.ConfigParser()
        cfg.read(config)
        constr = 'dbname=%(dbname)s user=%(user)s host=%(host)s password=%(password)s'%cfg._sections['SQL']
        #print('connecting with %s'%constr)
        #self.conn = psycopg2.connect('dbname=lncddb user=lncd host=arnold.wpic.upmc.edu')
        self.conn = psycopg2.connect(constr)
        self.conn.set_session(autocommit=True)

        sqls = pyesql.parse_file('./queries.sql')
        self.query = sqls(self.conn)
        #a=self.query.name_search(fullname='%Foran%')

    """
    make a table and a list of names (dict key) and
    create a psycopg2 sql object that can be executed 
    """
    def mkinsert(self,table,colnames):
        table=psycopg2.sql.Identifier(table)
        # are keys and values order always stable??
        cols=map(psycopg2.sql.Identifier,colnames);
        vals=map(psycopg2.sql.Placeholder,colnames)

        col=psycopg2.sql.SQL(",").join(cols)
        valkey=psycopg2.sql.SQL(",").join(vals)

        insertsql=psycopg2.sql.SQL("insert into {} ({}) values ({})").format(table, col,valkey)
        return(insertsql)

    def insert(self,table,d):
        sql=self.mkinsert(table,d.keys())
        print(sql.as_string(self.conn)%d)
        cur=self.conn.cursor()
        cur.execute(sql,d)
        cur.close()
