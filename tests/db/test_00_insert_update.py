from pyesql_helper import pyesql_helper as ph
from lncdSql import lncdSql


def test_sqla_tblins(create_db):
    """ test with without lsql """
    import sqlalchemy as sqla
    lsql = lncdSql(None, conn=ph(create_db.connection))
    tbl = sqla.Table('contact', lsql.sqlmeta, autoload=True,
                     autoload_with=lsql.conn.connection)
    fake_contact = {'pid': 1, 'cid': 5,
                    'ctype': 'address', 'cvalue': 'nowhere',
                    'who': 'PersonPlaceThing', 'relation': 'None'}
    ins = tbl.insert(fake_contact)
    lsql.conn.execute(ins)


def test_lsql_tblinsert(create_db):
    """ test with with lsql """
    lsql = lncdSql(None, conn=ph(create_db.connection))
    fake_contact = {'pid': 2, 'cid': 6,
                    'ctype': 'address', 'cvalue': 'nowhere',
                    'who': 'PersonPlaceThing', 'relation': 'None'}
    lsql.insert('contact', fake_contact)
    nowhere = create_db.\
        connection.execute('select cvalue from contact where cid = 6').scalar()
    assert nowhere == 'nowhere'


def test_lsql_update(create_db):
    """ test with with lsql """
    lsql = lncdSql(None, conn=ph(create_db.connection))
    fake_contact = {'pid': 2, 'cid': 7,
                    'ctype': 'address', 'cvalue': 'nowhere',
                    'who': 'PersonPlaceThing', 'relation': 'None'}
    lsql.insert('contact', fake_contact)
    lsql.update(table_name='contact', new_column='cvalue', id_value=7,
                new_value='everywhere', id_column='cid')
    assert create_db.\
        connection.execute('select cvalue from contact where cid = 7').\
        scalar() == 'everywhere'


def test_lsql_update_dict(create_db):
    """ test updating with a dictionary """
    lsql = lncdSql(None, conn=ph(create_db.connection))
    fake_contact = {'pid': 2, 'cid': 7,
                    'ctype': 'address', 'cvalue': 'nowhere',
                    'who': 'PersonPlaceThing', 'relation': 'None'}
    lsql.insert('contact', fake_contact)
    lsql.update_columns(table_name='contact', id_column='cid', id_value=7,
                        update_dict={'cvalue': '555', 'ctype': 'phone'})
    assert create_db.\
        connection.execute('select cvalue from contact where cid = 7').\
        scalar() == '555'
    assert create_db.\
        connection.execute('select ctype from contact where cid = 7').\
        scalar() == 'phone'
    
