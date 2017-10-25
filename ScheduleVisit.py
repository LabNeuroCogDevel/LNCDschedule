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
        columns=['vtimestamp','study','vtype','visitno','RA','pid']
        self.model = { k: None for k in columns }

        # change this to true when validation works
        self._want_to_close = False

        ## wire up buttons and boxes
        self.study_box.activated.connect(lambda: self.allvals('study'))
        self.vtype_box.activated.connect(lambda: self.allvals('vtype'))
        self.visitno_spin.valueChanged.connect(lambda: self.allvals('visitno'))
        self.vtimestamp_edit.dateTimeChanged.connect(lambda: self.allvals('relation'))

    def add_vtypes(self,vals): self.vtype_box.addItems(vals)
    def add_studies(self,vals): self.study_box.addItems(vals)

    def setup(self,pid,name,RA,dt):
        print('updating contact with %s and %s'%(pid,name))
        self.model['pid'] = pid
        self.model['RA']  = RA
        qdt = QtCore.QDateTime.fromTime_t(dt.timestamp())
        self.vtimestamp_edit.setDateTime(qdt)
        self.who_label.setText(name)

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('schedule visit: updating %s'%key)
        if(isOrAll(key,'vtype')  ):    self.model['vtype']  = comboval(self.vtype_box)
        if(isOrAll(key,'study')  ):    self.model['study']  = comboval(self.study_box)
        if(isOrAll(key,'visitno')):    self.model['vistno'] = self.visitno_spin.value()
        if(isOrAll(key,'vtimestamp')): self.model['vtimestamp'] = self.vtimestamp_edit.toString()
        

    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("schedule visit is valid?\n%s"%str(self.model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.model.keys():
            if self.model[k] == None or self.model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid':True,'msg':'OK'})
    
        
