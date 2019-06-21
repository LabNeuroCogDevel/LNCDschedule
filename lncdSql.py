import psycopg2
import psycopg2.sql
import pyesql
import configparser
import PasswordDialog
import re  # just for censoring password


class lncdSql():
    """ database interface for lncddb """

    def __init__(self, config, gui=None, conn=None):

        # can only have one master QT app pointer
        # so record it in the class (or None/False if not using it)

        if config is not None:
            constr = connstr_from_config(config, gui)
            print('connecting: ' +
                  re.sub('password=[^\\s]+', 'password=*censored*', constr))
            self.conn = psycopg2.connect(constr)
            self.conn.set_session(autocommit=True)
        elif conn is not None:
            self.conn = conn
        else:
            raise Exception("Bad arguments! need config or conn")

        sqls = pyesql.parse_file('./queries.sql')
        self.query = sqls(self.conn)
        # a=self.query.name_search(fullname='%Foran%')

        # test connection permissions
        # query will error if user not given permission
        # see sql/04_add-RAs.sql
        print('testing db connection')
        # TODO: why do we need to rethrow error for it to stop the gui?!
        try:
            self.query.get_lunaid_from_pid(pid=1)
        except Exception as err:
            print('error! %s' % err)
            raise Exception("No permissions on db: %s" % err)

    def mkupdate(self, table, id_column, id, new_value, id_type):
        table = psycopg2.sql.Identifier(table)
        id_column = psycopg2.sql.Identifier(id_column)
        id_type = psycopg2.sql.Identifier(id_type)
        # TODO: something is funny here!! new_value/id is never used?!
        # new_value = psycopg2.sql.Placeholder(new_value)
        # new_value = psycopg2.sql.SQL(",").join(new_value)
        id = psycopg2.sql.Placeholder(new_value)

        updatesql = psycopg2.sql.SQL("UPDATE {} SET {} = %s where {} = %s").\
            format(table, id_column, id_type)
        print(updatesql.as_string(self.conn))
        return updatesql

    def insert(self, table, d):
        """ convience function to usert data into a table """
        sql = mkinsert(table, d.keys())
        print(sql.as_string(self.conn) % d)
        cur = self.conn.cursor()
        cur.execute(sql, d)
        cur.close()

    def update(self, table_name, id_column, id, column_change, id_type):
        """
        update a table with given data
        :param table_name: eg contact
        :param id_column: like cid
        :param id:  whatever cid to change for value
        :param column_change: like cvalue
        :param id_type:  like new phone number entered at gui
        """
        sql = self.mkupdate(table_name, id_column, id, column_change, id_type)
        cur = self.conn.cursor()
        cur.execute(sql, (column_change, id))
        cur.close()


def connstr_from_config(config, gui):
    """
    return connection string after reading config file
    can use a gui to get user/pass if needed
    """
    # TODO: move to utils? does not depend on "self"
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
    return(constr)


def mkinsert(table, colnames):
    """
    make a table and a list of names (dict key) and
    create a psycopg2 sql object that can be executed
    """
    table = psycopg2.sql.Identifier(table)
    # are keys and values order always stable??
    cols = map(psycopg2.sql.Identifier, colnames)
    vals = map(psycopg2.sql.Placeholder, colnames)

    col = psycopg2.sql.SQL(",").join(cols)
    valkey = psycopg2.sql.SQL(",").join(vals)

    insertsql = psycopg2.sql.SQL("insert into {} ({}) values ({})").\
        format(table, col, valkey)
    return(insertsql)
