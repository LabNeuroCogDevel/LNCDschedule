#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import psycopg2.sql
import sqlalchemy.engine.base
import json


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

    @property
    def __class__(self):
        """get around a check in insert"""
        return sqlalchemy.engine.base.Connection

    def execute(self, *kargs):
        """
        make list of SQL query results (*kargs: query string)
        return list and store to return with `fetchall()`
        """
        if isinstance(kargs[0], psycopg2.sql.Composed):
            print("i'm not going do what you want")

        ex = self.connection.execute(*kargs)

        # TODO/UGLY: trying to iterate over ex fails if insert
        try:
            self.results = [r for r in ex]
        except:
            pass

        return self.results

    def fetchall(self):
        """
        return the work of execute for pattern:
           conn.execute(); res=conn.fetchall()
        """
        return self.results

    def fetchone(self):
        """
        return the work of execute for pattern:
           conn.execute(); res=conn.fetchall()
        """
        if self.results:
            return self.results[0]
        else:
            return None

    def cursor(self):
        """
        Rathern than implement a fake conn that uses a fake cursor,
           cursor() returns a refernce to the class itself
        so all the needed methods are in this one class: pyesql_helper
        """
        return self

    def close(self):
        """do nothing?"""
        return self


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


def note_to_json(key, val):
    """
    encode json if key calls for that (only 'notes' as of 20211129)
    added b/c fake_db.bash uses psql to submit csvs to database
    and requires all columns are present.
    but empty values for json are not handled well by the mocked database
    """
    if key not in ["notes"]:
        return val  # don't care about non-json keys
    return json.loads(val)


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
    with open(csv_source, "r") as fdesc:
        data_rows = csv.DictReader(fdesc, dialect="excel", escapechar="\\")
        data_rows = list(data_rows)
    # make empty string None
    data_rows = [
        {key: None if row[key] == "" else note_to_json(key, row[key]) for key in row}
        for row in data_rows
    ]
    pg._conn.execute(table_obj.insert().values(data_rows))
