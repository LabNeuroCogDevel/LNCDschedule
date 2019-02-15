from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

"""
This class provides a window for adding a person
persondata should be used to modified data
"""
class AddPersonWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        self.persondata={'fname': None, 'lname': None, 'dob': None, 'sex': None,'hand': None, 'source': None}
        super(AddPersonWindow,self).__init__(parent)
        uic.loadUi('./ui/add_person.ui',self)
        self.setWindowTitle('Add Person')

        # change this to true when validation works
        self._want_to_close = False

        ## wire up buttons and boxes
        self.dob_edit.selectionChanged.connect(lambda: self.allvals('dob'))
        self.hand_edit.activated.connect(lambda: self.allvals('hand'))
        self.sex_edit.activated.connect(lambda: self.allvals('sex'))
        self.fname_edit.textChanged.connect(lambda: self.allvals('fname'))
        self.lname_edit.textChanged.connect(lambda: self.allvals('lname'))
        # source
        # todo: toggle visitble of text edit if source is not other, use that value
        self.source_text_edit.textChanged.connect(lambda:self.allvals('source'))

    """
    use provided dictionary d to set persondata
    """
    def setpersondata(self,d):
        print("set person data: %s"%str(d))
        for k in self.persondata.keys():
            if k in d: self.persondata[k] = d[k]

        self.fname_edit.setText(self.persondata['fname'] )
        self.lname_edit.setText(self.persondata['lname'] )

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('updating %s'%key)
        if(key in ['dob','all']):   self.persondata['dob']   = caltodate(self.dob_edit)
        if(key in ['hand','all']):  self.persondata['hand']  = comboval(self.hand_edit)
        if(key in ['sex','all']):   self.persondata['sex']   = comboval(self.sex_edit)
        if(key in ['fname','all']): self.persondata['fname'] = self.fname_edit.text()
        if(key in ['lname','all']): self.persondata['lname'] = self.lname_edit.text()
        # todo, toggle visibility and pick combo or text
        if(key in ['source','all']):
            self.persondata['source']= self.source_text_edit.text()
        

    """
    do we have good data? just check that no key is null
    """
    def isvalid(self):
        self.allvals('all')
        print("add person is valid?\n%s"%str(self.persondata))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.persondata.keys():
            if self.persondata[k] == None or self.persondata[k] == '': return(False)
        # TODO: check dob is not today
        self._want_to_close = True
        return(True)
    
