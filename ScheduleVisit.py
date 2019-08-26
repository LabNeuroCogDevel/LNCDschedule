import datetime
import re
import json
from PyQt5 import uic, QtCore, QtWidgets
from LNCDutils import comboval, isOrAll, make_calendar_event

"""
This class provides a window for scheduling visit information
data in conact_model
"""


class ScheduleVisitWindow(QtWidgets.QDialog):
    """ model and viewer for adding a visit """

    def __init__(self, parent=None):
        super(ScheduleVisitWindow, self).__init__(parent)
        uic.loadUi('./ui/schedule.ui', self)
        self.setWindowTitle('Schedule Visit')

        # what data do we need
        # action intentionally empty -- will be set to 'sched'
        self.columns = ['vtimestamp', 'study', 'vtype', 'visitno', 'ra',
                   'pid', 'cohort', 'dur_hr', 'notes']
        self.model = {k: None for k in self.columns}

        # used to update google (remove old)
        self.old_googleuri = None
        self.vid = None

        # change this to true when validation works
        self._want_to_close = False

        # ## wire up buttons and boxes
        self.vtimestamp_edit.dateTimeChanged.connect(
            lambda: self.allvals('vtimestamp'))
        self.study_box.activated.connect(lambda: self.allvals('study'))
        self.vtype_box.activated.connect(lambda: self.allvals('vtype'))
        self.visitno_spin.valueChanged.connect(lambda: self.allvals('visitno'))
        self.dur_hr_spin.valueChanged.connect(lambda: self.allvals('dur_hr'))
        self.cohort_edit.textChanged.connect(lambda: self.allvals('cohort'))
        self.note_edit.textChanged.connect(lambda: self.allvals('notes'))

    def reset_model(self):
        """reset values"""
        self.model = {k: None for k in self.columns}
        self.old_googleuri = None
        self.vid = None

    def add_vtypes(self, vals):
        """ called after sql query to get all visit types """
        self.vtype_box.addItems(vals)

    def add_studies(self, vals):
        """ called after sql query to get all studies """
        self.study_box.addItems(vals)

    def setup(self, pid, name, RA, dt, old_googleuri=None, vid=None):
        """ populate model, run on 're/schedule' button click """
        # print('schedule setup: pid=%s (%s)' % (pid, name))
        self.model['pid'] = pid
        self.model['ra'] = RA
        qdt = QtCore.QDateTime.fromTime_t(int(dt.timestamp()))
        self.vtimestamp_edit.setDateTime(qdt)
        self.who_label.setText(name)
        # update reschedule information
        # not in model because it does not go into db
        self.old_googleuri = old_googleuri
        self.vid = vid

    def allvals(self, key='all'):
        """set data from gui edit value
        optionally be specific"""
        # print('schedule visit: updating %s' % key)
        if isOrAll(key, 'vtype'):
            self.model['vtype'] = comboval(self.vtype_box)
        if isOrAll(key, 'study'):
            self.model['study'] = comboval(self.study_box)
        if isOrAll(key, 'cohort'):
            self.model['cohort'] = self.cohort_edit.text()
        if isOrAll(key, 'visitno'):
            self.model['visitno'] = self.visitno_spin.value()
        if isOrAll(key, 'dur_hr'):
            self.model['dur_hr'] = self.dur_hr_spin.value()
        # notes inserted as json array (via visit_summary view trigger)

        if isOrAll(key, 'notes'):
            notestr = self.note_edit.toPlainText()

            if notestr:
                # sqlalchemy handles objects directly
                self.model['notes'] = [notestr]
                # if we use pgsql directly
                # notestr = json.dumps([notestr])
                # print(notestr)
            else:
                self.model['notes'] = None
                # TODO: should this be [None] tests_add_visit_and_note says no

        # looks like: Thu Oct 26 14:00:00 2017
        # format '%a %b %d %H:%M:%S %Y'
        if isOrAll(key, 'vtimestamp'):
            self.model['vtimestamp'] = self.\
                vtimestamp_edit.dateTime().toString()

    def add_to_calendar(self, cal, disp_model_person_dict):
        """use lncdCal class to add the event to the calendar
        and the resulting eventid to the model (as googleuri) """
        printmodel = {**disp_model_person_dict, **self.model}
        printmodel['initials'] = "".join(
            map(lambda x: x[0], printmodel['fullname'].split()))
        event = make_calendar_event(cal, printmodel)
        self.model['googleuri'] = event.get('id')
        return self.model['googleuri']

    def isvalid(self):
        """ do we have good data? just check that no key is null
        return (valid:T/F,msg:....) """
        self.allvals('all')
        print("schedule visit is valid?\n%s" % str(self.model))
        for k in self.model.keys():
            if k == 'notes':
                continue  # allow note to be null
            if self.model[k] is None or self.model[k] == '':
                return({'valid': False, 'msg': 'bad %s' % k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid': True, 'msg': 'OK'})
