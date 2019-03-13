from PyQt5 import uic,QtCore, QtWidgets,QtGui
from LNCDutils import  *
import json
import pprint

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
        data_columns=['vscore','note','lunaid','ra','vid','tasks']
        self.model = { k: None for k in data_columns }
        self.hasLuna = False

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

        self.test_button.clicked.connect(self.checkormsg )

        ## stop from closing if things are not okay
        #self.buttonBox.clicked.connect(self.isvalid)

    def checkormsg(self):
        check = self.isvalid()
        if not check['valid']:
          mkmsg('not all checkin data is valid:\n%s'%check['msg'])
        return(check['valid'])
        
    # NOTE: okay button can only be pressed once, enter still works
    @QtCore.pyqtSlot()
    def accept(self):
        #QtWidgets.QApplication.focusWidget().clearFocus()
        check = self.isvalid()
        if check['valid']:
          self.done(QtWidgets.QDialog.Accepted)
          return(QtWidgets.QDialog.Accepted)
        else:
          mkmsg('not all checkin data is valid:\n%s'%check['msg'])
          return(False)

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

        # checkin_what_data sends: pid,vid,fullname,study,vtype
        #self.CheckinVisit.setup(checkin_what_data,self.RA,study_tasks)
    def setup(self,d,RA,study_tasks):
        # d has keys: pid,vid,fullname,study,vtype
        print('updating checkin with %(pid)s(%(fullname)s) for %(study)s/%(vtype)s'%d)
        self.pid = d['pid']
        self.model['ra']  = RA
        self.model['vid'] = d['vid']
        self.who_label.setText("%s/%s: %s"%(d['study'],d['vtype'],d['fullname']))
        self.tasks_list.insertItems(0,study_tasks)
        self.study = d['study']
        self.vtype = d['vtype']
        self.all_task_disp()
        # dont set lunaid if we have one
        self.hasLuna = d.get('lunaid') != None
        if self.hasLuna:
            self.lunaid_edit.setText(str(d['lunaid']))
            self.lunaid_edit.setDisabled(True)
        elif d.get('nextluna') != None:
            self.lunaid_edit.setText(str(d['nextluna']))

    def all_task_disp(self):
        # subset data on search
        searchstr=self.search_edit.text().lower()
        if searchstr in ['','%']:
          data=self.all_tasks_data
        else:
          data= [ x for x in self.all_tasks_data if searchstr in  " ".join(x).lower() ] 

        # sort all task data relative to study and visit type
        data = sorted(data, key=lambda x: 
          (self.study not in x[1].split(' '),
           self.vtype not in x[2].replace('Questionnaire','Behavioral').split(' '),
           x[0]
          ),reverse=False)

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
        #print('checkin visit: updating %s'%key)
        if(isOrAll(key,'lunaid')): self.model['lunaid'] = self.lunaid_edit.text() 
        if(isOrAll(key,'vscore')): self.model['vscore'] = self.vscore_spin.value()
        if(isOrAll(key,'note')):   self.model['note']   = self.note_edit.toPlainText()
        if(isOrAll(key,'tasks')):  self.model['tasks']  = [ self.tasks_list.item(i).text() for i in range(self.tasks_list.count() ) ]

        # set note to none if empty string
        if self.model['note'] == '': self.model['note']  = None

        # if we already have a lunaid, set model to none
        # because we dont want to re-insert an ID in the db via visit_checkin_view triggers
        if self.hasLuna            : self.model['lunaid']= None

        
    """
    do we have good data? just check that no key is null
    return (valid:T/F,msg:....)
    """
    def isvalid(self):
        self.allvals('all')
        print("\ncheckin visit is valid?")
        pp=pprint.PrettyPrinter(indent=2)
        pp.pprint(self.model)
        for k in self.model.keys():
            if k == 'note': continue # allow note to be null
            if k == 'lunaid' and self.hasLuna: continue # allow note to be null
            if self.model[k] == None or self.model[k] == '' or self.model[k] == []:
                return({'valid':False,'msg':'bad %s'%k})
        return({'valid':True,'msg':'OK'})
    
        
    def checkin_to_db(self,sql):
       # use visit_checkin_view insert trigger to update the db:
       #   insert into visit_checkin_view (vid,ra,vscore,note,ids,tasks) values
       #   (3893,'testRA',4,'TEST CHECKINNOTE', 
       #    '[{"etype": "TestID", "id": "9"}, {"etype": "LunaID", "id": "9"}]'::jsonb,
       #    '["fMRIRestingState","SpatialWorkingMem","ScanSpit"]'::jsonb);
       #we have self.model:
       # {'vscore': 4.5, 'ra': 'fakeRA', 'note': 'test', 'lunaid': '99901', 'pid': 1182, 'tasks': ['Ant}
       # format data for insert
       d=self.model.copy()
       del d['lunaid']
       d['ids'] = json.dumps([{"etype":"LunaID", "id": "%s"%self.model['lunaid'] }])
       d['tasks'] = json.dumps(self.model['tasks'] )

       # lets see it
       print("\ninserting into visit_checkin_view:")
       pp=pprint.PrettyPrinter(indent=2)
       pp.pprint(d)

       # actually do it
       sql.insert('visit_checkin_view',d)
       


if __name__ == "__main__":
# usage:  python3 CheckinVisit.py 3952
    import lncdSql, sys

    # fake settings
    pid=0
    vid=0
    try: vid = int(sys.argv[1])
    except: pass
    fullname="FAKE FAKE"
    study='CogR01' #TODO update
    vtype='Scan'
    RA="fakeRA"
    lunaid=None

    # db data
    try:
        sql = lncdSql.lncdSql() # need ~/.pgpass
        v=sql.query.visit_by_vid(vid=vid)
        if(vid != 0 and len(v)>0):
            v=v[0]
            #pid,study,vtype, "action", vscore, age, note, to_char(vtimestamp,'YYYY-MM-DD') 
            pid=v[0]; study=v[1];vtype=v[2];
            fullname="%d-name"%vid
            p=sql.query.person_by_pid(pid=pid)
            p=p[0]
            lunaid=p[1]
            
        all_tasks = sql.query.all_tasks() 
        study_tasks = [ x[0] for x in sql.query.list_tasks_of_study_vtype(study=study,vtype=vtype) ]
    # we are just playing around
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

    window.accepted.connect(lambda : window.checkin_to_db(sql))
    # setup and show
    window.set_all_tasks(all_tasks)
    d={'pid': pid, 'vid': vid, 'fullname': fullname, 'study': study,'vtype':vtype,'lunaid':lunaid}
    window.setup(d,RA,study_tasks)
    window.show()

    sys.exit(app.exec_())
