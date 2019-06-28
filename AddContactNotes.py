from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

"""
This class provides a window for adding contact information
data in conact_model
"""
class AddContactNotesWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        
        columns = ['cstatus', 'detail', 'cid']
        self.contact_notes_model = {k:None for k in columns}
        super(AddContactNotesWindow, self).__init__(parent)
        uic.loadUi('./ui/add_contact_notes.ui',self)
        self.setWindowTitle('Add Contact Notes')

        #Wire up buttons and box
        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.notes.textChanged.connect(lambda: self.allvals('note'))

    def set_contact_notes(self, cid):
        #Enter the cid value in the user interface
        print('current cid is %s'%cid)
        self.contact_notes_model['cid'] = cid
        self.cid.setText(cid)


    def allvals(self, key='all'):
        if(key in ['ctype',    'all']): self.contact_notes_model['ctype'] = comboval(self.ctype_box)
        if(key in ['detail',   'all']): self.contact_notes_model['detail'] = self.detail.text()

