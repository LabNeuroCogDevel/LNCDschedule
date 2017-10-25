import datetime

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
