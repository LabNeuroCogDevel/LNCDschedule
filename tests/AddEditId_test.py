import AddEditId
from lncdSql import lncdSql
from pyesql_helper import pyesql_helper as ph

import pytest
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
import sys

APP = QApplication(sys.argv)


@pytest.fixture
def win(create_db):
    sql = lncdSql(config=None, conn=ph(create_db.connection))
    # win = AddEditId.AddEditApp(sql=sql)
    win = AddEditId.AddEditIdWindow(sql=sql, pid="1")
    return win


def test_setselect(win, qtbot):
    """test that fullnames gets to addperson when buttons clicked"""
    win.new_etype.addItems(["TESTID"])
    win.new_etype.setCurrentText("TESTID")
    win.new_id.setText("9999")
    assert win.data["ids"]["new"].get("etype") == "TESTID"


def test_edit_existing(win, create_db, qtbot):
    "shouldn't be able to update an old id until value is changed"
    create_db.connection.execute(
        "insert into enroll (eid,pid,etype,id) values (2, 1,'TESTID','test1')"
    )
    win.populate_known_ids()
    # 2 is the eid not necessarily the 2nd entry (though it is also that)
    assert not win.widgets[2]["update"].isEnabled()
    win.widgets[2]["id"].setText("test2")
    assert win.widgets[2]["update"].isEnabled()
    qtbot.mouseClick(win.widgets[2]["update"], Qt.LeftButton)
    edit_id = create_db.connection.execute(
        """select id from enroll
         where pid = 1 and etype = 'TESTID'"""
    ).fetchall()
    print(edit_id)
    assert edit_id[0][0] == "test2"


def test_addid(win, create_db, qtbot):
    """test that fullnames gets to addperson when buttons clicked"""

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
    print(new_lunaid)
    assert new_lunaid[0][0] == "9999"
