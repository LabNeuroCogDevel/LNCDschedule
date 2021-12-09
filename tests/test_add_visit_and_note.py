"""
add visit (and note). see that gui updates
"""

import datetime
import sys
from PyQt5.QtWidgets import QApplication


# initialize QT
# APP = QApplication(sys.argv)


def test_gui_add_visit(qtbot, lncdapp):
    """
    test schedule visit
    - can add a visit (with notes)
    - can selected added visit (gui updates)
    - schedule button becomes 'reschedule' when visit selected
    """

    # remove isvalid check (which updates vtype with box value)
    lncdapp.ScheduleVisit.isvalid = lambda: {"valid": True, "msg": "OK"}

    # attach tester to window
    qtbot.add_widget(lncdapp)
    # search by name - defined in person.csv and matching note.csv
    lncdapp.PromotedPersonTable.fullname.setText("NoNotes Subj")
    # select the first row in the table
    index = lncdapp.PromotedPersonTable.people_table.model().index(0, 1)
    lncdapp.PromotedPersonTable.people_table.setCurrentIndex(index)

    assert lncdapp.schedule_button.text() == "Schedule"

    # fake updating the visit model
    current_person = lncdapp.PromotedPersonTable.current_person()
    pid = current_person["pid"]
    now = datetime.datetime.now()
    lncdapp.ScheduleVisit.model = {
        "vtimestamp": now,
        "study": "AStudy",
        "vtype": "Scan",
        "visitno": 1,
        "ra": "ra1",
        "pid": pid,
        "cohort": "control",
        "dur_hr": 2,
        "notes": None,
    }

    # add notes using gui code
    lncdapp.ScheduleVisit.note_edit.setText("visit_summary Test Note")
    lncdapp.ScheduleVisit.allvals("notes")
    # TODO: set text for all gui items and run isvalid instead

    lncdapp.schedule_to_db()

    # success adding?
    assert (
        lncdapp.pgtest.connection.execute(
            "with maxvid as (select max(vid) as vid from visit) \
            select vtimestamp from visit join maxvid mv on visit.vid = mv.vid"
        ).scalar()
        == now
    )

    # qtbot.stop()  # to check out whats going on in the gui
    # and in the visits table
    index = lncdapp.visit_table.model().index(0, 1)
    lncdapp.visit_table.setCurrentIndex(index)
    assert lncdapp.visit_table.item(0, lncdapp.visit_columns.index("vid")).text() == "1"
    # update button text
    assert lncdapp.schedule_button.text() == "Reschedule"

    # note in note table
    newest_note_idx = lncdapp.note_table.rowCount() - 1
    note_col = lncdapp.note_columns.index("note")  # first column

    # dont need to jump there
    # but if we're debugging, nice to see what value is being pulled
    index = lncdapp.note_table.model().index(newest_note_idx, note_col)
    lncdapp.note_table.setCurrentIndex(index)

    assert (
        lncdapp.note_table.item(newest_note_idx, note_col).text()
        == "visit_summary Test Note"
    )
