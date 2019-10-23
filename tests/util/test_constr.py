from LNCDutils import make_connstr, db_config_to_dict


def test_make_connstr():
    """test connection string generated by dictionary. this is probably pointless"""
    defdb = {'dbname': 'db', 'host': 'h', 'user': 'uname'}
    assert make_connstr(defdb) == \
        'dbname=db user=uname host=h'
    assert make_connstr({**defdb, 'password': "pwd"}) ==\
        'dbname=db user=uname host=h password=pwd'
    assert make_connstr({**defdb, 'password': "pwd", 'port': "12"}) ==\
        'dbname=db user=uname host=h port=12 password=pwd'
    assert make_connstr({**defdb, 'port': "12"}) ==\
        'dbname=db user=uname host=h port=12'


def test_db_config_to_dict():
    """test reading in from config file: use example"""
    cfg = 'config.ini.example'
    # [SQL]
    # host    = localhost
    # dbname  = db
    # user    = uname
    # port = 5432
    assert make_connstr(db_config_to_dict(cfg)) == \
        'dbname=db user=uname host=localhost port=5432'


def test_db_config_to_dict_getuname(monkeypatch):
    """test updating when no username given. monkeypatch gui portion"""
    defdb = {'dbname': 'db', 'host': 'h'}
    monkeypatch.setattr('LNCDutils.PasswordDialog.user_pass',
                        lambda *x: {'user': 'a', 'pass': 'b'})
    assert make_connstr(db_config_to_dict(defdb, True)) == \
        'dbname=db user=a host=h password=b'