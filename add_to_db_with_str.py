import sqlite3
import pandas as pd
import datetime
import numpy as np
from config import DB_NAME
import sys

tablename = 'imperative'
q = 'не послушай, не оставь, не подготовь, не убери, не поиграй, не открой, не будь внимателен, не поищи, не разожги, не путешествуй, не напиши'
a = 'μην ακούσεις, μην αφήσεις, μην ετοιμάσεις, μην καθαρίσεις, μην παίξεις, μην ανοίξεις, μην προσέξεις, μην ψάξεις, μην ανάψεις, μην ταξιδέψεις, μην γράψεις'
co = 'правильный глагол'
h = 'ακούω, αφήνω, ετοιμάζω, καθαρίζω, παίζω, ανοίγω, προσέχω, ψάχνω, ανάβω, ταξιδεύω, γράφω'

def makedf(q, a, co, h):
    q = q.split(',')
    q = [i.strip().lower() for i in q]

    a = a.split(',')
    a = [i.strip().lower() for i in a]

    h = h.split(',')
    h = ['используйте глагол ' + i.strip().lower() for i in h]

    df = pd.DataFrame({'question': q, 'answer': a, 'hint': h})
    df['comment'] = co
    return df


db = sqlite3.connect(DB_NAME)
c = db.cursor()
print(sys.argv[0])


df = makedf(q, a, co, h)
print(df.head())
for i in range(df.shape[0]):
    c.execute(f"INSERT INTO {tablename} VALUES ('{df.iloc[i]['question']}', '{df.iloc[i]['answer']}', '{df.iloc[i]['comment']}', '{df.iloc[i]['hint']}')")


db.commit()
db.close()