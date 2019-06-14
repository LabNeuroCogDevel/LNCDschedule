# see also
# https://stackoverflow.com/questions/46005796/reuse-pytest-fixtures
# https://docs.pytest.org/en/2.7.3/plugins.html
import pytest


@pytest.fixture
def create_db(transacted_postgresql_db):
    """
    creates db when used as param in any 'test_fucntion'
    returns transacted_postgresql_db so it doesn't also have to be included
    expects `sql/` directory to be available
    """
    transacted_postgresql_db.run_sql_file('sql/03_mkschema.sql')
    return(transacted_postgresql_db)
