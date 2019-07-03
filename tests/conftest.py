import pytest
# see also
# https://stackoverflow.com/questions/46005796/reuse-pytest-fixtures
# https://docs.pytest.org/en/2.7.3/plugins.html

# # no config.ini, no working database
# # ignore files that depend on a working database
# collect_ignore = []
# import os.path
# if not os.path.isfile('config.ini'):
#     collect_ignore.append('tests/test_db_update.py')


# fake database
@pytest.fixture
def create_db(transacted_postgresql_db):
    """
    creates db when used as param in any 'test_fucntion'
    returns transacted_postgresql_db so it doesn't also have to be included
    expects `sql/` directory to be available
    """
    # add lncd user
    transacted_postgresql_db.run_sql_file('sql/07_update_roles.sql')
    # create tables
    transacted_postgresql_db.run_sql_file('sql/03_mkschema.sql')
    # create views
    transacted_postgresql_db.run_sql_file('sql/05_triggers.sql')
    return(transacted_postgresql_db)


@pytest.fixture
def lncdapp(create_db):
    """
    creates db when used as param in any 'test_fucntion'
    returns transacted_postgresql_db so it doesn't also have to be included
    expects `sql/` directory to be available
    """
    from schedule import ScheduleApp
    from pyesql_helper import pyesql_helper as ph
    win = ScheduleApp(sql_obj=ph(create_db.connection), cal_obj='Not Used')
    win.pgtest = create_db
    return win
