import sqlite3
import pandas as pd
import datetime
import numpy as np
from config import DB_NAME
import sys

tablename = 'future'
q = 'я куплю, я подготовлю, я заплачу, я прибуду, я оставлю, я прочитаю, я открою, я буду внимателен, я поищу, я побегу, я напишу, я приготовлю, я поработаю, я разрежу, я поговорю, я спрошу, я отвечу, я проснусь, я позвоню'
a = 'θα αγοράσω, θα ετοιμάσω, θα πληρώσω, θα φτάσω, θα αφήσω, θα διαβάσω, θα ανοίξω, θα προσέξω, θα ψάξω, θα τρέξω, θα γράψω, θα μαγειρέψω, θα δουλέψω, θα κόψω, θα μιλήσω, θα ρωτήσω, θα απαντήσω, θα ξυπνήσω, θα τηλεφωνήσω'
co = 'правильный глагол'
h = 'αγοράζω, ετοιμάζω, πληρώνω, φτάνω, αφήνω, διαβάζω, ανοίγω, προσέχω, ψάχνω, τρέχω, γράφω, μαγειρεύω, δουλεύω, κόβω, μιλάω, ρωτάω, απαντάω, ξυπνάω, τηλεφωνώ'


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