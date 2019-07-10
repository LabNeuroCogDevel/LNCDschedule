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
import AddNotes
import EditPeople
import AddContact
import AddStudy
import EditContact
import ScheduleVisit
import AddPerson
import CheckinVisit
import MoreInfo
import VisitsCards
import AddContactNotes
# local tools
from LNCDutils import (mkmsg, generic_fill_table, CMenuItem,
                       update_gcal, get_info_for_cal,
                       caltodate, comboval, ScheduleFrom)


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
    def __init__(self, config_file='config.ini', sql_obj=None, cal_obj=None):
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
        self.schedule_what_data = {'fullname': '', 'pid': None, 'date': None,
                                   'time': None, 'lunaid': None,
                                   'whichCntr': None}
        self.checkin_what_data = {'fullname': '', 'vid': None,
                                  'datetime': None, 'pid': None,
                                  'vtype': None, 'study': None,
                                  'lunaid': None, 'next_luna': None}

        # load gui (created with qtcreator)
        uic.loadUi('./ui/mainwindow.ui', self)
        self.setWindowTitle('LNCD Scheduler')

        # data store
        self.disp_model = {'pid': None, 'fullname': None,
                           'age': None, 'sex': None,
                           'lunaid': None}

        # get other modules for querying db and calendar
        try:
            print('initializing outside world: Calendar and DB')

            # setup calendar
            if cal_obj:
                self.cal = cal_obj
            else:
                self.cal = LNCDcal(config_file)

            # setup database
            if sql_obj:
                self.sql = lncdSql(None, conn=sql_obj)
            else:
                self.sql = lncdSql(config_file,
                                   gui=QtWidgets.QApplication.instance())

        except psycopg2.ProgrammingError as err:
            mkmsg("ERROR: DB permission issue!\n%s" %
                  str(err))
        except Exception as err:
            mkmsg("ERROR: cannot load calendar or DB!\n%s" %
                  str(err))
            return

        # ## who is using the app?
        self.RA = self.sql.db_user
        print("RA: %s" % self.RA)

        # AddStudies modal (accessed from menu)
        self.AddStudy = AddStudy.AddStudyWindow(self)
        self.AddStudy.accepted.connect(self.add_study_to_db)

        # ## menu
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&New')
        CMenuItem("RA", fileMenu)
        addStudy = CMenuItem("Study", fileMenu, self.add_studies)
        CMenuItem("Task", fileMenu)
        CMenuItem("Visit Type", fileMenu)

        # search settings
        searchMenu = menubar.addMenu('&Search')

        # add items to searchMenu
        def mkbtngrp(text):
            return(CMenuItem(text, searchMenu,
                             lambda x: self.search_people_by_name(), True))

        self.NoDropCheck = mkbtngrp("&Drops removed")
        # set up as exclusive (radio button like)
        lany = mkbtngrp("&All")
        lonly = mkbtngrp("&LunaIDs Only")
        lno = mkbtngrp("&Without LunaIDs")
        # create group
        self.luna_search_settings = QtWidgets.QActionGroup(searchMenu)
        self.luna_search_settings.addAction(lonly)
        self.luna_search_settings.addAction(lno)
        self.luna_search_settings.addAction(lany)
        # add to menu
        searchMenu.addAction(lany)
        searchMenu.addAction(lonly)
        searchMenu.addAction(lno)

        # Visit_table search settings
        visitsSearchMenu = menubar.addMenu('&Visit_table Search')
        CMenuItem("option", visitsSearchMenu, self.visit_table_queries)

        # ## setup person search field
        # by name
        self.fullname.textChanged.connect(self.search_people_by_name)
        self.fullname.setText('')
        self.search_people_by_name(
            self.fullname.text() +
            '%')  # doesnt already happens, why?

        # by lunaid
        self.subjid_search.textChanged.connect(self.search_people_by_id)
        # by attribute
        self.min_age_search.textChanged.connect(self.search_people_by_att)
        self.max_age_search.textChanged.connect(self.search_people_by_att)
        self.sex_search.activated.connect(self.search_people_by_att)
        self.study_search.activated.connect(self.search_people_by_att)

        # ## people_table ##
        #  setup search table "people_table"
        self.person_columns = [
            'fullname', 'lunaid', 'age', 'dob',
            'sex', 'lastvisit', 'maxdrop', 'studies']
        self.people_table.setColumnCount(len(self.person_columns))
        self.people_table.setHorizontalHeaderLabels(self.person_columns)
        self.people_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        # wire up clicks
        self.people_table.itemSelectionChanged.connect(self.people_item_select)
        self.people_table.setContextMenuPolicy(QtCore.Qt.ActionsContextMenu)

        # ## people context menu
        def select_and_note():
            # right click alone wont populate person
            self.people_item_select()
            self.add_notes_pushed()
        CMenuItem("Add Note/Drop", self.people_table, select_and_note)
        CMenuItem("Add ID", self.people_table)
        CMenuItem("Edit Person", self.people_table, self.change_person)
        # same as
        # a = QtWidgets.QAction("Add Id", self.people_table)
        # self.people_table.addAction(a)

        # ## cal_table ##
        # setup search calendar "cal_table"
        self.cal_columns = ['date', 'time', 'what']
        self.cal_table.setColumnCount(len(self.cal_columns))
        self.cal_table.setHorizontalHeaderLabels(self.cal_columns)
        # Adjust the cal table width
        header = self.cal_table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QtWidgets.QHeaderView.ResizeToContents)
        self.cal_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        self.cal_table.itemSelectionChanged.connect(self.cal_item_select)
        # and hook up the calendar date select widget to a query

        # for the sake of running tests. only run calendar query if need to
        if type(self.cal) is LNCDcal:
            self.calendarWidget.selectionChanged.connect(self.search_cal_by_date)
            self.search_cal_by_date()  # update for current day
            # TODO: eventually want to use DB instead of calendar. need to update
            # backend!

        # ## note table ##
        self.note_columns = [
                'note', 'dropcode', 'ndate',
                'vtimestamp', 'ra', 'vid']
        self.note_table_data = None
        self.note_table.setColumnCount(len(self.note_columns))
        self.note_table.setHorizontalHeaderLabels(self.note_columns)
        # Make the note_table uneditable
        self.note_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        self.people_table.itemSelectionChanged.connect(self.dropcode_coloring)

        # ## visit table ##
        self.visit_columns = [
            'day', 'study', 'vstatus', 'vtype', 'vscore',
            'age', 'notes', 'dvisit', 'dperson', 'vid']
        self.visit_table.setColumnCount(len(self.visit_columns))
        self.visit_table.setHorizontalHeaderLabels(self.visit_columns)
        # Make the visit table uneditable
        self.visit_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)
        # changes to make when selected visit changes
        self.visit_table.itemSelectionChanged.connect(self.visit_item_select)

        # ## context menu + sub-menu for visits: adding RAs
        visit_menu = QtWidgets.QMenu("visit_menu", self.visit_table)
        CMenuItem("no show", visit_menu)
        # Jump to reschedule visit function whenever the reschdule button is
        # clicked.
        CMenuItem("reschedule", visit_menu, lambda: self.reschedule_all())
        # find all RAs and add to context menu
        assignRA = visit_menu.addMenu("&Assign RA")
        for ra in self.sql.query.list_ras():
            CMenuItem(ra[0], assignRA,
                      lambda x, ra_=ra[0]: self.updateVisitRA(ra_))
        self.visit_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.visit_table.customContextMenuRequested.connect(
            lambda pos: visit_menu.exec_(self.visit_table.mapToGlobal(pos)))

        # contact table
        contact_columns = ['who', 'cvalue', 'relation',
                           'status', 'added', 'cid']
        self.contact_table.setColumnCount(len(contact_columns))
        self.contact_table.setHorizontalHeaderLabels(contact_columns)
        # Make the contact_table uneditable
        self.contact_table.setEditTriggers(
            QtWidgets.QAbstractItemView.NoEditTriggers)

        # schedule time widget
        self.timeEdit.timeChanged.connect(self.render_schedule)

        # ## general db info ##
        # study list used for checkin and search
        self.study_list = [r[0] for r in self.sql.query.list_studies()]
        # populate search with results
        self.study_search.addItems(self.study_list)

        # Assigning Edit People
        self.EditPeople = EditPeople.EditPeopleWindow(self)
        self.EditPeople.accepted.connect(self.change_person_to_db)
        # ## add person ##
        all_sources = [r[0] for r in self.sql.query.list_sources()]
        self.AddPerson = AddPerson.AddPersonWindow(self, sources=all_sources)
        self.add_person_button.clicked.connect(self.add_person_pushed)
        self.AddPerson.accepted.connect(self.add_person_to_db)

        # ## add ContactNotes
        self.AddContactNotes = AddContactNotes.AddContactNotesWindow(self)

        # ## add contact ##
        self.AddContact = AddContact.AddContactWindow(self)
        # autocomple stuffs
        self.AddContact.add_ctypes([r[0] for r in self.sql.query.list_ctype()])
        self.AddContact.suggest_relation(
            [r[0] for r in self.sql.query.list_relation()])
        # connect it up
        self.add_contact_button.clicked.connect(self.add_contact_pushed)
        self.AddContact.accepted.connect(self.add_contact_to_db)

        # Call to edit the contact table whenver the item is clicked
        self.contact_table.itemSelectionChanged.connect(self.edit_contact_table)

        # Menu bar for contact table
        contact_menu = QtWidgets.QMenu("contact_menu", self.contact_table)
        CMenuItem("Edit Contact", contact_menu,
                  lambda: self.edit_contact_pushed())
        # Jump to reschedule visit function whenever the reschdule button is
        # clicked.
        CMenuItem("Record Contact", contact_menu,
                  lambda: self.record_contact_push())
        self.contact_table.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.contact_table.customContextMenuRequested.connect(
            lambda pos:
                contact_menu.exec_(self.contact_table.mapToGlobal(pos)))

        # Edit contact
        self.EditContact = EditContact.EditContactWindow(self)
        # add the vid value into the interface
        self.visit_table.itemSelectionChanged.connect(self.edit_visit_table)

        self.VisitsCards = VisitsCards.VisitsCardsWindow(self)

        #Query the database when the wild cards has been selected and entered
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
        # Do the autocomplete later
        self.add_notes_button.clicked.connect(self.add_notes_pushed)
        self.AddNotes.accepted.connect(self.add_notes_to_db)
        # connect it up

        # ## add visit ##
        #
        # # schedule #
        # init
        self.ScheduleVisit = ScheduleVisit.ScheduleVisitWindow(self)
        self.ScheduleVisit.add_studies(self.study_list)
        self.ScheduleVisit.add_vtypes(
            [r[0] for r in self.sql.query.list_vtypes()])

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
        self.sql.insert('study', study_data)
        print(study_data)

    def add_studies(self):
        self.AddStudy.show()

    # check with isvalid method
    # used for ScheduleVisit and AddContact
    def useisvalid(self, obj, msgdesc):
        check = obj.isvalid()
        if(not check['valid']):
            mkmsg('%s: %s' % (msgdesc, check['msg']))
            return(False)
        return(True)

    def change_person(self):
        """
        edit person from person_table right click
        use current row info stored in 'disp_model'
        """
        # TODO:
        # if render_person is none: throw error message to click first

        # add dob to render person -- because it has all the other info too
        row_i = self.people_table.currentRow()
        col_i = self.person_columns.index('dob')
        dob = self.people_table.item(row_i, col_i).text()
        self.disp_model['dob'] = dob
        # launch module
        self.EditPeople.edit_person(self.disp_model)
        self.EditPeople.show()

    def change_person_to_db(self):
        """
        submitted edit from edit_person
        send update to db and refresh display
        """
        data = self.EditPeople.edit_model

        # nothign to do if we have NULL combo box item selected
        to_change = data['ctype']
        if not to_change or to_change == 'NULL':
            return

        print("pid %(pid)d: updated %(ctype)s to %(changes)s" % data)

        # run sql
        self.sqlUpdateOrShowErr('person', data['ctype'],
                                data['pid'], data['changes'], "pid")

        # update display -- update any changes to recreate fullname
        # update search based on full name
        self.disp_model[to_change] = data['changes']
        fullname = "%(fname)s %(lname)s" % self.disp_model
        self.update_people_table(fullname)

    # #### PEOPLE #####
    def add_person_pushed(self):
        name = self.fullname.text().title().split(' ')
        print('spliting name at len %d' % len(name))
        fname = name[0] if len(name) >= 1 else ''
        lname = " ".join(name[1:]) if len(name) >= 2 else ''
        d = {'fname': fname, 'lname': lname}
        self.AddPerson.setpersondata(d)
        self.AddPerson.show()

    """
    connector for on text change of fullname textline search bar
    """

    def search_people_by_name(self, fullname=None):
        if fullname is None:
            fullname = self.fullname.text()

        # only update if we've entered 3 or more characters
        # .. but let wildcard (%) go through
        if(len(fullname) < 3 and not re.search('%', fullname)):
            return

        # use maxdrop and lunaid range to add exclusions
        search = {
            'fullname': fullname,
            'maxlunaid': 99999,
            'minlunaid': -1,
            'maxdrop': 'family'}

        # exclude dropped?
        if self.NoDropCheck.isChecked():
            search['maxdrop'] = 'nodrop'

        # luna id status (all/without/only)
        setting = self.luna_search_settings.checkedAction()
        if setting is not None:
            setting = re.sub('&', '', setting.text())
            if re.search('LunaIDs Only', setting):
                search['minlunaid'] = 1
            elif re.search('Without LunaIDs', setting):
                search['maxlunaid'] = 1

        # finally query and update table
        res = self.sql.query.name_search(**search)
        self.fill_search_table(res)

    # seach by id
    def search_people_by_id(self, lunaid):
        if(lunaid == '' or not lunaid.isdigit()):
            mkmsg("LunaID should only be numbers")
            return
        if(len(lunaid) != 5):
            try:
                res = self.sql.query.lunaid_search_all(lunaid=lunaid)
            except ValueError:
                mkmsg("LunaID should only be numbers")
            self.fill_search_table(res)
            return
        try:
            lunaid = int(lunaid)
        except ValueError:
            mkmsg("LunaID should only be numbers")
            return
        res = self.sql.query.lunaid_search(lunaid=lunaid)
        self.fill_search_table(res)

    # by attributes
    def search_people_by_att(self, *argv):
        # Error check
        if(self.max_age_search.text() == '' or
           self.min_age_search.text() == '' or
           not self.max_age_search.text().isdigit() or
           not self.min_age_search.text().isdigit()):
            mkmsg("One of the input on the input box is either " +
                  "empty or not a number, nothing will work. " +
                  "Please fix it and try again")
            return

        d = {'study': comboval(self.study_search),
             'sex': comboval(self.sex_search),
             'minage': self.min_age_search.text(),
             'maxage': self.max_age_search.text()}
        print(d)
        res = self.sql.query.att_search(**d)
        #res = self.sql.query.att_search(sex=d['sex'],study=d['study'], minage=d['minage'],maxage=d['maxage'])
        self.fill_search_table(res)

    def fill_search_table(self, res):
        self.people_table_data = res
        self.people_table.setRowCount(len(res))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i, row in enumerate(res):
            for col_i, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.people_table.setItem(row_i, col_i, item)
        if res:
            self.changing_color(row_i, res)
    def dropcode_coloring(self):
        #Coloring anyrow with the dropcode that doesn't equal to None
        row_i = self.note_table.currentRow
        for i in range(self.note_table.rowCount()):
            for j in range(self.note_table.columnCount()):
                try:
                    print(self.note_table.itemAt(0,1)).text()
                except AttributeError:
                    print('it is None')
                    return

                self.note_table.item(row_i, j).setBackground(QtGui.QColor(250, 231, 163))

    def changing_color(self, row_i, res):
        """
        Change the color after the textes have been successfully inserted.
        based on drop level
        """
        # drop_j = self.person_columns.index('maxdrop')
        drop_j = 6
        drop_colors = {'subject': QtGui.QColor(249, 179, 139),
                       'visit': QtGui.QColor(240, 230, 140),
                       'future': QtGui.QColor(240, 240, 240),
                       'unknown': QtGui.QColor(203, 233, 109)}

        # N.B. this could go in previous for loop. left here for clarity
        for row_i, row in enumerate(res):
            droplevel = row[drop_j]
            # don't do anything if we don't have a color for this drop level
            if droplevel is None or droplevel == 'nodrop':
                continue
            drop_color = drop_colors.get(droplevel, drop_colors['unknown'])
            # go through each column of the row and color it
            for j in range(self.people_table.columnCount()):
                self.people_table.item(row_i, j).setBackground(drop_color)

    def people_item_select(self, thing=None):
        """
        when person row is selected, update the person model
        """
        # Whenever the people table subjects have been selected
        #  grey out the checkin button
        self.checkin_button.setEnabled(False)
        row_i = self.people_table.currentRow()
        # Color row when clicked -- indicate action target for right click
        self.click_color(self.people_table, row_i)

        if(row_i == -1):
            print("BUG: row_i is -1 -- nothing selected")
            return
        d = self.people_table_data[row_i]
        # main model
        print('people table: subject selected: %s' % d[8])
        self.render_person(pid=d[8], fullname=d[0], age=d[2],
                           sex=d[4], lunaid=d[1])
        self.render_schedule(ScheduleFrom.PERSON)

    def render_person_pid(self, pid):
        """
        update person model using only a pid
        """
        res = self.sql.query.person_by_pid(pid=pid)
        if res is None:
            mkmsg('Error: no person with pid %d' % pid)
            return

        pers = res[0]
        print(pers)
        # columns are:
        # pid, lunaid fullname fname lname dob sex hand addate
        # source curage curagefloor lastvisit numvisits nstudies ndrops ids
        # studies visittypes maxdrop
        self.render_person(pid=pers[0], lunaid=pers[1], fullname=pers[2],
                           sex=pers[6], age=pers[10])

    def render_person(self, pid, fullname, age, sex, lunaid=None):
        """
        how to populate all the subject info
        """
        self.disp_model['pid'] = pid
        self.disp_model['fullname'] = fullname
        self.disp_model['age'] = age
        self.disp_model['sex'] = sex
        self.disp_model['lunaid'] = lunaid

        # fname is all but the last name in fullname
        names = fullname.split(' ')
        self.disp_model['fname'] = " ".join(names[0:-1])
        self.disp_model['lname'] = names[-1]

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
        if (row_i == -1):
            print("DEBUG: visit_item_select but row_i is -1")
            return

        d = self.visit_table_data[row_i]
        try:
            vid = d[self.visit_columns.index('vid')]
        except IndexError:
            print('tuple index out of range')

        study = d[self.visit_columns.index('study')]
        pid = self.disp_model['pid']
        fullname = self.disp_model['fullname']

        # for j in range(self.visit_table.columnCount()):
        #self.visit_table.item(row_i, j).setBackground(QtGui.QColor(182, 236, 48))
        self.click_color(self.visit_table, row_i)

        self.checkin_what_data['pid'] = pid
        self.checkin_what_data['fullname'] = fullname
        try:
            self.checkin_what_data['vid'] = vid
        except UnboundLocalError:
            print('local variable vid referenced before assignment')
        self.checkin_what_data['study'] = study
        self.checkin_what_data['vtype'] = d[self.visit_columns.index('vtype')]
        self.checkin_what_data['datetime'] = d[self.visit_columns.index('day')]

        # as long as disp model matches visit (when wouldn't it?)
        # use lunaid from person table
        # Disable the checkin button when the subject is checkedin
        if(d[self.visit_columns.index('vstatus')] == 'checkedin'):
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

    def reschedule_all(self):
        """
        right click visit item -> reschedule
         need to remove from calendar and reinsert
        """
        # get what we clicked on
        row_i = self.visit_table.currentRow()
        status_i = self.visit_columns.index('vstatus')
        if row_i == -1:
            return
        vstatus = self.visit_table.item(row_i, status_i).text()
        if vstatus != 'sched':
            mkmsg("Can only reschedule 'sched' status, not '%s'" % vstatus)
            return

        # get old info. we will remove this after successful rescheduleing
        vid_i = self.visit_columns.index('vid')
        vid = self.visit_table.item(row_i, vid_i).text()
        googleuri = self.sql.query.get_googleuri(vid=vid)
        if not googleuri:
            mkmsg('No google uri for vid %d' % vid)
            return
        googleuri = googleuri[0]

        # create a new visit first
        # successful ScheduleVisit modal removes googleuri using schedule_to_db
        self.schedule_button_pushed(googleuri)
        # check delete was succesfull
        print("checking that we cannot find: %s" % googleuri)
        try:
            olduri_no_exist = self.cal.get_event(googleuri)
        except HttpError as httperr:
            print(httperr)
            # TODO: check error is actually 404
            olduri_no_exist = None

        if olduri_no_exist:
            mkmsg("Failed to update google calendar" +
                  "Can't delete %s. not removing from DB either" % googleuri)
            return

        # we also need to delete the origianl visit from the database
        try:
            self.sql.remove_visit(vid)
        except Exception as err:
            mkmsg('Unexpected error deleting (reschedule) from DB!' +
                  'Calendar (rm-ed) and DB (not rm-ed) are now out of sync\n' +
                  'remove vid=%s\n' % vid +
                  'Error: %s' % err)
            # TODO: remove newly added b/c new is probaly not in db!?
            return

        # finally update visit table
        self.update_visit_table()

    # Change color of the row whenever do leftclick
    def click_color(self, table, row_i):
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                if i == row_i:
                    table.item(i, j).setBackground(QtGui.QColor(191, 243, 228))
                    continue
                if(table is self.people_table):
                    try:
                        self.table_background(table, i, j)
                    except AttributeError:
                        print('NonType')
                else:
                    table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

        # Get rid of the color in other tables
        if table == self.visit_table:
            self.refresh_blank(self.contact_table)
            self.refresh_blank(self.people_table)

        elif table == self.contact_table:
            self.refresh_blank(self.visit_table)
            self.refresh_blank(self.people_table)

        elif table == self.people_table:
            self.refresh_blank(self.visit_table)
            self.refresh_blank(self.contact_table)

    def table_background(self, table, i, j):

        if table.item(i, 6).text() == 'subject':
            color = QtGui.QColor(249, 179, 139)
            table.item(i, j).setBackground(color)
        elif table.item(i, 6).text() == 'visit':
            color = QtGui.QColor(240, 230, 140)
            table.item(i, j).setBackground(color)
        elif table.item(i, 6).text() == 'future':
            color = QtGui.QColor(240, 240, 240)
            table.item(i, j).setBackground(color)
        elif table.item(i, 6).text() == 'family' or table.item(i, 6).text() == 'unknown':
            color = QtGui.QColor(203, 233, 109)
            table.item(i, j).setBackground(color)
        else:
            table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

    def refresh_blank(self, table):
        for i in range(table.rowCount()):
            for j in range(table.columnCount()):
                if table is self.people_table:
                    try:
                        self.table_background(table, i, j)
                    except AttributeError:
                        print('NonType')
                else:
                    table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

                # table.item(i, j).setBackground(QtGui.QColor(255, 255, 255))

    def updateVisitRA(self, ra):
        """ add or change visit RA assignment """
        row_i = self.visit_table.currentRow()
        d = self.visit_table_data[row_i]
        vid = d[self.visit_columns.index('vid')]

        # do not assign a checked in visit
        vstatus = d[self.visit_columns.index('vstatus')]
        if vstatus == 'checkedin':
            mkmsg("Cannot reassign a checked in visit!")
            return

        # pid = self.disp_model['pid']
        info = get_info_for_cal(self.sql.query, vid)
        # Update the database for RA
        info['ra'] = ra
        try:
            self.sql.query.update_RA(ra=info['ra'], vid=vid)
        except psycopg2.ProgrammingError:
            print('Error that does not make sense')

        print(info)
        #  1. update google calendar title
        info['googleuri'] = self.sql.query.get_googleuri(vid=vid)
        info['googleuri'] = info['googleuri'][0][0]
        info['calid'] = info['googleuri']

        try:
            # self.cal.delete_event(info['googleuri'])
            event = update_gcal(self.cal, info, assign=True)
        except Exception as err:
            mkmsg('update error! %s' % err)
            return
        # Update the event(e) in the database
        try:
            self.sql.query.update_uri(googleuri=event['id'], vid=vid)
        except psycopg2.ProgrammingError:
            print('Error that does not make sense')

        # For this, sched is origionally assigned. Changed it to sche so that the data base will  accept the vstatus.
        # //////////////////////////////////////////////
        new_node = {'ra': ra, 'action': 'assigned', 'vid': vid}
        # //////////////////////////////////////////////
        #  2. add to visit_action # vatimestamp? auto inserted?
        self.sql.insert('visit_action', new_node)
        #  3. update visit
        # TODO/FIXME: is this done elsewhere?  20190615WF
        # self.sql.update('visit', 'googleuri', event['id'], 'vid', vid)
        #  4. refresh visit view
        self.update_visit_table()

    def edit_visit_table(self):
        """ on item click: set visit as subject for actions """
        row_i = self.visit_table.currentRow()
        if row_i == -1:
            print("DEBUG: row is -1 in edit_visit_table, cannot set visit_id!")
            return
        self.visit_id = self.visit_table.item(row_i, 9).text()
        self.name = self.visit_table.item(row_i, 0).text()

    def update_visit_table(self):
        """ update visit table display"""
        pid = self.disp_model['pid']
        self.visit_table_data = self.sql.query.visit_by_pid(pid=pid)
        print(self.visit_table_data)
        generic_fill_table(self.visit_table, self.visit_table_data)

    def update_contact_table(self):
        """ update contact table display"""
        self.contact_table_data = self.sql.query.contact_by_pid(
            pid=self.disp_model['pid'])
        generic_fill_table(self.contact_table, self.contact_table_data)

    def update_note_table(self):
        """ update note table display"""
        # pid=self.disp_model['pid']
        print(self.disp_model['pid'])
        self.note_table_data = self.sql.query.note_by_pid(
            pid=self.disp_model['pid'])
        generic_fill_table(self.note_table, self.note_table_data)

    def update_people_table(self, fullname):
        """ update person table display"""
        # TODO/FIXME: what if want search by lunaid or age or study or ...
        self.search_people_by_name(fullname)

    def add_person_to_db(self):
        """ person to db """
        print(self.AddPerson.persondata)
        # pop up window and return if not valid
        (valid, msg) = self.AddPerson.isvalid()
        if not valid:
            mkmsg("Person info not valid?! %s" % msg)
            return

        self.fullname.setText('%(fname)s %(lname)s' %
                              self.AddPerson.persondata)
        # put error into dialog box
        try:
            # self.sql.query.insert_person(**(self.AddPerson.persondata))
            data = self.AddPerson.persondata
            data['adddate'] = datetime.datetime.now()
            self.sql.insert('person', data)
        except Exception as err:
            mkmsg(str(err))
            return

        self.search_people_by_name(self.fullname.text())

    # #### SCHEDULE #####

    def render_schedule(self, schedule_from=None):
        """
        handle setting up scheduling middle area
        """
        # only changes when we click on a different table
        if schedule_from:
            self.schedule_what_data['whichCntr'] = schedule_from

        # update schedule text
        self.schedule_what_data['pid'] = self.disp_model['pid']
        self.schedule_what_data['fullname'] = self.disp_model['fullname']
        self.schedule_what_data['lunaid'] = self.disp_model['lunaid']
        self.schedule_what_data['date'] = caltodate(self.calendarWidget)
        # Labels
        # def update_schedule_what_label(self):
        # def update_checkin_what_label(self):
        # def update_checkin_time(self):
        text = "%(fullname)s (%(lunaid)s): %(date)s@%(time)s" % \
               self.schedule_what_data
        self.schedule_what_label.setText(text)

        time = self.timeEdit.dateTime().time().toPyTime()
        if time:
            self.schedule_what_data['time'] = time

        # when we have a time and a person, enable schedule button
        if self.schedule_what_data['pid'] and \
           self.schedule_what_data['time'] and \
           self.schedule_what_data['date']:
            self.schedule_button.setDisabled(False)

        # is the button for scheduling or rescheduling
        if self.schedule_what_data['whichCntr'] == ScheduleFrom.VISIT:
            self.schedule_button.setText('Reschedule')
            self.schedule_button.clicked.connect(self.reschedule_all)
            # TODO: fetching vstatus happens twice. make function?
            row_i = self.visit_table.currentRow()
            status_i = self.visit_columns.index('vstatus')
            vstatus = self.visit_table.item(row_i, status_i).text()
            # if vstatus is not sched -- no reschedule
            if vstatus != 'sched':
                self.schedule_button.setDisabled(True)
        else:
            self.schedule_button.setText('Schedule')
            self.schedule_button.clicked.connect(self.schedule_button_pushed)

        # TODO: indicate schedule_from
        #  with e.g. an arrow icon

        print('render schedule: %s' % self.schedule_what_data)

    # #### VISIT #####
    # see generic_fill_table
    def schedule_button_pushed(self, old_google_uri=False):
        d = self.schedule_what_data['date']
        t = self.schedule_what_data['time']
        # Got the pid ID for the person who scheduled.
        pid = self.disp_model['pid']
        fullname = self.disp_model['fullname']
        if d is None or t is None:
            mkmsg('set a date and time before scheduling')
            return()
        if pid is None or fullname is None:
            mkmsg('select a person before trying to schedule')
            return()
        dt = datetime.datetime.combine(d, t)
        self.ScheduleVisit.setup(pid, fullname, self.RA, dt, old_google_uri)
        self.ScheduleVisit.show()

    def schedule_to_db(self):
        # valid?
        if not self.useisvalid(self.ScheduleVisit, "Cannot schedule visit"):
            return
        # todo: add to calendar or msgerr
        # makw the note index None so that the sql can recongnize it.
        if(self.ScheduleVisit.model['notes'] == ''):
            self.ScheduleVisit.model['notes'] = None
            print("updated note to none")

        try:
            self.ScheduleVisit.add_to_calendar(self.cal, self.disp_model)
            print(self.disp_model)
        except Exception as err:
            mkmsg('Failed to add to google calendar; not adding. %s' % str(err))
            return()
        # catch sql error
        # N.B. action(vstatus) intentionally empty -- will be set to 'sched'
        if not self.sqlInsertOrShowErr(
                'visit_summary', self.ScheduleVisit.model):
            # TODO/FIXME: remove from calendar if sql failed
            return()

        # we have a valid old_googleuri -> remove it
        if(self.ScheduleVisit.old_googleuri and
           self.ScheduleVisit.old_googleuri is not None and
           len(self.ScheduleVisit.old_googleuri) > 0):
            google_old_uri = self.ScheduleVisit.old_googleuri[0][0]
            try:
                self.cal.delete_event(google_old_uri)
            except HttpError as httperr:
                mkmsg('Failed to delete google event %s' % google_old_uri)
                print(httperr)

        # need to refresh visits
        self.update_visit_table()
        self.update_note_table()

    def visits_from_database(self):
        """Method that queries the database for the specific visits"""
        self.visit_table_data = self.VisitsCards.setup(self.disp_model['pid'], self.sql)
        # Upload the data to the table 
        self.visit_table.setRowCount(len(self.visit_table_data))
        # seems like we need to fill each item individually
        # loop across rows (each result) and then into columns (each value)
        for row_i, row in enumerate(self.visit_table_data):
            for col_i, value in enumerate(row):
                item = QtWidgets.QTableWidgetItem(str(value))
                self.visit_table.setItem(row_i, col_i, item)

    def record_contact_push(self):
        """ Method for record push --Waiting for later implementation """
        self.AddContactNotes.show()
        # Find the cid from the table
        row_i = self.contact_table.currentRow()
        cid = self.contact_table.item(row_i, 5).text()
        # Pass in cid to the user intrface
        self.AddContactNotes.set_contact_notes(cid)

    # ## checkin
    def checkin_button_pushed(self):
        pid = self.checkin_what_data['pid']
        # vid = self.checkin_what_data['vid']
        fullname = self.checkin_what_data['fullname']
        study = self.checkin_what_data['study']
        vtype = self.checkin_what_data['vtype']
        if study is None or vtype is None:
            mkmsg('pick a visit with a study and visit type')
            return()
        if pid is None or fullname is None:
            mkmsg('select a person before trying to checkin (howd you get here?)')
            return()

        # que up a new lunaid
        # N.B. we never undo this, but check is always for lunaid first
        if self.checkin_what_data.get('lunaid') is None:
            print('have no luna in checkin data! getting next')
            print(self.checkin_what_data)
            nextluna_res = self.sql.query.next_luna()
            nxln = nextluna_res[0][0]
            self.checkin_what_data['next_luna'] = nxln + 1
            print('next luna is %d' % self.checkin_what_data['next_luna'])

        # (self,pid,name,RA,study,study_tasks)
        study_tasks = [x[0] for x in
                       self.sql.query.
                       list_tasks_of_study_vtype(study=study, vtype=vtype)]
        print("checkin: launching %(fullname)s for %(study)s/%(vtype)s" %
              self.checkin_what_data)
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
            print(err)
            mkmsg('checkin failed!\n%s' % err)
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
        print(dt)
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
        j = self.cal_columns.index('what')
        # Loop Through the table to find people that were assigned.
        for i in range(self.cal_table.rowCount()):
            if '--' in self.cal_table.item(i, j).text():
                # Split the name form the events
                name = self.cal_table.item(i, j).text().split('--')[1]
                # add 1 to the count
                names[name] = names.get(name, 0) + 1

        # Alternative  -- use database
        #  res = self.sql.query.visits_this_week(startdate, enddate)
        #  for r in res:
        #    name = r[3]
        #    names[name] = names.get(name, 0) + 1

        # combine names and counts into one long string
        results = ", ".join(
            ["%s: %d" % (n, names[n]) for n in sorted(names.keys())])
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
            m_d = calevent['starttime'].strftime('%Y-%m-%d')
            tm = calevent['starttime'].strftime('%H:%M')
            self.cal_table.setItem(row_i, 0, QtWidgets.QTableWidgetItem(m_d))
            self.cal_table.setItem(row_i, 1, QtWidgets.QTableWidgetItem(tm))
            eventname = calevent['summary']
            self.cal_table.setItem(
                row_i, 2, QtWidgets.QTableWidgetItem(eventname))

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
            mkmsg('Undiagnosed error: cal row clicked > table data!')
            return
        # googleuri should be in database
        cal_id = self.cal_table_data[row_i].get('calid', None)
        if cal_id is None:
            mkmsg('Cal event does not have an id!? How?')
            return

        res = self.sql.query.visit_by_uri(googleuri=cal_id)
        if res:
            print(res)
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
        self.fullname.setText(self.disp_model['fullname'])
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
        print(cal_desc)
        current_date = self.cal_table.item(row_i, 0).text()
        current_time = self.cal_table.item(row_i, 1).text()
        current_date_time = current_date + ' ' + current_time + ':00'
        current_study = self.cal_table.item(row_i, 2).text().split('/')[0]
        # 7T x1 EEG-23yof (EG) - MB, LT
        title_regex = re.match(r'(\w+)/(\w+) x(\d+) (\d+)yo(\w)', cal_desc)
        if not title_regex:
            mkmsg("cannot parse calendar event title!\n" +
                  "expect 'study/type xX YYyo[m/f]' but have\n" + cal_desc)
            return None

        current_age = title_regex.group(4)
        current_gender = title_regex.group(5)

        if current_age is None:
            print("No current age in google cal event title!")
            return None

        res = self.sql.query.\
            get_pid_of_visit(vtimestamp=current_date_time,
                             study=current_study,
                             age=int(current_age))

        # Debuging, see results
        print(res)

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
        print(self.scheduled_date)
        self.checkin_status = self.sql.query.get_status(
            pid=pid, vtimestamp=self.scheduled_date)[0][0]
        print(self.checkin_status)

        if self.checkin_status == 'checkedin':
            self.checkin_button.setEnabled(False)

    # ### CONTACTS ###
    # self.add_contact_button.clicked.connect(self.add_contact_pushed)

    def add_contact_pushed(self):
        """ show add modal when button is pushed """
        # self.AddContact.setpersondata(d)
        self.AddContact.set_contact(
            self.disp_model['pid'],
            self.disp_model['fullname'])
        self.AddContact.show()

    def edit_contact_pushed(self):
        """ show edit modal when button is pushed """
        self.EditContact.edit_contact(self.contact_cid)
        self.EditContact.show()

    def update_contact_to_db(self):
        """ run sql update and refresh contact table """
        data = self.EditContact.edit_model
        self.sqlUpdateOrShowErr('contact', data['ctype'], data['cid'],
                                data['changes'], "cid")
        self.update_contact_table()

    # self.AddContact.accepted.connect(self.add_contact_to_db)
    def add_contact_to_db(self):
        """ run sql add and update table """
        # do we have good input?
        if not self.useisvalid(self.AddContact, "Cannot add contact"):
            return

        # catch sql error
        data = self.AddContact.contact_model
        data['added'] = datetime.datetime.now()
        # The contact is referring to the table in debeaver.
        self.sqlInsertOrShowErr('contact', data)
        self.update_contact_table()

    def edit_contact_table(self):
        """ on row click: update what contact is used for actions """
        row_i = self.contact_table.currentRow()
        self.click_color(self.contact_table, row_i)
        try:
            self.contact_cid = self.contact_table.item(row_i, 5).text()
        except AttributeError:
            print('weird error')
        try:
            self.name = self.contact_table.item(row_i, 0).text()
        except AttributeError:
            print('weird error')
        # print(contact_cid)

    # ## Notes
    def add_notes_pushed(self):
        """ on clikc run add notes modal """
        # self.Addnotes.setpersondata(d)
        self.AddNotes.set_note(self.disp_model['pid'],
                               self.disp_model['fullname'],
                               self.sql.query)
        # dropbox full of possible visits
        self.AddNotes.show()

    def add_notes_to_db(self):
        # Error check
        if not self.useisvalid(self.AddNotes, "Cannot add note"):
            return

        # add ra to model
        data = {**self.AddNotes.notes_model, 'ra': self.RA}

        # look at drop code and vid
        # both could be None
        dropcode = self.AddNotes.get_drop()
        vid = self.AddNotes.get_vid()
        # insert into note
        note_dict = {**data, 'vid': vid,
                     'dropcode': self.AddNotes.get_drop()}
        self.sqlInsertOrShowErr('note', note_dict)

        # whatever we've done, we need to update the view
        self.update_note_table()

    def sqlInsertOrShowErr(self, table, d):
        try:
            # self.sql.query.insert_person(**(self.AddPerson.persondata))
            print('insering into %s: %s' % (table, d))
            self.sql.insert(table, d)
            return(True)
        except Exception as err:
            mkmsg(str(err))
            return(False)

    # Later better map all the data into one variable so that it's easy to see.
    def sqlUpdateOrShowErr(self, table, id_column, id, new_value, id_type):
        try:
            self.sql.update(table, id_column, id, new_value, id_type)
            return(True)
        except Exception as err:
            mkmsg(str(err))
            return(False)


# actually launch everything
if __name__ == '__main__':
    # paths relative to where files are
    import os
    os.chdir(os.path.dirname(os.path.realpath(__file__)))

    APP = QtWidgets.QApplication([])

    if len(sys.argv) > 1:
        WINDOW = ScheduleApp(config_file=sys.argv[1])
    else:
        WINDOW = ScheduleApp()

    sys.exit(APP.exec_())
