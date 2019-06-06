#!/usr/bin/env python3
from PyQt5.QtWidgets import QApplication, QWidget,\
       QPushButton, QGridLayout, QLabel, QLineEdit
import subprocess

# https://build-system.fman.io/pyqt5-tutorial


def user_pass(app=None):
    if app is None:
        app = QApplication([])
    window = QWidget()
    # mutable object, passed by reference
    # acts as data model
    user_pass = {'user': None, 'pass': None}

    # iteams we need to track: user, pass, login
    input_user = QLineEdit()
    input_password = QLineEdit()
    input_password.setEchoMode(QLineEdit.Password)
    login_button = QPushButton('LogIn')

    # setup user pass
    def update_value(v, idx, up):
        up[idx] = v

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
        replace('\n', '').replace('\r', '')
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
    app.exec_()
    return(user_pass)


# for debugging -- quickly show dialog
if __name__ == "__main__":
    up = user_pass()
    print(up)
