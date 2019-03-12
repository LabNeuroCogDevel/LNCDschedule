from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

"""
This class provides a window for adding contact information
data in conact_model
"""
class AddContactWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        columns=['ctype','cvalue','relation','who','pid']
        self.contact_model = { k: None for k in columns }
        super(AddContactWindow,self).__init__(parent)
        uic.loadUi('./ui/add_contact.ui',self)
        self.setWindowTitle('Add Contact')

        # change this to true when validation works
        self._want_to_close = False

        ## autocompelte?!
        self.suggestions = {'relation': ['Subject']}

        ## wire up buttons and boxes
        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.who_edit.textChanged.connect(lambda: self.allvals('who'))
        self.relation_edit.textChanged.connect(lambda: self.allvals('relation'))
        self.cvalue_edit.textChanged.connect(lambda: self.allvals('cvalue'))

    def add_ctypes(self,vals): self.ctype_box.addItems(vals)
    def suggest_relation(self,vals): self.suggestions['relation']=vals
    def set_contact(self,pid,name):
        print('updating contact with %s and %s'%(pid,name))
        self.contact_model['pid'] = pid
        self.contact_name.setText(name)
        self.relation_edit.setText('Subject')
        self.who_edit.setText(name)

    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('contact: updating %s'%key)
        if(key in ['ctype'   ,'all']): self.contact_model['ctype']    = comboval(self.ctype_box)
        if(key in ['who'     ,'all']): self.contact_model['who']      = self.who_edit.text()
        if(key in ['relation','all']): self.contact_model['relation'] = self.relation_edit.text()
        if(key in ['cvalue'  ,'all']): self.contact_model['cvalue']   = self.cvalue_edit.text()
        

    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("add contact is valid?\n%s"%str(self.contact_model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.contact_model.keys():
            if self.contact_model[k] == None or self.contact_model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid':True,'msg':'OK'})
    
        
