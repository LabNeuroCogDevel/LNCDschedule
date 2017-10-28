import datetime
from PyQt5 import QtWidgets

# get combobox value
def comboval(cb):
    return(cb.itemText(cb.currentIndex()))

# get date from qdate widge 
def caltodate(qdate_widget):
    ordinal = qdate_widget.selectedDate().toPyDate().toordinal()
    dt=datetime.datetime.fromordinal(ordinal)
    return(dt)

# used in is_valid. does key match string or all
def isOrAll(k,s): return(k in [s, 'all'])


# used for visit, contact, notes, and all_tasks_table in checkin
def generic_fill_table(table,res):
    table.setRowCount(len(res))
    for row_i,row in enumerate(res):
        for col_i,value in enumerate(row):
            item=QtWidgets.QTableWidgetItem(str(value))
            table.setItem(row_i,col_i,item)
