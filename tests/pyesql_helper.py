#!/usr/bin/env python
# -*- coding: utf-8 -*-


class pyesql_helper:
    """
    fake cursor structure needed by pyesql
    resolve:
       AttributeError: 'Connection' object has no attribute 'cursor'

    conn.execute() ≡ conn.cursor().execute() ≈ conn.fetchall()

    pyesql and pytest-pgsql execute pattern is different
    pyesql:       conn.cursor().execute(); conn.fetchall()
    pytest-pgsql: conn.execute()
    """
    def __init__(self, conn):
        self.connection = conn
        self.results = None

    def execute(self, *kargs):
        """
        make list of SQL query results (*kargs: query string)
        return list and store to return with `fetchall()`
        """
        ex = self.connection.execute(*kargs)
        self.results = [r for r in ex]
        return(self.results)

    def fetchall(self):
        """
        return the work of execute for pattern:
           conn.execute(); res=conn.fetchall()
        """
        return(self.results)

    def fetchone(self):
        """
        return the work of execute for pattern:
           conn.execute(); res=conn.fetchall()
        """
        return(self.results[0])

    def cursor(self):
        """
        Rathern than implement a fake conn that uses a fake cursor,
           cursor() returns a refernce to the class itself
        so all the needed methods are in this one class: pyesql_helper
        """
        return(self)


def check_column(col, res, expect, exact=True):
    """
    column `col` of sql results `res` are in the expected list `expect`
    order is not tested, only membership
    :param col: column number (0-idx based) to check
    :param res: conn.execute() results
    :param expect: list of expected values
    :param exact: if false res can contain values not in expect
    :raises AssertionError: when res[:][col] != expect
    example:
      res = conn.execute('select ra from ra')
      check_column(0,res,['ra1','ra2'])
    """
    for x in res:
        assert x[col] in expect
    if exact:
        assert len(res) == len(expect)


def csv_none(pg, csv_source, table):
    """
    load csv like pgtest.load_csv
    but import empty strings as None
    :param pg: likely lncdapp.pgtest (transacted_postgresql_db fixture obj)
    :param csv_source: where data is stored
    :param table: fake db table name to put the data in
    """
    import csv
    table_obj = pg.get_table(table)
    with open(csv_source, 'r') as fdesc:
        data_rows = list(csv.DictReader(fdesc, dialect='excel'))
    # make empty string None
    data_rows = [
        {key: None if row[key] == '' else row[key] for key in row}
        for row in data_rows
    ]
    pg._conn.execute(table_obj.insert().values(data_rows))

