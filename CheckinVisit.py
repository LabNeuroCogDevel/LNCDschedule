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
        self.search_edit.textChanged.connect(self.all_task_disp)

        ## add if selected in all tasks (and not already there)
        self.all_tasks_table.itemClicked.connect(self.move_from_all)
        self.tasks_list.itemClicked.connect(self.remove_task)

        ## stop from closing if things are not okay
        #self.buttonBox.clicked.connect(self.isvalid)

    # NOTE: okay button can only be pressed once, enter still works
    @QtCore.pyqtSlot()
    def accept(self):
        #QtWidgets.QApplication.focusWidget().clearFocus()
        check = self.isvalid()
        if check['valid']:
          self.done(QtWidgets.QDialog.Accepted)
        else:
          mkmsg('not all checkin data is valid:\n%s'%check['msg'])
        return(QtWidgets.QDialog.Accepted)

    def move_from_all(self,item):
        rowi=self.all_tasks_table.row(item)
        addtask=self.all_tasks_table.item(rowi,0).text()
        addtask_studies=self.all_tasks_table.item(rowi,1).text().split(' ')
        print("add %s"%addtask)

        self.allvals('tasks') # update model['tasks']
        nextpos=self.tasks_list.count()
        if addtask not in self.model['tasks']:
            self.tasks_list.addItem(addtask)
            if not self.study in addtask_studies:
              self.tasks_list.item(nextpos).setBackground(QtGui.QColor('red'))
        # update all tasks display (colors)
        self.all_task_disp()
        self.all_tasks_table.clearSelection()
    def remove_task(self,item):
        print("remove task %s"%item.text())
        rowi=self.tasks_list.row(item)
        self.tasks_list.takeItem(rowi)
        # update all tasks display (colors)
        self.all_task_disp()
        self.tasks_list.clearSelection()

        
    def set_all_tasks(self,all_tasks):
        self.all_tasks_data = all_tasks
        generic_fill_table(self.all_tasks_table,self.all_tasks_data)

    def setup(self,pid,name,RA,study,vtype,study_tasks):
        print('updating checkin with %s and %s'%(pid,name))
        self.model['pid'] = pid
        self.model['ra']  = RA
        self.who_label.setText(name)
        self.tasks_list.insertItems(0,study_tasks)
        self.study = study
        self.vtype = vtype
        self.all_task_disp()

    def all_task_disp(self):
        # subset data on search
        searchstr=self.search_edit.text().lower()
        if searchstr in ['','%']:
          data=self.all_tasks_data
        else:
          data= [ x for x in self.all_tasks_data if searchstr in  " ".join(x).lower() ] 

        # sort all task data relative to study and visit type
        data = sorted(data, key=lambda x: 
          (self.study in x[1].split(' '),
           self.vtype in x[2].split(' '),
           x[0]
        ),reverse=True)

        # re-populate
        generic_fill_table(self.all_tasks_table,data)

        # color 
        self.allvals('tasks') # update self.model['tasks']
        for rowi in range(0,self.all_tasks_table.rowCount()):
            tblitem   = self.all_tasks_table.item(rowi,0).text()
            tblstudy  = self.all_tasks_table.item(rowi,1).text()
            tbltype   = self.all_tasks_table.item(rowi,2).text()
            # blue if expected, red if not in selected tasks, but is in study
            if tblitem in self.model['tasks']:
              self.all_tasks_table.item(rowi,0).setBackground(QtGui.QColor('blue'))
            elif tblstudy == self.study:
              self.all_tasks_table.item(rowi,0).setBackground(QtGui.QColor('orange'))

             
            #if self.all_tasks_table.
    """
    set data from gui edit value
    optionally be specific
    """
    def allvals(self,key='all'):
        print('checkin visit: updating %s'%key)
        if(isOrAll(key,'lunaid')):     self.model['lunaid'] = self.lunaid_edit.text()
        if(isOrAll(key,'vscore')):    self.model['vscore']  = self.vscore_spin.value()
        if(isOrAll(key,'note')):       self.model['note']   = self.note_edit.toPlainText()
        if(isOrAll(key,'tasks')):       self.model['tasks']   = [ self.tasks_list.item(i).text() for i in range(self.tasks_list.count() ) ]
        # todo collected

        
    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("checkin visit is valid?\n%s"%str(self.model))
        for k in self.model.keys():
            if k == 'note': continue # allow note to be null
            if self.model[k] == None or self.model[k] == '' or self.model[k] == []:
                return({'valid':False,'msg':'bad %s'%k})
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
    try:
        sql = lncdSql.lncdSql() # need ~/.pgpass
        all_tasks = sql.query.all_tasks() 
        study_tasks = [ x[0] for x in sql.query.list_tasks_of_study_vtype(study=study,vtype=vtype) ]
    except Exception as e:
        print(e) 
        print('no db, using fake data')
        # taskname studies modes
        all_tasks = [
         ('rest','RewardR21 RewardR01 PET BrainMech P5','Scan'),
         ('anti','CogR01','Behavioral'),
         ('RIST','CogR01','Questioneer'),
         ('WASI','RewardR21','Questioneer'),
        ]
        study_tasks = ['RIST','WASI' ]

    # app
    app= QtWidgets.QApplication(sys.argv)
    window = CheckinVisitWindow()

    # setup and show
    window.set_all_tasks(all_tasks)
    window.setup(pid,fullname,RA,study,vtype,study_tasks)
    window.show()

    sys.exit(app.exec_())
