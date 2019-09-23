from pyesql_helper import pyesql_helper as ph
from lncdSql import lncdSql

def test_db_multiRA_insertion(lncdapp):

	#Test the function of assing multi_RA
    fake_RA_selected = ['foranw', 'missarm', 'thompsonl12']
    vid = 0
    lncdapp.multira_to_db_operaiton(fake_RA_selected, vid)
    #Check whether the data is successfully inserted in the database

    ra_action = lncdapp.pgtest.\
        connection.execute('select ra,action from visit_action where vid = vid')

    print(ra_action)
    
    #Check if value in the dictionary
    for a in fake_RA_selected:
    	assert a in ra_action.values()
    








    

    
	