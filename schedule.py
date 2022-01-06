#!/usr/bin/env python3
import sys
import datetime
import re  # for whoami
import psycopg2
from PyQt5 import uic, QtCore, QtGui, QtWidgets
from LNCDcal import LNCDcal
from googleapiclient.errors import HttpError

# local files
from lncdSql import lncdSql
import EditNotes
import MultiRA
import AddNotes
import AddContact
import AddStudy
import AddRA
import AddTask
import AddVisitType
import EditContact
import ScheduleVisit
import CheckinVisit
import MoreInfo
import VisitsCards
import AddContactNotes
import PersonTable  # need by uic import of promoted widget

# local tools
from LNCDutils import (
    mkmsg,
    generic_fill_table,
    CMenuItem,
    update_gcal,
    get_info_for_cal,
    caltodate,
    comboval,
    ScheduleFrom,
    catch_to_mkmsg,
    sqlUpdateOrShowErr,
)


# google reports UTC, we are EST or EDT. get the diff between google and us
# TODO: not used, remove or reconsider usage?
# '%s' doesn't work on windows
# LAUNCHTIME = int(datetime.datetime.now().strftime('%s'))
# TZFROMUTC = datetime.datetime.fromtimestamp(LAUNCHTIME) - \
#     datetime.datetime.utcfromtimestamp(LAUNCHTIME)


class ScheduleApp(QtWidgets.QMainWindow):
    """
    Qt Application class for running main window
    """

    def __init__(self, config_file="config.ini", sql_obj=None, cal_obj=None):
        """
        initialize application
        :param config_file: contains calendar and postgres settings
        :param sql_obj: lncdSql object (for testing). if None, created f/config
        :param cal_obj: LNCDcal object (for testing). if None, created f/config
        """
        super().__init__()
        # Defined for editing the contact_table
        self.contact_cid = 0
        # Defined for editing the visit table
        self.visit_id = 0
        # schedule and checkin data
        self.schedule_what_data = {
            "fullname": "",
            "pid": None,
            "date": None,
            "time": None,
            "lunaid": None,
            "whichCntr": None,
        }
        self.checkin_what_data = {
            "fullname": "",
            "vid": None,
            "datetime": None,
            "pid": None,
            "vtype": None,
            "study": None,
            "lunaid": None,
            "next_luna": None,
        }
        self.visit_table_data = None

        # load gui (created with qtcreator)
        uic.loadUi("./ui/mainwindow.ui", self)
        self.setWindowTitle("LNCD Scheduler")

        # data store
        self.disp_model = {
            "pid": None,
            "fullname": None,
            "age": None,
            "sex": None,
            "lunaid": None,
        }

        # get other modules for querying db and calendar
        try:
            print("initializing outside world: Calendar and DB")

            # setup calendar
            if cal_obj:
                self.cal = cal_obj
            else:
                self.cal = LNCDcal(config_file)

            # setup database
            if sql_obj:
                self.sql = lncdSql(None, conn=sql_obj)
            else:
                self.sql = lncdSql(config_file, gui=QtWidgets.QApplication.instance())

        except psycopg2.ProgrammingError as err:
            mkmsg("ERROR: DB permission issue!\n%s" % str(err))
        except Exception as err:
            mkmsg("ERROR: cannot load calendar or DB!\n%s" % str(err))
            return

        # this is sketchy
        # use table widget defined in PersonTable (called PromotedPersonTable in ui file)
        self.PromotedPersonTable.embed(self.sql)

        # ## who is using the app?
        self.RA = self.sql.db_user
        print("RA: %s" % self.RA)

        # AddStudies modal (accessed from menu)
        self.AddStudy = AddStudy.AddStudyWindow(self)
        self.AddStudy.accepted.connect(self.add_study_to_db)
        self.AddRA = AddRA.AddRAWindow(self)
        self.AddRA.accepted.connect(self.add_ra_to_db)
        self.AddTask = AddTask.AddTaskWindow(self)
        self.AddTask.accepted.connect(self.add_task_to_db)
        self.AddVisitType = AddVisitType.AddVisitTypeWindow(self)
        self.AddVisitType.accepted.connect(self.add_visit_type_to_db)

        # ## menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu("&New")
        CMenuItem("RA", fileMenu, self.AddRA.show)
        CMenuItem("Study", fileMenu, self.AddStudy.show)
        CMenuItem("Task", fileMenu, self.AddTask.show)
        CMenuItem("Visit Type", fileMenu, self.add_visit_type)
        # add Drops removed, All LunaIDs Only, Without LunaIDs
        self.PromotedPersonTable.setup_search_menu_opts(menubar)

        # Visit_table search settings
        visitsSearchMenu = menubar.addMenu("&Visit_table Search")
        CMenuItem("option", visitsSearchMenu, self.visit_table_queries)

        # ## setup person search field
        # ## people_table ##
        self.PromotedPersonTable.person_changed.connect(self.people_row_seleted)

        # ## cal_table ##
        # setup search calendar "cal_table"
        self.cal_columns = ["date", "time", "what"]
        self.cal_table.setColumnCount(len(self.cal_columns))
        self.cal_table.setHorizontalHeaderLabels(self.cal_columns)
        # Adjust the cal table width
        header = self.cal_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.cal_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cal_table.itemSelectionChanged.connect(self.cal_item_select)
        # and hook up the calendar date select widget to a query

        # for the sake of running tests. only run calendar query if need to
        if type(self.cal) is LNCDcal:
            self.calendarWidget.selectionChanged.connect(self.search_cal_by_date)
            self.search_cal_by_date()  # update for current day
            # TODO: eventually want to use DB instead of calendar. need to update
            # backend!

        # ## note table ##
        self.note_columns = ["note", "dropcode", "ndate", "vtimestamp", "ra", "vid"]
        self.note_table_data = None
        self.note_table.setColumnCount(len(self.note_columns))
        self.note_table.setHorizontalHeaderLabels(self.note_columns)
        # Make the note_table uneditable
        self.note_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        self.note_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.note_table.customContextMenuRequested.connect(
            lambda pos: note_menu.exec_(self.note_table.mapToGlobal(pos))
        )

        # ## visit table ##
        self.visit_columns = [
            "day",
            "study",
            "vstatus",
            "vtype",
            "vscore",
            "age",
            "notes",
            "dvisit",
            "dperson",
            "vid",
        ]
        self.visit_table.setColumnCount(len(self.visit_columns))
        self.visit_table.setHorizontalHeaderLabels(self.visit_columns)
        # Make the visit table uneditable
        self.visit_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        # changes to make when selected visit changes
        self.visit_table.itemSelectionChanged.connect(self.visit_item_select)

        # ## context menu + sub-menu for visits: adding RAs
        visit_menu = QtWidgets.QMenu("visit_menu", self.visit_table)
        # Option to delete the schedule
        CMenuItem("Delete", visit_menu, self.delete_visit)

        CMenuItem("no show", visit_menu)
        # Jump to reschedule visit function whenever the reschdule button is
        # clicked.
        CMenuItem("reschedule", visit_menu, self.reschedule_visit)
        # Option to add multiple RAs
        CMenuItem("Multiple RA", visit_menu, self.assignmul_RA)

        self.MultiRA = MultiRA.ChosenMultipleRAWindow(self)
        # self.MultiRA.button.clicked.connect(self.multira_to_db)
        self.MultiRA.buttonBox.accepted.connect(self.multira_to_db)
        # When the bottonbox is cancel
        self.MultiRA.buttonBox.rejected.connect(self.turn_off)

        # find all RAs and add to context menu
        assignRA = visit_menu.addMenu("&Assign RA")

        # ra in this for loop can be implemented in the multiRA implementation
        for ra in self.sql.query.list_ras():
            CMenuItem(ra[0], assignRA, lambda x, ra_=ra[0]: self.updateVisitRA(ra_))

        self.visit_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.visit_table.customContextMenuRequested.connect(
            lambda pos: visit_menu.exec_(self.visit_table.mapToGlobal(pos))
        )

        # contact table
        contact_columns = ["who", "cvalue", "relation", "status", "added", "cid"]
        self.contact_table.setColumnCount(len(contact_columns))
        self.contact_table.setHorizontalHeaderLabels(contact_columns)
        # Make the contact_table uneditable
        self.contact_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        # schedule time widget
        self.timeEdit.timeChanged.connect(self.render_schedule)

        # ## add ContactNotes
        self.AddContactNotes = AddContactNotes.AddContactNotesWindow(self)

        # ## add contact ##
        self.AddContact = AddContact.AddContactWindow(self)
        # autocomple stuffs
        self.AddContact.add_ctypes([r[0] for r in self.sql.query.list_ctype()])
        self.AddContact.suggest_relation([r[0] for r in self.sql.query.list_relation()])
        # connect it up
        self.add_contact_button.clicked.connect(self.add_contact_pushed)
        self.AddContact.accepted.connect(self.add_contact_to_db)

        # Call to edit the contact table whenver the item is clicked
        self.contact_table.itemSelectionChanged.connect(self.edit_contact_table)

        # Menu bar for contact table
        contact_menu = QtWidgets.QMenu("contact_menu", self.contact_table)
        CMenuItem("Edit Contact", contact_menu, lambda: self.edit_contact_pushed())
        # Jump to reschedule visit function whenever the reschdule button is
        # clicked.
        CMenuItem("Record Contact", contact_menu, lambda: self.record_contact_push())
        self.contact_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contact_table.customContextMenuRequested.connect(
            lambda pos: contact_menu.exec_(self.contact_table.mapToGlobal(pos))
        )

        # Edit contact
        self.EditContact = EditContact.EditContactWindow(self)
        # add the vid value into the interface
        self.visit_table.itemSelectionChanged.connect(self.edit_visit_table)

        self.VisitsCards = VisitsCards.VisitsCardsWindow(self)

        # Query the database when the wild cards has been selected and entered
        self.VisitsCards.accepted.connect(self.visits_from_database)

        self.MoreInfo = MoreInfo.MoreInfoWindow(self)
        self.visit_info_button.clicked.connect(self.more_information_pushed)
        # Change the wrong cvalue if needed.
        # Must make sure it's clicked
        # self.edit_contact_button.clicked.connect(self.edit_contact_pushed)
        self.EditContact.accepted.connect(self.update_contact_to_db)

        # ## add notes ##
        # and query for pid from visit_summary
        self.AddNotes = AddNotes.AddNoteWindow(self)

        self.EditNotes = EditNotes.EditNotesWindow(self)
        # Do the autocomplete later
        self.add_notes_button.clicked.connect(self.add_notes_pushed)
        self.AddNotes.accepted.connect(self.add_notes_to_db)

        self.note_table.itemSelectionChanged.connect(self.note_item_select)

        self.MultiRA.accepted.connect(self.multira_to_db)

        self.EditNotes.accepted.connect(self.edit_notes_to_db)
        # Menu bar for note table
        note_menu = QtWidgets.QMenu("note_menu", self.note_table)
        CMenuItem("Edit_notes", note_menu, lambda: self.edit_note_pushed())

        # ## add visit ##
        #
        # # schedule #
        # init
        study_list = [r[0] for r in self.sql.query.list_studies()]
        self.ScheduleVisit = ScheduleVisit.ScheduleVisitWindow(self)
        self.ScheduleVisit.add_studies(study_list)
        self.ScheduleVisit.add_vtypes([r[0] for r in self.sql.query.list_vtypes()])

        # wire up button, disable by default
        self.schedule_button.setDisabled(True)
        self.schedule_button.clicked.connect(self.schedule_button_pushed)
        self.ScheduleVisit.accepted.connect(self.schedule_to_db)

        # ## checkin
        # init
        self.CheckinVisit = CheckinVisit.CheckinVisitWindow(self)
        all_tasks = self.sql.query.all_tasks()
        self.CheckinVisit.set_all_tasks(all_tasks)
        # wire
        self.checkin_button.clicked.connect(self.checkin_button_pushed)
        self.CheckinVisit.accepted.connect(self.checkin_to_db)

        self.show()

    # #### GENERIC ####
    def add_study_to_db(self):
        study_data = self.AddStudy.study_data
        self.sql.insert("study", study_data)
        print("adding studies: %s" % study_data)

    def add_ra_to_db(self):
        ra_data = self.AddRA.ra_data
        self.sql.insert("ra", ra_data)
        print("adding ra: %s" % ra_data)
        # for this RA to access the database they need to be added as a user

    def add_task_to_db(self):

        # Make sure the dictionaries that are added to the db are not empty or partially-full
        if self.AddTask.add_optional_bool:
            self.AddTask.task_data["settings"] = self.AddTask.temp_settings
        if self.AddTask.file_dict:
            self.AddTask.task_data["files"] = self.AddTask.file_dict

        task_data = self.AddTask.task_data
        self.sql.insert("task", task_data)
        print("adding task: %s" % task_data)

    def add_visit_type(self):
        self.AddVisitType.show()

    def add_visit_type_to_db(self):
        visit_type_data = self.AddVisitType.visit_type_data
        self.sql.insert("visit", visit_type_data)
        print("adding visit type" % visit_type_data)

    # check with isvalid method
    # used for ScheduleVisit and AddContact
    def useisvalid(self, obj, msgdesc):
        check = obj.isvalid()
        if not check["valid"]:
            mkmsg("%s: %s" % (msgdesc, check["msg"]))
            return False
        return True

    # #### PEOPLE #####

    """
    connector for on text change of fullname textline search bar
    """

    def note_item_select(self):
        row_i = self.note_table.currentRow()
        # Color row when clicked -- indicate action target for right click
        self.click_color(self.note_table, row_i)

    def dropcode_coloring(self):
        """Coloring anyrow with the dropcode that doesn't equal to None"""
        for i in range(self.note_table.rowCount()):
            dropcode = self.note_table.item(i, 1).text()
            if not dropcode or dropcode == "None":
                continue
            print("coloring drop '%s'" % dropcode)
            for j in range(self.note_table.columnCount()):
                self.note_table.item(i, j).setBackground(QtGui.QColor(250, 231, 163))

    def people_row_seleted(self, row):
        "what to do with signal from PersonTable. row is dict"
        # main model
        print("people table: subject selected: %s" % row["pid"])
        self.render_person(
            pid=row["pid"],
            fullname=row["fullname"],
            age=row["age"],
            sex=row["sex"],
            lunaid=row["lunaid"],
        )
        self.render_schedule(ScheduleFrom.PERSON)

    def render_person(self, pid, fullname, age, sex, lunaid=None):
        """
        how to populate all the subject info
        """
        self.disp_model["pid"] = pid
        self.disp_model["fullname"] = fullname
        self.disp_model["age"] = age
        self.disp_model["sex"] = sex
        self.disp_model["lunaid"] = lunaid

        # fname is all but the last name in fullname
        names = fullname.split(" ")
        self.disp_model["fname"] = " ".join(names[0:-1])
        self.disp_model["lname"] = names[-1]

        # try to get a pid if we are calling from a place that doesn't have it
        if lunaid is None:
            res = self.sql.query.get_lunaid_from_pid(pid=pid)
            if res:
                lunaid = res[0][0]

        # update visit table
        self.update_visit_table()
        # update contact table
        self.update_contact_table()
        # update notes
        self.update_note_table()
        self.render_schedule(ScheduleFrom.PERSON)
        # TODO:
        # do we want to clear other models
        #  clear: checkin_what_data schedule_what_data

    def visit_table_queries(self):
        # print('testing testing')
        self.VisitsCards.show()

    def visit_item_select(self, thing=None):
        # Enable the button in the first place
        self.checkin_button.setEnabled(True)

        row_i = self.visit_table.currentRow()
        if row_i == -1:
            print("DEBUG: visit_item_select but row_i is -1")
            return

        d = self.visit_table_data[row_i]
        try:
            vid = d[self.visit_columns.index("vid")]
        except IndexError:
            print("visit_item_select: tuple index out of range")

        study = d[self.visit_columns.index("study")]
        pid = self.disp_model["pid"]
        fullname = self.disp_model["fullname"]

        # for j in range(self.visit_table.columnCount()):
        # self.visit_table.item(row_i, j).setBackground(QtGui.QColor(182, 236, 48))
        self.click_color(self.visit_table, row_i)

        self.checkin_what_data["pid"] = pid
        self.checkin_what_data["fullname"] = fullname
        try:
            self.checkin_what_data["vid"] = vid
        except UnboundLocalError:
            print("visit_item_select: local variable vid referenced before assignment")
        self.checkin_what_data["study"] = study
        self.checkin_what_data["vtype"] = d[self.visit_columns.index("vtype")]
        self.checkin_what_data["datetime"] = d[self.visit_columns.index("day")]

        # as long as disp model matches visit (when wouldn't it?)
        # use lunaid from person table
        # Disable the checkin button when the subject is checkedin
        if d[self.visit_columns.index("vstatus")] == "checkedin":
            self.checkin_button.setEnabled(False)
        self.render_schedule(ScheduleFrom.VISIT)

    # Function to show more informations in checkin
    def more_information_pushed(self):
        row_i = self.visit_table.currentRow()
        if self.visit_table.item(row_i, 9) is not None:
            vid = self.visit_table.item(row_i, 9).text()
        else:
            return
        self.MoreInfo.setup(vid, self.sql)
        self.MoreInfo.show()

    def delete_visit(self):
        row_i = self.visit_table.currentRow()
        if row_i == -1:
            print("DEBUG: reschedule visit but no visit selected!")
            return

        vid_i = self.visit_columns.index("vid")
        vid = self.visit_table.item(row_i, vid_i).text()

        # Process to search for and remove google url
        uri = self.sql.query.get_googleuri(vid=vid)
        uri = uri[0][0]
        # Move the event from calendar
        self.cal.move_event(uri)

        # self.sql.removal_insert(vid)
        try:
            self.sql.query.remove_visit(vid=vid)
        except psycopg2.ProgrammingError:
            print("trivial error")
            print("Remove successfully")
        except psycopg2.InternalError:
            mkmsg(
                "Cannot remove visit %s b/c status is not sched or have enrolled or have tasks"
                % vid
            )

        # finally update visit table
        self.update_visit_table()
        # mkmsg('still implementing')
        # print(vid)

    def reschedule_visit(self):
        """
        reschedule button click or right click visit item -> reschedule
        1. check reschedule is reasonable
        2. get old vid
        3. push to normal schedule
        """
        # get what we clicked on
        row_i = self.visit_table.currentRow()
        if row_i == -1:
            print("DEBUG: reschedule visit but no visit selected!")
            return

        status_i = self.visit_columns.index("vstatus")
        vstatus = self.visit_table.item(row_i, status_i).text()
        if vstatus not in ["sched", "resched", "assigned"]:
            mkmsg("Can only reschedule '(re)sched/assigned', not " + vstatus)
            return

        # TODO: stop from rescheduling something in the distant past?
        # shouldn't be an issue, but db pull has sched where it shouldnt

        # get old info. we will remove this after successful rescheduleing
        vid_i = self.visit_columns.index("vid")
        vid = self.visit_table.item(row_i, vid_i).text()

        # create a new visit first
        # successful ScheduleVisit modal removes googleuri using schedule_to_db
        self.schedule_button_pushed(vid)

        # finally update visit table
        self.update_visit_table()

    # Change color of the row whenever do leftclick
    def click_color(self, table, row_i):
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                if i == row_i:
                    try:
                        table.item(i, j).setBackground(QtGui.QColor(191, 243, 228))
                    except AttributeError:
                        print("Affordable to ignore")
                    continue
                if table is self.note_table:
                    try:
                        self.note_table_background(table, i, j)
                    except AttributeError:
                        print("click color: bad i j (%d,%d@%s)" % (i, j, table))
                else:
                    try:
                        table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))
                    except AttributeError:
                        print("Affordable to ignore")
        # Get rid of the color in other tables
        if table == self.note_table:
            self.refresh_blank(self.contact_table)
            # self.refresh_blank(self.people_table)
            self.refresh_blank(self.visit_table)

        if table == self.visit_table:
            self.refresh_blank(self.contact_table)
            # self.refresh_blank(self.people_table)
            self.refresh_blank(self.note_table)

        elif table == self.contact_table:
            self.refresh_blank(self.visit_table)
            # self.refresh_blank(self.people_table)
            self.refresh_blank(self.note_table)

        # elif table == self.people_table:
        #    self.refresh_blank(self.visit_table)
        #    self.refresh_blank(self.contact_table)
        #    self.refresh_blank(self.note_table)

    def note_table_background(self, table, i, j):
        if table.item(i, 1).text() != "None":
            self.note_table.item(i, j).setBackground(QtGui.QColor(250, 231, 163))
        elif table.item(i, 1).text() == "None":
            table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

    def table_background(self, table, i, j):

        if table.item(i, 6).text() == "subject":
            color = QtGui.QColor(249, 179, 139)
            table.item(i, j).setBackground(color)
        elif table.item(i, 6).text() == "visit":
            color = QtGui.QColor(240, 230, 140)
            table.item(i, j).setBackground(color)
        elif table.item(i, 6).text() == "future":
            color = QtGui.QColor(240, 240, 240)
            table.item(i, j).setBackground(color)
        elif (
            table.item(i, 6).text() == "family" or table.item(i, 6).text() == "unknown"
        ):
            color = QtGui.QColor(203, 233, 109)
            table.item(i, j).setBackground(color)
        else:
            table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

    def refresh_blank(self, table):
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

    # Function to simplt turn off the window and do nothing
    def turn_off(self):

        self.MultiRA.close()

    def multira_to_db(self):
        # get the list  of all the ra chosen
        RA_selection = self.MultiRA.get_data()

        # First clear all the assigned ra to avoid overlap
        row_i = self.visit_table.currentRow()
        d = self.visit_table_data[row_i]
        vid = d[self.visit_columns.index("vid")]

        # do not assign a checked in visit
        vstatus = d[self.visit_columns.index("vstatus")]
        if vstatus == "checkedin":
            mkmsg("Cannot reassign a checked in visit!")
        else:
            self.multira_to_db_operaiton(RA_selection, vid)

        # Always remember to clear the list
        RA_selection.clear()  # TODO: why -- does this clear the gui too?
        self.MultiRA.close()

    def multira_to_db_operaiton(self, RA_selection, vid):
        # Warning!!!!!! Remove the previous asigned RA that is in the database
        # Remove RA
        try:
            self.sql.query.remove_RA(vid=vid)
        except:
            print("Failed to rm assigned RAs from vid %d, probably okay" % vid)

        # Get the current uri
        visitcal = self.sql.query.get_googleuri(vid=vid)
        print(visitcal)
        if not visitcal:
            mkmsg("Cannot find google uri for vid %s" % str(vid))
            return None
        # List to add in RA abbreviation
        RA_abbr = []
        # Assign the new multi_RA to visit_action
        for ra in RA_selection:
            # ra = self.sql.query.get_abbr(ra=ra)[0][0]
            # print(ra)
            # print(vid)
            new_node = {"ra": ra, "action": "assigned", "vid": vid}
            self.sql.insert("visit_action", new_node)
            this_ra_abbr = self.sql.query.get_abbr(ra=ra)
            if not this_ra_abbr:
                mkmsg('No RA matching "%s". Not adding to vid %d!' % (ra, vid))
            else:
                RA_abbr.append(this_ra_abbr[0][0])

        # Transform the RA_abbr list to a string
        RA_abbr = ",".join(RA_abbr)
        print(RA_abbr)

        # Get the big info of that visit from the calendar
        info = get_info_for_cal(self.sql.query, vid)
        if visitcal is None:
            mkmsg("Cannot find google uri for vid %d" % vid)
            return None
        print(visitcal)

        # print(info)
        info["calid"] = visitcal[0][0]
        # Change the info['RA'] to the joined RA
        info["ra"] = RA_abbr

        try:
            # self.cal.delete_event(info['googleuri'])
            event = update_gcal(self.cal, info, assign=True)
        except Exception as err:
            mkmsg("update error! %s" % err)
            return

        # Update the event(e) in the database
        try:
            self.sql.query.update_uri(googleuri=event["id"], vid=vid)
        except psycopg2.ProgrammingError as err:
            print("updateVisitRA sql err: %s" % err)

        # Store the data into database

        # Return vid for the testing
        return vid

    def assignmul_RA(self):
        # Create a list to store all the ras
        ra_list = []
        # mkmsg('Implementing')
        self.MultiRA.show()
        # Loop thorugh the RAs and append them to the list
        for ra in self.sql.query.list_ras():
            ra_list.append(ra[0])
        self.MultiRA.setup(ra_list)

        ra_choices = self.MultiRA.get_data()

        print(ra_choices)

    def updateVisitRA(self, ra):
        """add or change visit RA assignment"""
        row_i = self.visit_table.currentRow()
        d = self.visit_table_data[row_i]
        vid = d[self.visit_columns.index("vid")]

        # do not assign a checked in visit
        vstatus = d[self.visit_columns.index("vstatus")]
        if vstatus == "checkedin":
            mkmsg("Cannot reassign a checked in visit!")
            return

        # pid = self.disp_model['pid']
        info = get_info_for_cal(self.sql.query, vid)
        # Update the database for RA
        info["ra"] = self.sql.query.get_abbr(ra=ra)[0][0]
        try:
            self.sql.query.update_RA(ra=info["ra"], vid=vid)
        except psycopg2.ProgrammingError as err:
            print("updateVisitRA: bad sql? %s" % err)

        print("updateVisitRA: %s" % info)
        #  1. update google calendar title
        info["googleuri"] = self.sql.query.get_googleuri(vid=vid)
        info["googleuri"] = info["googleuri"][0][0]
        # TODO: calid is not googleuri!?
        info["calid"] = info["googleuri"]

        try:
            # self.cal.delete_event(info['googleuri'])
            event = update_gcal(self.cal, info, assign=True)
        except Exception as err:
            mkmsg("update error! %s" % err)
            return
        # Update the event(e) in the database
        try:
            self.sql.query.update_uri(googleuri=event["id"], vid=vid)
        except psycopg2.ProgrammingError as err:
            print("updateVisitRA sql err: %s" % err)

        # For this, sched is origionally assigned. Changed it to sche so that the data base will  accept the vstatus.
        # //////////////////////////////////////////////
        new_node = {"ra": ra, "action": "assigned", "vid": vid}
        # //////////////////////////////////////////////
        #  2. add to visit_action # vatimestamp? auto inserted?
        self.sql.insert("visit_action", new_node)
        #  3. update visit
        # TODO/FIXME: is this done elsewhere?  20190615WF
        # self.sql.update('visit', 'googleuri', event['id'], 'vid', vid)
        #  4. refresh visit view
        self.update_visit_table()

    def edit_visit_table(self):
        """on item click: set visit as subject for actions"""
        row_i = self.visit_table.currentRow()
        if row_i == -1:
            print("DEBUG: row=-1 in edit_visit_table, cannot set visit_id!")
            return
        self.visit_id = self.visit_table.item(row_i, 9).text()
        self.name = self.visit_table.item(row_i, 0).text()

    def edit_note_pushed(self):
        # Parse the data to the editnote
        # Get the vid
        row_i = self.note_table.currentRow()
        self.vid = self.note_table.item(row_i, 5).text()
        # Data as default value
        self.data = {"Note": None, "Dropcode": None, "Date": None}
        self.data["note"] = self.note_table.item(row_i, 0).text()
        self.data["dropcode"] = self.note_table.item(row_i, 1).text()
        self.data["ndate"] = self.note_table.item(row_i, 2).text().split(" ")[0]

        # Do we need to care about the case when the vid is None?
        self.EditNotes.set_up(self.vid, self.data)
        self.EditNotes.show()

    def edit_notes_to_db(self):
        data = self.EditNotes.edit_model
        sqlUpdateOrShowErr(
            self.sql, "note", data["ctype"], data["vid"], data["changes"], "vid"
        )
        self.update_note_table()

    def update_visit_table(self):
        """update visit table display"""
        pid = self.disp_model["pid"]
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        print("update_visit_table table data\n\t%s" % self.visit_table_data)
        generic_fill_table(self.visit_table, self.visit_table_data)

    def update_contact_table(self):
        """update contact table display"""
        self.contact_table_data = self.sql.query.contact_by_pid(
            pid=self.disp_model["pid"]
        )
        generic_fill_table(self.contact_table, self.contact_table_data)

    def update_note_table(self):
        """update note table display"""
        # pid=self.disp_model['pid']
        print("update_note_table pid: %s" % self.disp_model["pid"])
        self.note_table_data = self.sql.query.note_by_pid(pid=self.disp_model["pid"])
        generic_fill_table(self.note_table, self.note_table_data)

    # #### SCHEDULE #####

    def render_schedule(self, schedule_from=None):
        """
        handle setting up scheduling middle area
        """
        # print('render schedule: %s' % self.schedule_what_data)
        # only changes when we click on a different table
        if schedule_from:
            self.schedule_what_data["whichCntr"] = schedule_from

        # update schedule text
        self.schedule_what_data["pid"] = self.disp_model["pid"]
        self.schedule_what_data["fullname"] = self.disp_model["fullname"]
        self.schedule_what_data["lunaid"] = self.disp_model["lunaid"]
        self.schedule_what_data["date"] = caltodate(self.calendarWidget)
        # Labels
        # def update_schedule_what_label(self):
        # def update_checkin_what_label(self):
        # def update_checkin_time(self):
        text = "%(fullname)s (%(lunaid)s): %(date)s@%(time)s" % self.schedule_what_data
        self.schedule_what_label.setText(text)

        time = self.timeEdit.dateTime().time().toPyTime()
        if time:
            self.schedule_what_data["time"] = time

        # when we have a time and a person, enable schedule button
        if (
            self.schedule_what_data["pid"]
            and self.schedule_what_data["time"]
            and self.schedule_what_data["date"]
        ):
            self.schedule_button.setDisabled(False)

        # is the button for scheduling or rescheduling
        if self.schedule_what_data["whichCntr"] == ScheduleFrom.VISIT:
            self.schedule_button.setText("Reschedule")
            self.schedule_button.clicked.connect(self.reschedule_visit)
            # TODO: fetching vstatus happens twice. make function?
            row_i = self.visit_table.currentRow()
            status_i = self.visit_columns.index("vstatus")
            vstatus = self.visit_table.item(row_i, status_i).text()
            # if vstatus is not sched -- no reschedule
            if vstatus != "sched":
                self.schedule_button.setDisabled(True)
        else:
            self.schedule_button.setText("Schedule")
            self.schedule_button.clicked.connect(self.schedule_button_pushed)

        # TODO: indicate schedule_from
        #  with e.g. an arrow icon
        # print('render schedule: %s' % self.schedule_what_data)

    # #### VISIT #####
    # see generic_fill_table
    def schedule_button_pushed(self, vid=None):
        """
        grab widget values and pop up a scheduler
        if popup dialog is okay, add to db
        """
        d = self.schedule_what_data["date"]
        t = self.schedule_what_data["time"]
        # Got the pid ID for the person who scheduled.
        pid = self.disp_model["pid"]
        fullname = self.disp_model["fullname"]
        if d is None or t is None:
            mkmsg("set a date and time before scheduling")
            return ()
        if pid is None or fullname is None:
            mkmsg("select a person before trying to schedule")
            return ()

        dt = datetime.datetime.combine(d, t)

        googleuri = None
        if vid:
            googleuri = self.sql.query.get_googleuri(vid=vid)
            if not googleuri:
                mkmsg("No google uri for vid %d" % vid)
                return
            googleuri = googleuri[0][0]

        self.ScheduleVisit.setup(pid, fullname, self.RA, dt, googleuri, vid)
        self.ScheduleVisit.show()

    def schedule_to_db(self, refresh_model=True):
        """after successfully filling out ScheduleVisit
        can be first or reschedule: depeonds on vid/old_googleuri
        :param refresh_model: should we use the gui to update the model
          1. create new calendar (or error)
          2. insert/update       (or error and remove new cal)
          3. move old calendar id to backup id (or warn)
        """
        # valid? has side effect of putting gui widget values to model
        # dont do that if we are testing (refresh_model=False)
        if refresh_model and not self.useisvalid(
            self.ScheduleVisit, "Cannot schedule visit"
        ):
            return

        # make the note index None so that the sql can recongnize it.

        # if we have LNCDcal -- use it to insert a googleuri
        # we don't upload credentials, so not avaiable during travis CI tests
        old_googleuri = None
        new_googleuri = None
        vid = self.ScheduleVisit.vid
        have_cal = isinstance(self.cal, LNCDcal)
        if have_cal:
            print("add to cal\n\tdisp: %s" % self.disp_model)
            print("\twhat: %s" % self.schedule_what_data)
            print("\tmodel: %s" % self.ScheduleVisit.model)
            print("\told uri: %s" % self.ScheduleVisit.old_googleuri)
            try:
                # can be None if not new
                old_googleuri = self.ScheduleVisit.old_googleuri
                # -> model['googleuri'], will go into db same as rest of model
                new_googleuri = self.ScheduleVisit.add_to_calendar(
                    self.cal, self.disp_model
                )
            except Exception as err:
                mkmsg("Failed to add to google calendar; not adding. %s" % str(err))
                return

        # set status: have vid -> reschedule (update)
        # no vid -> schedule (insert)
        if vid:
            print(
                "updating visit (%s) and rm'ing old uri (%s) from calendar"
                % (vid, old_googleuri)
            )
            self.ScheduleVisit.model["action"] = "resched"
            added = catch_to_mkmsg(
                self.sql.update_columns,
                "visit_summary",
                "vid",
                vid,
                self.ScheduleVisit.model,
            )
        else:
            self.ScheduleVisit.model["action"] = "sched"
            added = self.sqlInsertOrShowErr("visit_summary", self.ScheduleVisit.model)

        # db insert error checking
        if not added and have_cal:
            print("removing new gcalevent %s" % self.ScheduleVisit.model["googleuri"])
            self.cal.delete_event(new_googleuri)
            return

        # # check if old is still around (TOOD: add find_googleuri to queries)
        # if self.queries.find_googleuri(uri=old_googleuri):
        #     mkmsg('Still have old calendar event referenced in DB!')

        if old_googleuri and have_cal:
            try:
                # TODO: change to move_event
                self.cal.move_event(old_googleuri)

            except HttpError as httperr:
                mkmsg(
                    "Google event not deleted!"
                    + "Do it yourself? (calid: %s, err: %s)" % (old_googleuri, httperr)
                )

        # need to refresh visits
        self.update_visit_table()
        self.update_note_table()

    def visits_from_database(self):
        """Method that queries the database for the specific visits"""
        self.visit_table_data = self.VisitsCards.setup(self.disp_model["pid"], self.sql)
        # Upload the data to the table
        self.visit_table.setRowCount(len(self.visit_table_data))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i, row in enumerate(self.visit_table_data):
            for col_i, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.visit_table.setItem(row_i, col_i, item)

    def record_contact_push(self):
        """Method for record push --Waiting for later implementation"""
        self.AddContactNotes.show()
        # Find the cid from the table
        row_i = self.contact_table.currentRow()
        cid = self.contact_table.item(row_i, 5).text()
        # Pass in cid to the user intrface
        self.AddContactNotes.set_contact_notes(cid)

    # ## checkin
    def checkin_button_pushed(self):
        pid = self.checkin_what_data["pid"]
        # vid = self.checkin_what_data['vid']
        fullname = self.checkin_what_data["fullname"]
        study = self.checkin_what_data["study"]
        vtype = self.checkin_what_data["vtype"]
        if study is None or vtype is None:
            mkmsg("pick a visit with a study and visit type")
            return ()
        if pid is None or fullname is None:
            mkmsg("select a person before trying to checkin (howd you get here?)")
            return ()

        # que up a new lunaid
        # N.B. we never undo this, but check is always for lunaid first
        if self.checkin_what_data.get("lunaid") is None:

            print(
                "have no luna in checkin data! getting next:\n\t%s"
                % self.checkin_what_data
            )
            nextluna_res = self.sql.query.next_luna()
            nxln = nextluna_res[0][0]
            self.checkin_what_data["next_luna"] = nxln + 1
            print("next luna is %d" % self.checkin_what_data["next_luna"])

        # (self,pid,name,RA,study,study_tasks)
        study_tasks = [
            x[0]
            for x in self.sql.query.list_tasks_of_study_vtype(study=study, vtype=vtype)
        ]
        print(
            "checkin: launching %(fullname)s for %(study)s/%(vtype)s"
            % self.checkin_what_data
        )
        # checkin_what_data sends: pid,vid,fullname,study,vtype
        self.CheckinVisit.setup(self.checkin_what_data, self.RA, study_tasks)
        self.CheckinVisit.show()

    def checkin_to_db(self):
        """
        wrap CheckinVisit's own checkin_to_db to add error msg and refresh visits
        """
        try:
            self.update_visit_table()
        except Exception as err:
            mkmsg("checkin failed!\n%s" % err)
        self.CheckinVisit.checkin_to_db(self.sql)
        # todo: update person search to get lunaid if updated
        # Update the visit table so that the current vastatus changed to
        # checkedin
        self.update_visit_table()

    # #### NOTES ####
    # see generic_fill_table

    # ### CALENDAR ###

    def search_cal_by_date(self):
        # selectedQdate=self.calendarWidget.selectedDate().toPyDate()
        # dt=datetime.datetime.fromordinal( selectedQdate.toordinal() )
        dt = caltodate(self.calendarWidget)
        print("cal search update date: %s" % dt)
        # update calendar table
        # now=datetime.datetime.now()
        delta = datetime.timedelta(days=5)
        dmin = dt - delta
        dmax = dt + delta
        res = self.cal.find_in_range(dmin, dmax)
        # This res contains all the data for the week within
        self.fill_calendar_table(res)
        # update checking (with current selected date)
        self.render_schedule()
        # Read the table information after its filled
        self.ra_calendar_count()

    def ra_calendar_count(self):
        """
        count number visits each RA has
        that are on display in the calendar table
        """
        # Define the list
        names = {}
        # which column contains the description
        j = self.cal_columns.index("what")
        # Loop Through the table to find people that were assigned.
        for i in range(self.cal_table.rowCount()):
            if "--" in self.cal_table.item(i, j).text():
                # Split the name form the events
                name = self.cal_table.item(i, j).text().split("--")[1]
                # Now check the multi_RA case
                # If the ra is splited by comma
                if "," in name:
                    # Split the list first
                    name = name.split(",")
                    for RA_names in name:
                        # Fix the format
                        RA_names = " " + RA_names
                        names[RA_names] = names.get(RA_names, 0) + 1

                else:
                    # add 1 to the count
                    names[name] = names.get(name, 0) + 1

        # Alternative  -- use database
        #  res = self.sql.query.visits_this_week(startdate, enddate)
        #  for r in res:
        #    name = r[3]
        #    names[name] = names.get(name, 0) + 1

        # combine names and counts into one long string
        results = ", ".join(["%s: %d" % (n, names[n]) for n in sorted(names.keys())])
        # update label
        self.ra_information_label.setText(results)

    def fill_calendar_table(self, calres):
        """
        update calendar table with calres
        :param calres: is list of dict with keys
          'summary', 'note', 'calid', 'starttime', 'creator', 'dur_hr', 'start'
        * fill the calendar table with goolge calendar items from search result
        * separate time into date and time of day, add summary
        """
        self.cal_table_data = calres
        self.cal_table.setRowCount(len(calres))
        for row_i, calevent in enumerate(calres):
            # google uses UTC, but we are in EST or EDT
            # st   = str(calevent['starttime'] + TZFROMUTC)
            # st=str(calevent['starttime'])
            m_d = calevent["starttime"].strftime("%Y-%m-%d")
            tm = calevent["starttime"].strftime("%H:%M")
            self.cal_table.setItem(row_i, 0, QtWidgets.QTableWidgetItem(m_d))
            self.cal_table.setItem(row_i, 1, QtWidgets.QTableWidgetItem(tm))
            eventname = calevent["summary"]
            self.cal_table.setItem(row_i, 2, QtWidgets.QTableWidgetItem(eventname))

    def cal_item_select(self):
        """
        when we hit an item in the calendar table, update
         * potential checkin data and label
         * potental schedual data and srings
        to get person:
         - search database for calendar id
         - if that fails try to search based on title
        """
        # First enable the button no matter what
        self.checkin_button.setEnabled(True)
        row_i = self.cal_table.currentRow()
        if row_i > len(self.cal_table_data):
            mkmsg("Undiagnosed error: cal row clicked > table data!")
            return
        try:
            # googleuri should be in database
            cal_id = self.cal_table_data[row_i].get("calid", None)
            if cal_id is None:
                print("Cal event does not have an id!? How?")
                return
        except IndexError:
            print("the calid cannot be gotten from the list")
            return
        try:
            res = self.sql.query.visit_by_uri(googleuri=cal_id)
        except UnboundLocalError:
            # There is no calid existed in the list
            mkmsg("calid does not exit")
            return
        if res:
            print("cal item select: %s" % res)
            pid = res[0][0]
        else:
            print("WARNING: cannot find eid %s in db! Search title" % cal_id)
            pid = self.find_pid_by_cal_desc(row_i)

        # cant do anything if we dont have a pid
        if pid is None:
            return

        # update gui to to person
        self.checkin_from_cal(pid)
        self.render_person_pid(pid)
        self.fullname.setText(self.disp_model["fullname"])
        # let schedule know we came from the calendar
        self.render_schedule(ScheduleFrom.CAL)

    def find_pid_by_cal_desc(self, row_i):
        """
        Find a pid by the calendar title
        :return: pid
        """
        # Find if -- is in the string, if it is, then them this even is
        # assigned RA.

        cal_desc = self.cal_table.item(row_i, 2).text()
        print("find by cal cal_desc %s" % cal_desc)
        current_date = self.cal_table.item(row_i, 0).text()
        current_time = self.cal_table.item(row_i, 1).text()
        current_date_time = current_date + " " + current_time + ":00"
        current_study = self.cal_table.item(row_i, 2).text().split("/")[0]
        # 7T x1 EEG-23yof (EG) - MB, LT
        title_regex = re.match(r"(\w+)/(\w+) x(\d+) (\d+)yo(\w)", cal_desc)
        if not title_regex:
            mkmsg(
                "cannot parse calendar event title!\n"
                + "expect 'study/type xX YYyo[m/f]' but have\n"
                + cal_desc
            )
            return None

        current_age = title_regex.group(4)
        current_gender = title_regex.group(5)

        if current_age is None:
            print("No current age in google cal event title!")
            return None

        res = self.sql.query.get_pid_of_visit(
            vtimestamp=current_date_time, study=current_study, age=int(current_age)
        )

        # Debuging, see results
        print("cal find by pid: %s" % res)

        if not res:
            return None

        pid = res[0][0]
        return pid

    def checkin_from_cal(self, pid):
        """
        set checkin model to match item clicked on calendar
        requires taht we found a DB pid to match the google event
        """
        row_i = self.cal_table.currentRow()
        self.scheduled_date = self.cal_table.item(row_i, 0).text()
        print("cal checkin\n\tdate: %s" % self.scheduled_date)
        try:
            self.checkin_status = self.sql.query.get_status(
                pid=pid, vtimestamp=self.scheduled_date
            )[0][0]
        except IndexError:
            print("The object might not be existed in some cases")

        print("\tstatus: %s" % self.checkin_status)

        if self.checkin_status == "checkedin":
            self.checkin_button.setEnabled(False)

    # ### CONTACTS ###
    # self.add_contact_button.clicked.connect(self.add_contact_pushed)

    def add_contact_pushed(self):
        """show add modal when button is pushed"""
        # self.AddContact.setpersondata(d)
        self.AddContact.set_contact(self.disp_model["pid"], self.disp_model["fullname"])
        self.AddContact.show()

    def edit_contact_pushed(self):
        """show edit modal when button is pushed"""
        # row_i = self.contact_table.currentRow()
        self.EditContact.edit_contact(self.contact_cid, self.contact_table)
        self.EditContact.show()

    def update_contact_to_db(self):
        """run sql update and refresh contact table"""
        data = self.EditContact.edit_model
        sqlUpdateOrShowErr(
            self.sql, "contact", data["ctype"], data["cid"], data["changes"], "cid"
        )
        self.update_contact_table()

    # self.AddContact.accepted.connect(self.add_contact_to_db)
    def add_contact_to_db(self):
        """run sql add and update table"""
        # do we have good input?
        if not self.useisvalid(self.AddContact, "Cannot add contact"):
            return

        # catch sql error
        data = self.AddContact.contact_model
        data["added"] = datetime.datetime.now()
        # The contact is referring to the table in debeaver.
        self.sqlInsertOrShowErr("contact", data)
        self.update_contact_table()

    def edit_contact_table(self):
        """on row click: update what contact is used for actions"""
        row_i = self.contact_table.currentRow()
        if row_i < 0:
            print("DEBUG: neg row index in edit_contact_table")
            return

        self.click_color(self.contact_table, row_i)
        try:
            self.contact_cid = self.contact_table.item(row_i, 5).text()
            self.name = self.contact_table.item(row_i, 0).text()
        except AttributeError:
            print("edit contact: attribute error setting row %d" % row_i)

    # ## Notes
    def add_notes_pushed(self):
        """on clikc run add notes modal"""
        # self.Addnotes.setpersondata(d)
        self.AddNotes.set_note(
            self.disp_model["pid"], self.disp_model["fullname"], self.sql.query
        )
        # dropbox full of possible visits
        self.AddNotes.show()

    def add_notes_to_db(self):
        # Error check
        if not self.useisvalid(self.AddNotes, "Cannot add note"):
            return
        # add ra to model
        data = {**self.AddNotes.notes_model, "ra": self.RA}

        # look at drop code and vid
        # both could be None
        dropcode = self.AddNotes.get_drop()
        vid = self.AddNotes.get_vid()
        # insert into note
        note_dict = {**data, "vid": vid, "dropcode": self.AddNotes.get_drop()}
        self.sqlInsertOrShowErr("note", note_dict)

        # whatever we've done, we need to update the view
        self.update_note_table()

        # Refresh the people_table
        self.PromotedPersonTable.search_people_by_name()

    def sqlInsertOrShowErr(self, table, d):
        """
        @param table - table to inser to
        @param d - data to insert
        @return True/False if inserted
        @sideffect - gui message if error
        """
        # TODO: test
        # return catch_to_mkmsg(self.sql.insert, d)
        try:
            # self.sql.query.insert_person(**(self.AddPerson.persondata))
            # print('insering into %s: %s' % (table, d)) # sql.insert does this
            self.sql.insert(table, d)
            return True
        except Exception as err:
            mkmsg(str(err))
            return False


# actually launch everything
if __name__ == "__main__":
    # paths relative to where files are
    import os

    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    APP = QtWidgets.QApplication([])

    if len(sys.argv) > 1:
        WINDOW = ScheduleApp(config_file=sys.argv[1])
    else:
        WINDOW = ScheduleApp()

    sys.exit(APP.exec_())
