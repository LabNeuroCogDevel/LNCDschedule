from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

class EditNotesWindow(QtWidgets.QDialog):

    def __init__(self,parent = None):
        
        super(EditNotesWindow,self).__init__(parent)

        columns = ['ctype', 'changes', 'pid']
        self.edit_model = {k:None for k in columns}

        uic.loadUi('./ui/edit_note.ui',self)
        self.setWindowTitle('Edit Notes')

        #Wire up buttons and boxes
        #Disable editing the vid
        self.value_box_2.setDisabled(True)

        self.ctype_box.activated.connect(self.formatter)

        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.value_box.textChanged.connect(lambda: self.allvals('value'))
    
    def allvals(self, key = 'all'):

        if(key in ['ctype', 'all']):
            self.edit_model['ctype'] = self.ctype_box.currentText()
        if(key in ['value', 'all']):
            self.edit_model['changes'] = self.value_box.text()

    def edit_note(self, data):

        self.data = data
        


    def formatter(self):
        #Populate box with default (previous) value

        want_edit = str(self.ctype_box.currentText())
        default_value = self.data.get(want_edit, '')
        self.value_box.setText(default_value)