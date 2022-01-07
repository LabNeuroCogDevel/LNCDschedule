from lncdSql import lncdSql
from pyesql_helper import pyesql_helper as ph


def test_all_pid_enrolls(create_db):
    """test that fullnames gets to addperson when buttons clicked"""
    sql = lncdSql(config=None, conn=ph(create_db.connection))
    new_lunaid = create_db.connection.execute(
        """insert into enroll (pid,etype,id) values (1,'TESTID','1')"""
    )
    res = sql.all_pid_enrolls(1)
    assert "TESTID" in [x["etype"] for x in res]
