import sqlite3
import pandas as pd
import numpy as np
from config import DB_NAME
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
    df = pd.DataFrame({'question': [], 'answer': [], 'comment': []})
    c.execute(f"SELECT rowid, question, answer, comment from {tablename} ORDER BY rowid")
    items = c.fetchall()
    for el in items:
        df = pd.concat([df, pd.DataFrame({'question': [el[1]], 'answer': [el[2]], 'comment': [el[3]]})])

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
    c.execute(f"SELECT rowid, question, answer, comment from {tablename} WHERE question = ? ", (question,))
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

"""
    db.commit()
    db.close()
    return text, delete_option

def write_to_table(table, question, answer, comment):
    tablename = get_tablename(table)
    db = sqlite3.connect(DB_NAME)
    c = db.cursor()
    c.execute(f"SELECT rowid, question, answer, comment from {tablename} WHERE question == '{question}' ")
    items = c.fetchall()
    if len(items) == 0:
        deleted = 0
    else:
        deleted = 1
        c.execute(f"DELETE FROM {tablename} WHERE question == '{question}' ")
    c.execute(f"INSERT INTO {tablename} VALUES ('{question}', '{answer}', '{comment}')")

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
    c.execute(f"SELECT question, answer, comment from {tablename} WHERE rowid == '{rowid_rand}' ")
    items = c.fetchall()
    el = items[0]
    text = f"""
переведите на греческий *{el[0]}*
||ОТВЕТ: {el[1]}||
||КОММЕНТАРИЙ: {el[2]}||
    """
    db.commit()
    db.close()
    return text