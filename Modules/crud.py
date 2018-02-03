import sqlite3
import os.path
# http://evilnapsis.com/2016/10/09/crud-con-python-y-sqlite/


def connect(func):
    def wrapper(*args):
        try:
            db_path = os.path.abspath(os.path.join(os.pardir, "i4_0", "src", "db.sqlite3"))
            con = sqlite3.connect(db_path)
        except sqlite3.OperationalError:
            db_path = os.path.abspath(os.path.join(os.pardir, os.pardir, "i4_0", "src", "db.sqlite3"))
            con = sqlite3.connect(db_path)
        cur = con.cursor()
        i = func(cur, *args)
        if i:
            con.close()
            return i
        else:
            con.commit()
            con.close()
    return wrapper


# @connect
# def create(cur):
#     contact = ('Agustin', 'Ramos', '9141183199', 'Tabasco, Mexico')
#     cur.execute("insert into principal_pintura (name,lastname,phone,address) values (?,?,?,?)", contact)


# @connect
# def read(cur):
#     for row in cur.execute('SELECT * FROM principal_pintura where'):
#         print(row)


@connect
def get_item(cur, mx):
    item = ('Espera', mx)
    cur.execute('SELECT id, servicio, tiempo, maquina FROM principal_pintura WHERE id = (SELECT min(id) FROM principal_pintura WHERE estado=? and maquina=?)', item)
    a = cur.fetchone()
    return a


@connect
def update(cur, *args):
    cur.execute("update principal_pintura set estado=? where id=?", args)
    return None


# @connect
# def delete(cur):
#     cur.execute("delete from person where id=?", 3)

# create table person(
#     id integer not null primary key,
#     name varchar(255),
#     lastname varchar(255),
#     phone varchar(255),
#     address varchar(255)
# )
