from lncdSql import lncdSql
from pyesql_helper import pyesql_helper as ph


def test_getuser(create_db):
    """test that fullnames gets to addperson when buttons clicked"""

    sql = lncdSql(config=None, conn=ph(create_db.connection))
    assert sql.db_user is not None
    # test db user is always postgres
    assert sql.db_user == 'postgres'
