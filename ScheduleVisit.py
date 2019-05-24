from PyQt5 import uic,QtCore, QtWidgets
import datetime
from LNCDutils import  *

"""
This class provides a window for scheduling visit information
data in conact_model
"""
class ScheduleVisitWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        super(ScheduleVisitWindow,self).__init__(parent)
        uic.loadUi('./ui/schedule.ui',self)
        self.setWindowTitle('Schedule Visit')

        # what data do we need
        # action intentionally empty -- will be set to 'sched'
        columns=['vtimestamp','study','vtype','visitno','ra','pid','cohort','dur_hr','note']
        self.model = { k: None for k in columns }

        # change this to true when validation works
        self._want_to_close = False

        ## wire up buttons and boxes
        self.vtimestamp_edit.dateTimeChanged.connect(lambda: self.allvals('vtimestamp'))
        self.study_box.activated.connect(lambda: self.allvals('study'))
        self.vtype_box.activated.connect(lambda: self.allvals('vtype'))
        self.visitno_spin.valueChanged.connect(lambda: self.allvals('visitno'))
        self.dur_hr_spin.valueChanged.connect(lambda: self.allvals('dur_hr'))
        self.cohort_edit.textChanged.connect(lambda: self.allvals('cohort'))
        self.note_edit.textChanged.connect(lambda: self.allvals('note'))

    def add_vtypes(self,vals): self.vtype_box.addItems(vals)
    def add_studies(self,vals): self.study_box.addItems(vals)

    def setup(self,pid,name,RA,dt, old_googleuri=None):
        print('updating schedule with %s and %s'%(pid,name))
        self.model['pid'] = pid
        self.model['ra']  = RA
        self.old_googleuri = old_googleuri
        qdt = QtCore.QDateTime.fromTime_t(int(dt.timestamp()))
        self.vtimestamp_edit.setDateTime(qdt)
        self.who_label.setText(name)

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('schedule visit: updating %s'%key)
        if(isOrAll(key,'vtype')  ):    self.model['vtype']   = comboval(self.vtype_box)
        if(isOrAll(key,'study')  ):    self.model['study']   = comboval(self.study_box)
        if(isOrAll(key,'cohort')):     self.model['cohort']  = self.cohort_edit.text()
        if(isOrAll(key,'visitno')):    self.model['visitno'] = self.visitno_spin.value()
        if(isOrAll(key,'dur_hr')):     self.model['dur_hr']  = self.dur_hr_spin.value()
        if(isOrAll(key,'note')):       self.model['note']    = self.note_edit.toPlainText()

        #looks like: Thu Oct 26 14:00:00 2017
        if(isOrAll(key,'vtimestamp')): self.model['vtimestamp'] = self.vtimestamp_edit.dateTime().toString()
        
    """
    use lncdCal class to add the event to the calendar
    and the resulting eventid to the model (as googleuri)
    """
    def add_to_calendar(self, cal, disp_model_person_dict):
        printmodel = {**disp_model_person_dict, **self.model}
        printmodel['initials'] = "".join(
                map(lambda x: x[0], printmodel['fullname'].split()))
        event = make_calendar_event(cal, printmodel)
        self.model['googleuri'] = event.get('id')

    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("schedule visit is valid?\n%s"%str(self.model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.model.keys():
            if k == 'note': continue # allow note to be null
            if self.model[k] == None or self.model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid':True,'msg':'OK'})
