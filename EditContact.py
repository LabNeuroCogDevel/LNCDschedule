from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

"""
This class provides a window for adding contact information
data in conact_model
"""
class EditContactWindow(QtWidgets.QDialog):

    def __init__(self,parent = None):

        super(EditContactWindow,self).__init__(parent)
        uic.loadUi('./ui/edit_contact.ui',self)
        self.setWindowTitle('Edit Contact')

        ## wire up buttons and boxes
        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.value_box.textChanged.connect(lambda: self.allvals('value'))

    def allvals(self, key = 'all'):
        if(key in ['ctype'    ,'all']): self.edit_model['ctype']=self.ctype_box.currentText()
        if(key in ['value'    ,'all']): self.edit_model['relation']=self.value_box.text()
    def edit_contact(self,cid):
        self.value_box_2.setText(str(cid))
        edit_model['cid'] = cid