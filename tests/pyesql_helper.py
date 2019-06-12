#!/usr/bin/env python
# -*- coding: utf-8 -*-


class pyesql_helper:
    """
    fake cursor structure needed by pyesql
    resolve:
       AttributeError: 'Connection' object has no attribute 'cursor'
    """
    def __init__(self, conn):
        self.connection = conn
        self.results = None

    def execute(self, *kargs):
        ex = self.connection.execute(*kargs)
        self.results = [r for r in ex]
        return(self.results)

    def fetchall(self):
        return(self.results)

    def cursor(self):
        return(self)


def check_column(col, res, expect, exact=True):
    for x in res:
        assert x[col] in expect
    if exact:
        assert len(res) == len(expect)
