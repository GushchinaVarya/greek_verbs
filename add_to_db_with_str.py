import sqlite3
import pandas as pd
import datetime
import numpy as np
from config import DB_NAME
import sys

tablename = 'future'
q = 'они купят, они подготовят, они заплатят, они прибудут, они оставят, они прочитают, они откроют, они будут внимательны, они поищут, они побегут, они напишут, они приготовят, они поработают, они разрежут, они поговорят, они спросят, они ответят, они проснутся, они позвонят'
a = 'θα αγοράσουν, θα ετοιμάσουν, θα πληρώσουν, θα φτάσουν, θα αφήσουν, θα διαβάσουν, θα ανοίξουν, θα προσέξουν, θα ψάξουν, θα τρέξουν, θα γράψουν, θα μαγειρέψουν, θα δουλέψουν, θα κόψουν, θα μιλήσουν, θα ρωτήσουν, θα απαντήσουν, θα ξυπνήσουν, θα τηλεφωνήσουν'
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