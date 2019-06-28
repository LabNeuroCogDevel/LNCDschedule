#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test functions in lncdSql.py

from datetime import datetime
import pytest
import lncdSql
from pyesql_helper import pyesql_helper as ph


@pytest.fixture
def sql(transacted_postgresql_db):
    # connect to our database
    lsql = lncdSql.lncdSql(config=None,
                           conn=ph(transacted_postgresql_db.connection))
    # make temp table for testing
    # cur = lsql.conn.cursor()
    # cur.execute("create temp table test_table(id int, time timestamp)")

    # with fake db
    transacted_postgresql_db.\
        connection.execute("create table test_table(id int, time timestamp)")
    return lsql


# test that insert works
def test_insert(sql):
    now = datetime.now()
    # TODO: broke w/fakedb -- ObjectNotExecutableError
    sql.insert("test_table", {"id": 1, "time": now})

    cur = sql.conn.cursor()
    cur.execute("select * from test_table where id = 1")
    r = cur.fetchall()
    assert len(r) == 1
    assert r[0][1] == now


# test that update works
def test_update(sql):
    id_to_update = 10
    # first insert two things - with junk times
    sql.insert("test_table", {"id": id_to_update, "time": datetime(1, 1, 1)})
    sql.insert("test_table", {"id": 20, "time": datetime(2, 2, 2)})
    cur = sql.conn.cursor()

    # run update, and check results
    now = datetime.now()
    sql.update("test_table", "id", id_to_update, "time", now)
    cur.execute("select * from test_table where id = %d" % id_to_update)
    r = cur.fetchall()
    assert len(r) == 1
    assert r[0][1] == now
