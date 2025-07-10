import sqlite3
import pandas as pd
import datetime
import numpy as np
from config import DB_NAME
import sys

tablename = sys.argv[1]
csvfile = sys.argv[2]
db = sqlite3.connect(DB_NAME)
c = db.cursor()
print(sys.argv[0], sys.argv[1], sys.argv[2])

#c.execute(""" CREATE TABLE future (
#    question TEXT NOT NULL,
#    answer TEXT NOT NULL,
#    comment TEXT,
#    hint TEXT
#)""")
#c.execute("INSERT INTO future VALUES ('я куплю', 'εγώ Θα αγοράσω', 'глагод типа α', 'используйте глагол αγοράσω')")
#c.execute("SELECT rowid, question, answer, comment, hint from future")
#items = c.fetchall()
#for el in items:
#    print(el[0], el[1], '->', el[2], '   ', el[3], el[4])

#c.execute("SELECT  ROW_NUMBER() OVER (ORDER BY rowid) rowid, question, answer, comment, hint comment FROM future;")
#items = c.fetchall()
#for el in items:
#    print(el[0], el[1], '->', el[2], '   ', el[3], el[4])

df = pd.read_csv(sys.argv[2], index_col=0)
print(df.head())
for i in range(df.shape[0]):
    c.execute(f"INSERT INTO {tablename} VALUES ('{df.iloc[i]['question']}', '{df.iloc[i]['answer']}', '{df.iloc[i]['comment']}', '{df.iloc[i]['hint']}')")


db.commit()
db.close()