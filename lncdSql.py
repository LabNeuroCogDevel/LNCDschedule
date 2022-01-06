import psycopg2
import psycopg2.sql
import psycopg2.extras
import pyesql
import re  # just for censoring password
import sqlalchemy as sqla
from sqlalchemy.dialects.postgresql import JSON
from LNCDutils import db_config_to_dict, make_connstr


class lncdSql:
    """database interface for lncddb"""

    def __init__(self, config, gui=None, conn=None):
        """
        :param config: file used to configure connection
        :param gui: pointer to QtApp. used for password prompt
        :param conn: connection to use instead of config (for testing)
        """

        # can only have one master QT app pointer
        # so record it in the class (or None/False if not using it)
        self.engine = None
        if conn is not None:
            self.conn = conn
            # is testing
            if hasattr(conn, "connection"):
                self.conn = conn
                self.engine = conn.connection
        elif config is not None:
            self.config = db_config_to_dict(config, gui)
            constr = make_connstr(self.config)
            print(
                "connecting: "
                + re.sub("password=[^\\s]+", "password=*censored*", constr)
            )
            self.conn = psycopg2.connect(constr)
            self.conn.set_session(autocommit=True)
        else:
            raise Exception("Bad arguments! need config or conn")

        # define database user
        self.db_user = cur_user(self.conn)

        # deal with sql alchemy
        if self.engine is None:
            self.engine = sqla.create_engine(
                "postgresql+psycopg2://", creator=lambda: self.conn
            )
        self.sqlmeta = sqla.MetaData(self.engine)

        # load up predefine sql queries
        sqls = pyesql.parse_file("./queries.sql")
        self.query = sqls(self.conn)

        # try connection permissions if we are using e.g. config.ini
        #  (otherwise we are probably in a test and dont want this check)
        # query will error if user not given permission
        # see sql/04_add-RAs.sql
        self.config = config
        if config:
            print("testing db connection")
            # TODO: why do we need to rethrow error for it to stop the gui?!
            try:
                self.query.get_lunaid_from_pid(pid=1)
            except Exception as err:
                print("error! %s" % err)
                raise Exception("No permissions on db: %s" % err)

    # function meant to add data to dropped_visit
    # def removal_insert(self, data):
    # Add the vid input to the dropped_visit table
    # sql = "INSERT INTO dropped_visit (vid) VALUES (%d)"
    # val = (data)
    # self.engine.execute(sql, val)

    def getTable(self, table_name):
        """sqlaclhemy table. autogenerated from engine"""
        # probably inefficent to generate the table every time!
        # maybe add to dict
        # N.B. for testing w/pytest-pgsql + transacted + pyesql-helper
        # engine might be somewhere else
        fix_columns = ()
        if table_name == "visit_summary":
            fix_columns = (sqla.Column("notes", JSON(none_as_null=True)),)

        tbl = sqla.Table(
            table_name,
            self.sqlmeta,
            *fix_columns,
            extend_existing=True,
            autoload=True,
            autoload_with=self.engine
        )
        return tbl

    def insert(self, table_name, data):
        """convience function to insert data into a table"""
        print("insert: %s values %s" % (table_name, data))
        tbl = self.getTable(table_name)
        ins = tbl.insert(data)
        self.engine.execute(ins)
        return True

    def update(self, table_name, new_column, id_value, new_value, id_column):
        """
        update a table with given data
        N.B should change new_* to dict to support >1 column at a time
        :param table_name: table to update
        :param new_value: new value to use
        :param id_value: value of id to look up
        :param new_column: column where value will change
        :param id_column: column that stores row identifier
        used like
          'contact',data['ctype'], data['cid'], data['changes'], "cid"
          'person',data['ctype'], data['pid'], data['changes'], "pid"
        """
        print("update: %s %s=%s " % (table_name, new_column, new_value))

        tbl = self.getTable(table_name)
        # build sql
        update_sql = (
            tbl.update()
            .where(getattr(tbl.c, id_column) == id_value)
            .values({new_column: new_value})
        )
        # execute it
        self.engine.execute(update_sql)

    def update_columns(self, table_name, id_column, id_value, update_dict):
        """
        update a table with given data. use a dictionary for many values
        :param table_name: table to update
        :param new_value: new value to use
        :param id_value: value of id to look up
        :param update_dict: {'column': 'new_value', ...}
        """
        print("update: %s %s=%s " % (table_name, id_value, update_dict))

        tbl = self.getTable(table_name)
        # build sql
        update_sql = (
            tbl.update()
            .where(getattr(tbl.c, id_column) == id_value)
            .values(update_dict)
        )
        # execute it
        self.engine.execute(update_sql)

    def remove_visit(self, vid):
        """remove visit by pid
        :param vid: visit id to remove (integer)
        """
        sqlstr = "delete from visit where vid = %d" % int(vid)
        cur = self.conn.cursor()
        cur.execute(sqlstr)
        cur.close()

    def mksearch(self, option):
        # Special casew for vtimestamp b/c
        # date is formatted differently from the database
        if option == "vtimestamp":
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
            searchsql = psycopg2.sql.SQL(
                """
             SELECT
               to_char(vtimestamp,'YYYY-MM-DD'), study,
               vtype, vscore, age, notes, dvisit, dperson, vid
             FROM
               visit_summary
             where
               pid = %s and {} like %s
             """
            ).format(option)

        return searchsql

    def search(self, pid, table, option, value):
        sql = self.mksearch(option)
        print("search\n\toption: %s" % option)
        print("\tsql: %s" % sql)
        cur = self.conn.cursor()
        # Differentiate between general case and special case
        if option == "vtimestamp":
            cur.execute(sql, (pid, value))
        else:
            cur.execute(sql, (pid, value))
        data = cur.fetchall()
        return data

    def dict_cur(self):
        "wrap psychopg2.extra.DictCursor factory with quick function"
        return self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def all_pid_enrolls(self, pid: int):
        dict_cur = self.dict_cur()
        dict_cur.execute("select eid, etype, id from enroll where pid = %s", pid)
        res = dict_cur.fetchall()
        # need to_dict only for tests. dict_cur should be enough
        return to_dict(res, ["eid", "etype", "id"])


def to_dict(res, keys):
    """array of arrays to array of dicts a la DictCursor.
    Initially for tests where dictCursor is not supported
    """
    if type(res) == dict:
        return res
    return [dict(zip(keys, r)) for r in res]


def cur_user(conn):
    """
    get current pgsql database user
    :param conn: connection to query
    """
    cur = conn.cursor()
    cur.execute("select current_user")
    user = cur.fetchone()
    return user[0]
