import sys
import pytest
import PasswordDialog
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtCore import Qt, QTimer

# initialize QT
APP = QApplication(sys.argv)


def test_password_dialog():
    """can we load up password dialog"""
    w = PasswordDialog.PasswordDialog(APP)
    w.input_user.setText("a_user")
    w.input_password.setText("the_pass")
    assert w.user_pass["user"] == "a_user"
    assert w.user_pass["pass"] == "the_pass"


def test_password_dialog_preset():
    """password dialog can be given a username?"""
    w = PasswordDialog.PasswordDialog(APP, "b_user")
    w.input_user.setText("b_user")
    assert w.user_pass["user"] == "b_user"
    assert w.user_pass["pass"] is None


@pytest.mark.skip("not sure how to avoid non-breaking wait for enter")
def test_user_pass(qtbot):
    """test the blocking function"""
    win = QWidget()
    QTimer.singleShot(200, lambda *kargs: qtbot.keyClick(win, Qt.Key_Enter, delay=100))
    PasswordDialog.user_pass(win, "b_user")
