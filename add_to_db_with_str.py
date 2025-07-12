import sqlite3
import pandas as pd
import datetime
import numpy as np
from config import DB_NAME
import sys

tablename = 'imperative'
q = 'положите, вытащите, дайте, принесите, возьмите, отправьте, поешьте, посмотрите, найдите, скажите, попейте, выйдите, войдите, сделайте, изучите, подождите, пойдите, уйдите, помойте, придите, сядьте'
a = 'βάλτε, βγάλτε, δώστε, φέρτε, πάρτε, στείλτε, φάτε, δείτε, βρείτε, πείτε, πιείτε, βγείτε, μπείτε, κάντε, μάθετε, περιμένετε, πηγαίνετε, φύγετε, πλύνετε, ελάτε, καθίστε'
co = 'неправильный глагол, завершенная форма'
h = 'βάζω, βγάζω, δίνω, φέρνω, παίρνω, στέλνω, τρώω, βλέπω, βρίσκω, λέω, πίνω, βγαίνω, μπαίνω, κάνω, μαθαίνω, περιμένω, πηγαίνω, φεύγω, πλένω, έρχομαι, κάθομαι'

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