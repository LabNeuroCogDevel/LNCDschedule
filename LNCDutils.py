# import calendar
import datetime
from enum import Enum
import configparser
from PyQt5 import QtWidgets
import PasswordDialog


class ScheduleFrom(Enum):
    """enumerate where schedule data came from
    could use str, but this gives pseudo type check
    """

    PERSON = 1
    VISIT = 2
    CAL = 3


# get combobox value
def comboval(cb):
    return cb.itemText(cb.currentIndex())


# get date from qdate widge
def caltodate(qdate_widget):
    ordinal = qdate_widget.selectedDate().toPyDate().toordinal()
    dt = datetime.datetime.fromordinal(ordinal)
    return dt


# used in is_valid. does key match string or all
def isOrAll(k, s):
    return k in [s, "all"]


# used for visit, contact, notes, and all_tasks_table in checkin
def generic_fill_table(table, res):
    table.setRowCount(len(res))
    for row_i, row in enumerate(res):
        for col_i, value in enumerate(row):
            item = QtWidgets.QTableWidgetItem(str(value))
            table.setItem(row_i, col_i, item)


def mkmsg(msg, icon=QtWidgets.QMessageBox.Critical):
    """
    dialog box to send an error or warning message
    """
    # persistent to this function so not eaten by GC
    if not hasattr(mkmsg, "win"):
        mkmsg.win = QtWidgets.QMessageBox()
    mkmsg.win.setIcon(icon)
    mkmsg.win.setText(msg)
    print("mkmsg: " + msg)
    mkmsg.win.show()


def CMenuItem(
    text, widget, action=lambda: mkmsg("Not Implemented yet"), checkable=False
):
    """
    generic to add a context menu item
    """
    a = QtWidgets.QAction(text, widget, checkable=checkable)
    if action is not None:
        a.triggered.connect(action)
    widget.addAction(a)
    return a


# ## calendar
def make_calendar_event(cal, info, assign=False):
    """
    give a dictionary with all the visit info, get back a google event
    study, vtype, visitno, age, sex, initials, dur_hr, vtimestamp, notes, ra
    """
    info["initials"] = "".join(map(lambda x: x[0], info["fullname"].split()))

    # prefer values in model over person dict
    info["createwhen"] = datetime.datetime.now()
    print(info["vtimestamp"])
    print("++++++++++++++++++++++++++++++++++")
    # (datetime.datetime.now() - dob).total_seconds()/(60*60*24*365.25)
    title = "%(study)s/%(vtype)s"
    title += " x%(visitno)d %(age).0fyo%(sex)s (%(initials)s)"
    if assign:
        title += " -- %(ra)s"
    # format
    title = title % info
    # description
    desc = "%(notes)s\n-- %(ra)s on %(createwhen)s" % info
    # from e.g. "Thu Oct 26 14:00:00 2017" to datetime object
    startdt = datetime.datetime.strptime(
        str(info["vtimestamp"]), "%a %b %d %H:%M:%S %Y"
    )
    event = cal.insert_event(startdt, info["dur_hr"], title, desc)
    return event


def get_info_for_cal(query, vid):
    """
    get info we need to update a calender event on google
    using visit id and visit_summary in db
    """
    res = query.cal_info_by_vid(vid=vid)
    if res is None:
        mkmsg("Error finding vid %d" % vid)
        return ()
    headers = [
        "study",
        "vtype",
        "visitno",
        "age",
        "sex",
        "fullname",
        "dur_hr",
        "vtimestamp",
        "notes",
        "ra",
        "id",
    ]
    info = dict(zip(headers, res[0]))
    return info


def update_gcal(cal, info, assign=False):
    """
    update google calendar event:
       delete and create anew to replace/update
       a visit in the db on google calendar
       using dictionary (see get_info_for_cal, then make some changes)
    """
    if isinstance(cal, str) or not cal:
        print('ASSUME TESTING! calendar object is "%s"' % cal)
        return info

    print("updating gcal with %s" % info)
    cal.delete_event(info["calid"])
    # change from yyyy-mm-dd hh:mm to  mon ....
    info["vtimestamp"] = info["vtimestamp"].strftime("%a %b %d %H:%M:%S %Y")
    event = make_calendar_event(cal, info, assign)
    return event


# ## DATABASE
def catch_to_mkmsg(func, *kargs):
    """generic wrapper to send excpetions to mkmsg"""
    try:
        func(*kargs)
        return True
    except Exception as err:
        mkmsg(str(err))
        return False


def db_config_to_dict(config, gui=None):
    """
    @param config  dictionary or str path to config file
    @param gui     QtWidgets.QApplication.instance() to prompt for user/pass
    @return dictionary with db config
    read config.ini file like
      [SQL]
       host=...
       dbname=...
       ..
    """
    # TODO: move to utils? does not depend on "self"
    if isinstance(config, dict):
        dbsettings = config
    else:
        cfg = configparser.ConfigParser()
        cfg.read(config)
        dbsettings = cfg._sections.get("SQL")
        if dbsettings is None:
            raise Exception("%s does not have SQL section!" % config)

    # if the config doesn't have a username, we will try to get one
    if not dbsettings.get("user"):
        if gui is None or gui is False:
            raise Exception(
                "No username in config file" + "and no gui to authenticate requested!"
            )
        user_pass = PasswordDialog.user_pass(gui)
        dbsettings["user"] = user_pass["user"]
        dbsettings["password"] = user_pass["pass"]
    return dbsettings


def make_connstr(config_dict):
    """
    @param config_dict dictionary containing dbname, user, host
                       and maybe port and password
    @return connection string and user after reading config file
    """
    # only set password if its not empty
    # otherise we can continue without using a password... maybe
    confline = "dbname=%(dbname)s user=%(user)s host=%(host)s"

    # if we specify a port or password, use it
    if config_dict.get("port"):
        confline += " port=%(port)s"
    if config_dict.get("password"):
        confline += " password=%(password)s"

    constr = confline % config_dict
    return constr


def connstr_from_config(config, gui=None):
    """
    @param config  see db_config_to_dict. str path or dict
    @param gui     see db_config_to_dict. QtWidgets.QApplication.instance()
    @return connection string and user after reading config file
    """
    config_dict = db_config_to_dict(config, gui)
    return make_connstr(config_dict)
