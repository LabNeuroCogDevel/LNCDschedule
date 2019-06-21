#!/usr/bin/env python3
from PyQt5.QtWidgets import QApplication, QWidget,\
       QPushButton, QGridLayout, QLabel, QLineEdit
import subprocess

# https://build-system.fman.io/pyqt5-tutorial


def user_pass(app=None):
    """ prompt for username and password """
    if app is None:
        app = QApplication([])
    window = QWidget()
    # mutable object, passed by reference
    # acts as data model
    user_pass = {'user': None, 'pass': None}

    # items we need to track: user, pass, login
    input_user = QLineEdit()
    input_password = QLineEdit()
    input_password.setEchoMode(QLineEdit.Password)
    login_button = QPushButton('LogIn')

    # enter on password or user submits
    input_password.returnPressed.connect(lambda: closedown(app))
    input_user.returnPressed.connect(lambda: closedown(app))

    # setup user pass
    def update_value(v, idx, user_pass_ref):
        user_pass_ref[idx] = v

    def closedown(app):
        app.quit()

    # setup callbacks
    # wire up user_pass model to gui
    input_user.textChanged.\
        connect(lambda x: update_value(x, 'user', user_pass))
    input_password.textChanged.\
        connect(lambda x: update_value(x, 'pass', user_pass))
    login_button.clicked.connect(lambda x: closedown(app))

    # set default username based on system
    # called after connecting text change so closes in both places
    username = subprocess.check_output("whoami").decode().\
        replace('\n', '').replace('\r', '').\
        replace('1upmc-acct\\', '')  # remove domain on win pc
    input_user.setText(username)

    # define layout
    layout = QGridLayout()
    layout.addWidget(QLabel('User:'), 0, 0)
    layout.addWidget(input_user, 0, 1)

    layout.addWidget(QLabel('Password:'), 1, 0)
    layout.addWidget(input_password, 1, 1)

    layout.addWidget(login_button, 2, 0)
    window.setLayout(layout)

    # show
    window.show()
    # focus password -- username is probably already set
    input_password.setFocus()
    # run
    app.exec_()
    return(user_pass)


# for debugging -- quickly show dialog
if __name__ == "__main__":
    upcase = user_pass()
    print(upcase)
