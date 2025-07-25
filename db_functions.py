import sqlite3
import pandas as pd
import numpy as np
from config import DB_NAME, DB_USERS_NAME
import datetime
from telegram import InlineKeyboardButton

def get_tablename(table):
    if table == "настоящее время":
        tablename = 'present'
    if table == "будущее время":
        tablename = 'future'
    if table == "прошедшее время":
        tablename = 'past'
    if table == "повелительное наклонение":
        tablename = 'imperative'
    return tablename

def generate_csv(table):
    tablename = get_tablename(table)
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    df = pd.DataFrame({'question': [], 'answer': [], 'comment': [], 'hint': []})
    c.execute(f"SELECT rowid, question, answer, comment, hint from {tablename} ORDER BY rowid")
    items = c.fetchall()
    for el in items:
        df = pd.concat([df, pd.DataFrame({'question': [el[1]], 'answer': [el[2]], 'comment': [el[3]], 'hint': [el[4]]})])

    df = df.reset_index(drop=True)
    df.index = df.index.values+1
    filename = 'tmp_db/'+tablename+'_'+'_'.join(str(datetime.datetime.now()).split(' '))+'.csv'
    df.to_csv(filename)

    db.commit()
    db.close()

    return filename, 1

def check_if_db_has_this(table, question):
    tablename = get_tablename(table)
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute(f"SELECT rowid, question, answer, comment, hint from {tablename} WHERE question = ? ", (question,))
    items = c.fetchall()
    how_many = len(items)
    if how_many == 0:
        text = ""
        delete_option = 0
    else:
        delete_option = 1
        text = """_B базе уже есть_
"""
        for el in items:
            text = text + f"""
ВОПРОС: {el[1]}
ОТВЕТ: {el[2]}
КОММЕНТАРИЙ: {el[3]}
ПОДСКАЗКА: {el[4]}

"""
    db.commit()
    db.close()
    return text, delete_option

def write_to_table(table, question, answer, comment, hint):
    tablename = get_tablename(table)
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute(f"SELECT rowid, question, answer, comment, hint from {tablename} WHERE question == '{question}' ")
    items = c.fetchall()
    if len(items) == 0:
        deleted = 0
    else:
        deleted = 1
        c.execute(f"DELETE FROM {tablename} WHERE question == '{question}' ")
    c.execute(f"INSERT INTO {tablename} VALUES ('{question}', '{answer}', '{comment}', '{hint}')")

    db.commit()
    db.close()
    return deleted

def get_question(table):
    tablename = get_tablename(table)
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute(f"SELECT rowid from {tablename} ")
    items = c.fetchall()
    b = np.array(items)
    b = b.reshape(b.shape[0])
    rowid_rand = np.random.choice(b)
    c.execute(f"SELECT question, answer, comment, hint from {tablename} WHERE rowid == '{rowid_rand}' ")
    items = c.fetchall()
    el = items[0]
    text_q = f"""
переведите на греческий 

*{el[0]}*
"""
    text_h = f"""ПОДСКАЗКА: ||{el[3]}||
        """
    text_a = f"""ОТВЕТ: ||{el[1]}||
КОММЕНТАРИЙ: ||{el[2]}||
    """
    db.commit()
    db.close()
    return text_q,text_h,text_a


def add_user(chat_id, name):
    db = sqlite3.connect(DB_USERS_NAME)
    c = db.cursor()
    c.execute(f"SELECT COUNT(chat_id) FROM users where chat_id = {chat_id}")
    items = c.fetchall()
    if items[0][0]==0:
        is_new = True
        c.execute(f"INSERT INTO users VALUES ({chat_id}, '{name}')")
    else:
        is_new = False
    db.commit()
    db.close()
    return is_new

def get_users():
    db = sqlite3.connect(DB_USERS_NAME)
    c = db.cursor()
    c.execute(f"SELECT chat_id, name FROM users")
    items = c.fetchall()
    ids = [int(el[0]) for el in items]
    names = [el[1] for el in items]
    db.commit()
    db.close()
    return ids, names
