from PyQt5 import uic, QtCore, QtWidgets
from LNCDutils import  comboval
import datetime, re

#Provide window for add Notes informaiton.

class AddNoteWindow(QtWidgets.QDialog):

#Add Autocomplete features later
    def __init__(self, parent = None):

        #Array for nid and vid
        self.nid_drop = None
        #The value for vid
        self.vid_value = []
        columns = ['note', 'pid', 'ndate']
        self.visit = None

        self.notes_model = {k: None for k in columns}
        super(AddNoteWindow, self).__init__(parent)
        uic.loadUi('./ui/add_notes.ui', self)
        self.setWindowTitle('Add Notes')

        #Only refresh the note_edit value for now and change the rest later.
        #self.suggestions = {'relation': ['Subject']}
        #Wire up xtype_box later.

        #self.ctype_box_2.activated.connect(lambda: self.allvals('ctype'))
        self.note_edit.textChanged.connect(lambda: self.allvals('note'))

        #Get the newly entered text for preparing to enter them to the database.

    def set_note(self, pid, name, query):
        """
        contruct note dialog box
        """
        self.notes_model['pid'] = pid
        self.ctype_box.clear()         # rm hardcode ui elem., repop w/dropcoes
        self.ctype_box_2.clear()       # rm prev visits
        self.notes_model['note'] = ""  # rm prev notes
        self.vid_lookup = {}

        # add dropreasons (like 'BAD_VIEN', 'SUBJ_ISSUE')
        self.ctype_box.addItem("")
        res = query.list_dropcodes()
        for r in res:
            self.ctype_box.addItem(r[0] + " (" + r[1] + ")")

        # add possible visits that could be assocated with the note
        res = query.vdesc_from_pid(pid=pid)
        self.ctype_box_2.addItem('NULL')  # always have null
        if res:
            self.ctype_box_2.addItems([x[1] for x in res])
            self.vid_lookup = {x[1]: x[0] for x in res}

    def get_vid(self):
        visit_desc = self.ctype_box_2.currentText()
        # Get the vid value when the ok button is clicked on the set node page.
        vid = None
        if(visit_desc != 'NULL'):
            vid = self.vid_lookup[visit_desc]
        return(vid)

    def get_drop(self):
        dlevel = self.ctype_box.currentText()
        # Get the vid value when the ok button is clicked on the set node page.
        drop = None
        if(dlevel is not None and dlevel != ''):
            drop = re.sub(' \\(.*', '', dlevel)
        return(drop)

    def allvals(self, key='all'):
        print('note: updating %s' % key)
        # Directly pass the ctype_box_2 value into a variable called visit to query from the DB.
        # if(key in ['ctype','all']): self.visit = comboval(self.ctype_box_2)
        if(key in ['note', 'all']):
            self.notes_model['note'] = self.note_edit.text()
        if(key in ['ndate', 'all']):
            self.notes_model['ndate'] = datetime.datetime.now()
        print(self.notes_model)

    def isvalid(self):
        self.allvals('all')
        print("add note is valid?\n%s" % str(self.notes_model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.notes_model.keys():
            if self.notes_model[k] is None or self.notes_model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})

        self._want_to_close = True
        #print("sdfsfs")
        return({'valid':True,'msg':'OK'})
