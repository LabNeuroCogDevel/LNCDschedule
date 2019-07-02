import psycopg2
import psycopg2.sql
import pyesql
import configparser
import PasswordDialog
import re  # just for censoring password


class lncdSql():
    """ database interface for lncddb """

    def __init__(self, config, gui=None, conn=None):
        """
        :param config: file used to configure connection
        :param gui: pointer to QtApp. used for password prompt
        :param conn: connection to use instead of config (for testing)
        """

        # can only have one master QT app pointer
        # so record it in the class (or None/False if not using it)

        if conn is not None:
            self.conn = conn
        elif config is not None:
            constr = connstr_from_config(config, gui)
            print('connecting: ' +
                  re.sub('password=[^\\s]+', 'password=*censored*', constr))
            self.conn = psycopg2.connect(constr)
            self.conn.set_session(autocommit=True)
        else:
            raise Exception("Bad arguments! need config or conn")

        # define database user
        self.db_user = cur_user(self.conn)

        sqls = pyesql.parse_file('./queries.sql')
        self.query = sqls(self.conn)
        # a=self.query.name_search(fullname='%Foran%')

        # try connection permissions if we are using e.g. config.ini
        #  (otherwise we are probably in a test and dont want this check)
        # query will error if user not given permission
        # see sql/04_add-RAs.sql
        if config:
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
        """ convience function to insert data into a table """
        sql = mkinsert(table, d.keys())
        print("inserting into %s values %s" % (table, d))
        # print(sql.as_string(self.conn) % d)
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

    def remove_visit(self, vid):
        """ remove visit by pid
        :param vid: visit id to remove (integer)
        """
        sqlstr = "delete from visit where vid = %d" % int(vid)
        cur = self.conn.cursor()
        cur.execute(sqlstr)
        cur.close()

    def mksearch(self, option):
        # Special casew for vtimestamp b/c
        # date is formatted differently from the database
        if option == 'vtimestamp':
            searchsql = """
            SELECT
                to_char(vtimestamp,'YYYY-MM-DD'), studys,
                vtype, vscore, age, notes, dvisit, dperson, vid
            FROM visit_person_view
            where
               pid = %s and
               to_char(vtimestamp,'YYYY-MM-DD') like %s
            """
        else:
            # General cases
            option = psycopg2.sql.Identifier(option)
            searchsql = psycopg2.sql.SQL("""
             SELECT
               to_char(vtimestamp,'YYYY-MM-DD'), study,
               vtype, vscore, age, notes, dvisit, dperson, vid
             FROM
               visit_summary
             where
               pid = %s and {} like %s
             """).format(option)

        return searchsql

    def search(self, pid, table, option, value):
        sql = self.mksearch(option)
        print(option)
        print(sql)
        cur = self.conn.cursor()
        # Differentiate between general case and special case
        if(option == 'vtimestamp'):
            cur.execute(sql, (pid, value))
        else:
            cur.execute(sql,(pid,value))
        data = cur.fetchall()
        return data


def connstr_from_config(config, gui):
    """
    return connection string and user after reading config file
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
    return constr


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


def cur_user(conn):
    """
    get current pgsql database user
    :param conn: connection to query
    """
    cur = conn.cursor()
    cur.execute("select current_user")
    user = cur.fetchone()
    return(user[0])
