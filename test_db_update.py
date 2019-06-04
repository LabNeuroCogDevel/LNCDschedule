#!/usr/bin/env python
# -*- coding: utf-8 -*-
# test functions in lncdSql.py

import lncdSql
from datetime import datetime

# connect to our database
sql = lncdSql.lncdSql('config.ini')
# make temp table for testing
cur = sql.conn.cursor()
cur.execute("create temp table test_table(id int, time timestamp)")


# test that insert works
def test_insert():
    now = datetime.now()
    sql.insert("test_table", {"id": 1, "time": now})

    cur = sql.conn.cursor()
    cur.execute("select * from test_table where id = 1")
    r = cur.fetchall()
    assert len(r) == 1
    assert r[0][1] == now


# test that update works
def test_update():
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
