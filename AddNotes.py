from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *
import datetime, re

#Provide window for add Notes informaiton.

class AddNoteWindow(QtWidgets.QDialog):

#Add Autocomplete features later
    def __init__(self, parent = None):

        #Array for nid and vid
        self.nid_vid = {}
        #The value in the drop down box
        self.drop_down_value = []
        #The value for vid
        self.vid_value = []
        columns = ['note', 'pid']
        self.visit = None

        self.notes_model = {k: None for k in columns }
        super(AddNoteWindow, self).__init__(parent)
        uic.loadUi('./ui/add_notes.ui', self)
        self.setWindowTitle('Add Notes')

        #Only refresh the note_edit value for now and change the rest later.
        #self.suggestions = {'relation': ['Subject']}
        #Wire up xtype_box later.

        #self.ctype_box_2.activated.connect(lambda: self.allvals('ctype'))
        self.note_edit.textChanged.connect(lambda: self.allvals('note'))

        #Get the newly entered text for preparing to enter them to the database.
    def set_note(self, pid, name, ndate):
        self.notes_model['pid'] = pid
        #Clear the drop_down box every time it changes to a new subject.
        self.ctype_box_2.clear()

        #Loop through the array which contains the drop down values and then put it in the drop_down box.
        self.ctype_box_2.addItem('NULL')

        for x in range(len(self.drop_down_value)):
            self.ctype_box_2.addItem(self.drop_down_value[x])
             #Clear the drop_down_value every time it changes to a new obejct.
        self.drop_down_value.clear()
        self.nid_vid.clear()

        #Method to add the ndate to the datebase
    def add_ndate(self):
        self.notes_model['ndate'] = datetime.datetime.now()

    def get_vid(self):
        #Get the vid value when the ok button is clicked on the set node page.
        if(self.ctype_box_2.currentText() == 'NULL'):
            vid = None
        else: 
            vid = (self.ctype_box_2.currentText()).split(',')[0]
            #vid is shown as a string, so we need to remove "'" before converting it to an int
            self.nid_vid['vid'] = int(re.sub("'", "", vid))

    def allvals(self,key='all'):
        print('contact: updating %s'%key)
        #Directly pass the ctype_box_2 value into a variable called visit to query from the DB.
        if(key in ['ctype'   ,'all']): self.visit = comboval(self.ctype_box_2)
        #print(self.visit)
        if(key in ['note'     ,'all']): self.notes_model['note'] = self.note_edit.text()

    def isvalid(self):
        self.allvals('all')
        print("add note is valid?\n%s"%str(self.notes_model))
        #print(self.drop_down_value)
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.notes_model.keys():
            if self.notes_model[k] == None or self.notes_model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        #print("sdfsfs")
        return({'valid':True,'msg':'OK'})
    


        


        




