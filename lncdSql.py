import psycopg2
import psycopg2.sql
import pyesql
import configparser
import PasswordDialog


class lncdSql():
    def __init__(self, config, gui=None):
        # read config.ini file like
        # [SQL]
        #  host=...
        #  dbname=...
        #  ..
        cfg = configparser.ConfigParser()
        cfg.read(config)
        confline = 'dbname=%(dbname)s user=%(user)s host=%(host)s'
        # if we specify a port, use it
        if cfg._sections['SQL'].get('port'):
            confline += " port=%(port)s"

        # if the config doesn't have a username, we will try to get one
        if not cfg._sections['SQL'].get('user'):
            if gui is None or gui is False:
                raise Exception('No username in config file' +
                                'and no gui to authenticate requested!')
            else:
                user_pass = PasswordDialog.user_pass(gui)
                cfg._sections['SQL']['user'] = user_pass['user']
                cfg._sections['SQL']['password'] = user_pass['pass']

        # only set password if its not empty
        # otherise we can continue without using a password... maybe
        if cfg._sections['SQL']['password']:
            confline += " password=%(password)s"

        constr = confline % cfg._sections['SQL']

        print('connecting with %s' % constr)
        self.conn = psycopg2.connect(constr)
        self.conn.set_session(autocommit=True)

        sqls = pyesql.parse_file('./queries.sql')
        self.query = sqls(self.conn)
        # a=self.query.name_search(fullname='%Foran%')

    """
    make a table and a list of names (dict key) and
    create a psycopg2 sql object that can be executed
    """
    def mkinsert(self, table, colnames):
        table=psycopg2.sql.Identifier(table)
        # are keys and values order always stable??
        cols=map(psycopg2.sql.Identifier,colnames);
        vals=map(psycopg2.sql.Placeholder,colnames)

        col=psycopg2.sql.SQL(",").join(cols)
        valkey=psycopg2.sql.SQL(",").join(vals)

        insertsql=psycopg2.sql.SQL("insert into {} ({}) values ({})").\
           format(table, col,valkey)
        return(insertsql)

    def mkupdate(self,table,id_column, id, new_value, id_type):
        table = psycopg2.sql.Identifier(table)
        id_column = psycopg2.sql.Identifier(id_column)
        id_type = psycopg2.sql.Identifier(id_type)
        #new_value = psycopg2.sql.Placeholder(new_value)
        #new_value = psycopg2.sql.SQL(",").join(new_value)
        id = psycopg2.sql.Placeholder(new_value)

        updatesql = psycopg2.sql.SQL("UPDATE {} SET {} = %s where {} = %s").\
           format(table, id_column, id_type)
        print(updatesql.as_string(self.conn))
        return updatesql

    def insert(self,table,d):
        sql=self.mkinsert(table,d.keys())
        print(sql.as_string(self.conn)%d)
        cur=self.conn.cursor()
        cur.execute(sql,d)
        cur.close()

    def update(self,table_name, id_column, id, column_change, id_type):
        sql = self.mkupdate(table_name, id_column, id, column_change, id_type)
        cur=self.conn.cursor()
        cur.execute(sql, (column_change, id))
        cur.close()
        """
        table eg contact
        column_change like cvalue
        id_column like cid
        value is like new phone number en\tered at gui
        id is whatever cid to change for value
        """
