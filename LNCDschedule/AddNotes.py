from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

#Provide window for add Notes informaiton.

class AddNoteWindow(QtWidgets.QDialog):

#Add Autocomplete features later
    def __init__(self, parent = None):

        #self.notes_model = {k: None for k in columns}
        columns = ['note', 'pid']
        self.notes_model = {k: None for k in columns }
        super(AddNoteWindow, self).__init__(parent)
        uic.loadUi('./ui/add_notes.ui', self)
        self.setWindowTitle('Add Notes')

        #Only refresh the note_edit value for now and change the rest later.
        #self.suggestions = {'relation': ['Subject']}
        #Wire up xtype_box later.
        self.note_edit.textChanged.connect(lambda: self.allvals('note'))

        #Get the newly entered text for preparing to enter them to the database.
    def set_note(self, pid, name):
    	self.notes_model['pid'] = pid

    def allvals(self,key='all'):
        print('contact: updating %s'%key)
        #print(self.note_edit.text())
        #if(key in ['ctype'   ,'all']): self.notes_model['ctype']    = comboval(self.ctype_box)
        if(key in ['note'     ,'all']): self.notes_model['note']      = self.note_edit.text()

    def isvalid(self):
        self.allvals('all')
        print("add note is valid?\n%s"%str(self.notes_model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.notes_model.keys():
            if self.notes_model[k] == None or self.notes_model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        #print("sdfsfs")
        return({'valid':True,'msg':'OK'})
    


        


        




