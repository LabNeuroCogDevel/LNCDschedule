from datetime import datetime
import psycopg2
from PyQt5 import uic, QtWidgets
import PasswordDialog
from LNCDutils import (mkmsg, make_connstr, catch_to_mkmsg)


class AddRAWindow(QtWidgets.QDialog):
    """
    This class provides a window for adding an RA
    """

    def __init__(self, parent=None):
        super(AddRAWindow, self).__init__(parent)
        self.ra_data = {}
        uic.loadUi('./ui/add_ra.ui', self)
        self.setWindowTitle('Add RA')

        self.ra_text.textChanged.connect(self.ra)
        self.abbr_text.textChanged.connect(self.abbr)
        self.ra_data['start_date'] = datetime.now()

    def ra(self):
        """update ra field"""
        self.ra_data['ra'] = self.ra_text.text()

    def abbr(self):
        """update abbr field"""
        self.ra_data['abbr'] = self.abbr_text.text()

    def add_user_sql(self, lncdsql):
        """
        @param lncdsql is an lncdSql object (used to get connection string)
        @return True/False added
        try to get
        """
        add_user = """
        create role %(ra)s with LOGIN REPLICATION password NULL;
        GRANT ALL PRIVILEGES ON DATABASE lncddb TO %(ra)s;
        grant all privileges on all tables in schema public to %(ra)s;
        grant all privileges on all functions in schema public to %(ra)s;
        grant all privileges on all sequences in schema public to %(ra)s;
        """ % self.ra_data

        admin_user = 'postgres'
        user_pass = PasswordDialog.user_pass(QtWidgets.QApplication.instance(),
                                             admin_user)
        if not user_pass['pass']:
            mkmsg('get admin to run\n\n %s' % add_user)
            return
        constr = {**lncdsql.config,
                  'user': admin_user,
                  'password': user_pass['pass']}
        dbcon = make_connstr(constr)
        conn = psycopg2.connect(constr)
        conn.set_session(autocommit=True)
        didadd = catch_to_mkmsg(conn.execute, add_user)
        # TODO: cache admin password?
        conn.close()
        return(didadd)
