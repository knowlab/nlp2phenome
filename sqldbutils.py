import utils as imutil
import pyodbc
import logging
import mysql.connector
from mysql.connector import pooling


def get_db_connection_by_setting(setting_file=None, setting_obj=None):
    if setting_file is not None:
        settings = imutil.load_json_data(setting_file)
    else:
        settings = setting_obj
    if 'db_type' in settings and settings['db_type'] == 'mysql':
        return get_mysqldb_host_connection(settings['server'],
                                      settings['user'],
                                      settings['password'],
                                      settings['database'])

    if 'trusted_connection' in settings:
        con_string = 'driver=%s;server=%s;trusted_connection=yes;DATABASE=%s;' % (settings['driver'],
                                                                         settings['server'],
                                                                         settings['database'])
    elif 'dsn' in settings:
        con_string = 'DSN=%s;UID=%s;PWD=%s;DATABASE=%s;' % (settings['dsn'],
                                                            settings['user'],
                                                            settings['password'],
                                                            settings['database'])
    else:
        con_string = 'driver=%s;server=%s;UID=%s;PWD=%s;DATABASE=%s;' % (settings['driver'],
                                                                         settings['server'],
                                                                         settings['user'],
                                                                         settings['password'],
                                                                         settings['database'])
    # print pyodbc.drivers()
    cnxn = pyodbc.connect(con_string)
    cursor = cnxn.cursor()
    return {'cnxn': cnxn, 'cursor': cursor}


def get_mysqldb_host_connection(my_host, my_user, my_pwd, my_db, mysql_lib='official'):
    db = mysql.connector.connect(host=my_host,  # your host, usually localhost
                                 user=my_user,  # your username
                                 passwd=my_pwd, # your password
                                 db=my_db,      # name of the data base
                                 use_unicode=True,
                                 charset='utf8')
    db.set_character_set('utf8')
    cursor = db.cursor()
    return {'cnxn': db, 'cursor': cursor}


def get_mysql_pooling(settings, num):
    dbconfig = {
        "host": settings['server'],
        "user": settings['user'],
        "password": settings['password'],
        "database": settings['database']
    }
    return mysql.connector.pooling.MySQLConnectionPool(pool_name = "mypool",
                                                       pool_size = num,
                                                       **dbconfig)


def release_db_connection(cnn_obj):
    cnn_obj['cnxn'].close()
    #cnn_obj['cursor'].close()
    #cnn_obj['cnxn'].disconnect()


def query_data(query, container=None, dbconn=None, pool=None):
    if pool is not None:
        cnn = pool.get_connection()
        conn_dic = {'cnxn': cnn, 'cursor': cnn.cursor()}
    else:
        conn_dic = dbconn
    try:
        conn_dic['cursor'].execute(query)
        if container is not None:
            rows = conn_dic['cursor'].fetchall()
            columns = [column[0] for column in conn_dic['cursor'].description]
            for row in rows:
                container.append(dict(zip(columns, row)))
        else:
            conn_dic['cnxn'].commit()
    except Exception as e:
        logging.error('error [%s] doing [%s]' % (e, query))
    finally:
        if dbconn is None:
            release_db_connection(conn_dic)


def escape_string(s):
    return s.replace("'", "''")