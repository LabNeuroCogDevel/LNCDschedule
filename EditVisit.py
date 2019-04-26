from PyQt5 import uic,QtCore, QtWidgets
from LNCDutils import  *

"""
This class provides a window for adding contact information
data in conact_model
"""
class EditVisitWindow(QtWidgets.QDialog):

    def __init__(self,parent = None):

        columns=['vvalue','changes','vid']
        self.edit_model = { k: None for k in columns }
        super(EditVisitWindow,self).__init__(parent)
        uic.loadUi('./ui/edit_visit.ui',self)
        self.setWindowTitle('Edit Visit')

        ## wire up buttons and boxes
        self.ctype_box.activated.connect(lambda: self.allvals('ctype'))
        self.value_box.textChanged.connect(lambda: self.allvals('value'))

    def allvals(self, key = 'all'):
        if(key in ['ctype'    ,'all']): self.edit_model['ctype']=self.ctype_box.currentText()
        if(key in ['value'    ,'all']): self.edit_model['changes']=self.value_box.text()
    def edit_visit(self,vid):
        self.value_box_2.setText(str(vid))
        self.edit_model['vid'] = vid