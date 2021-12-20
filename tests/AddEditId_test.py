import AddEditId
from lncdSql import lncdSql
from pyesql_helper import pyesql_helper as ph

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys

APP = QApplication(sys.argv)


def test_addid(create_db, qtbot):
    """test that fullnames gets to addperson when buttons clicked"""

    sql = lncdSql(config=None, conn=ph(create_db.connection))
    # win = AddEditId.AddEditApp(sql=sql)
    win = AddEditId.AddEditIdWindow(sql=sql, pid="1")
    assert not win.new_button.isEnabled()

    # need a new idtype that wont already be in the fake DB
    win.new_etype.addItems(["TESTID"])
    win.new_etype.setCurrentText("TESTID")

    win.new_id.setText("9999")

    assert win.new_button.isEnabled()

    qtbot.mouseClick(win.new_button, Qt.LeftButton)

    new_lunaid = create_db.connection.execute(
        """select id from enroll
         where pid = 1 and etype = 'TESTID'"""
    ).fetchall()
    assert new_lunaid[0][0] == "9999"
