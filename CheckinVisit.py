from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  *

"""
This class provides a window for scheduling visit information
data in conact_model
"""
class CheckinVisitWindow(QtWidgets.QDialog):

    def __init__(self,parent=None):
        super(CheckinVisitWindow,self).__init__(parent)
        uic.loadUi('./ui/checkin.ui',self)
        self.setWindowTitle('Checkin Visit')

        # what data do we need
        # action intentionally empty -- will be set to 'sched'
        data_columns=['vscore','note','lunaid','ra','pid','tasks']
        self.model = { k: None for k in data_columns }

        # change this to true when validation works
        self._want_to_close = False

        # prepare all tasks table | filled by "set_all_tasks"
        all_tasks_columns=['task','studies','modes']
        self.all_tasks_table.setColumnCount(len(all_tasks_columns))
        self.all_tasks_table.setHorizontalHeaderLabels(all_tasks_columns)

        ## wire up buttons and boxes
        self.vscore_spin.valueChanged.connect(lambda: self.allvals('vscore'))
        self.note_edit.textChanged.connect(lambda: self.allvals('note'))
        self.lunaid_edit.textChanged.connect(lambda: self.allvals('lunaid'))

        ## add if selected in all tasks (and not already there)
        self.all_tasks_table.itemClicked.connect(self.move_from_all)
        self.tasks_list.itemClicked.connect(self.remove_task)




    def move_from_all(self,item):
        nitems=self.tasks_list.count()
        have_items = [ self.tasks_list.item(i).text() for i in range(nitems) ]
        print("add %s"%item.text())
        if item.text() not in have_items:
            self.tasks_list.addItem(item.text())
            self.tasks_list.item(nitems).setBackground(QtGui.QColor('red'))
            #todo only color if not in study
    def remove_task(self,item):
        print("remove task %s"%item.text())
        rowi=self.tasks_list.row(item)
        self.tasks_list.takeItem(rowi)

        
    def set_all_tasks(self,all_tasks):
        self.all_tasks_data = all_tasks
        generic_fill_table(self.all_tasks_table,self.all_tasks_data)

    def setup(self,pid,name,RA,study,study_tasks):
        print('updating checkin with %s and %s'%(pid,name))
        self.model['pid'] = pid
        self.model['ra']  = RA
        self.who_label.setText(name)
        self.tasks_list.insertItems(0,study_tasks)
        self.all_task_disp(study)

    def all_task_disp(self,study):
        # sort all task data relative to study and visit type
        # re-populate
        generic_fill_table(self.all_tasks_table,self.all_tasks_data)

        # color current study
        #for rowi in range(0,self.all_tasks_table.rowCount()):
        #    all_taks_table
            #if self.all_tasks_table.
    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('checkin visit: updating %s'%key)
        if(isOrAll(key,'lunaid')):     self.model['lunaid'] = self.lunaid_edit.text()
        if(isOrAll(key,'vscore')):    self.model['vscore']  = self.visitno_spin.value()
        if(isOrAll(key,'note')):       self.model['note']   = self.note_edit.toPlainText()
        # todo collected

        
    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("schedule visit is valid?\n%s"%str(self.model))
        #print("close?: %s; checking if %s is valid"%(self._want_to_close,str(self.persondata)))
        for k in self.model.keys():
            if k == 'note': continue # allow note to be null
            if self.model[k] == None or self.model[k] == '':
                return({'valid':False,'msg':'bad %s'%k})
        # TODO: check dob is not today
        self._want_to_close = True
        return({'valid':True,'msg':'OK'})
    
        

if __name__ == "__main__":
    import lncdSql, sys

    # fake settings
    pid=0
    fullname="FAKE FAKE"
    study='CogR01' #TODO update
    vtype='Scan'
    RA="fakeRA"

    # db data
    sql = lncdSql.lncdSql() # need ~/.pgpass
    all_tasks = sql.query.all_tasks() 
    study_tasks = [ x[0] for x in sql.query.list_tasks_of_study_vtype(study=study,vtype=vtype) ]

    # app
    app= QtWidgets.QApplication(sys.argv)
    window = CheckinVisitWindow()

    # setup and show
    window.set_all_tasks(all_tasks)
    window.setup(pid,fullname,RA,study,study_tasks)
    window.show()

    sys.exit(app.exec_())
