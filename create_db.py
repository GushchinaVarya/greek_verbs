import sqlite3
import pandas as pd
import datetime
import numpy as np

db = sqlite3.connect('greek_db_all.db')

c = db.cursor()

#c.execute(""" CREATE TABLE future (
#    question TEXT NOT NULL,
#    answer TEXT NOT NULL,
#    comment TEXT
#)""")

#c.execute(""" CREATE TABLE past (
#    question TEXT NOT NULL,
#    answer TEXT NOT NULL,
#    comment TEXT
#)""")

#c.execute(""" CREATE TABLE present (
#    question TEXT NOT NULL,
#    answer TEXT NOT NULL,
#    comment TEXT
#)""")

#c.execute(""" CREATE TABLE imperative (
#    question TEXT NOT NULL,
#    answer TEXT NOT NULL,
#    comment TEXT
#)""")

#c.execute("INSERT INTO future VALUES ('я куплю', 'εγώ Θα αγοράσω', 'правильный глагол')")
#c.execute("INSERT INTO future VALUES ('он прочитает', 'αυτός Θα διαβάσει', 'правильный глагол')")
#c.execute("INSERT INTO future VALUES ('мы решим', 'εμείς Θα αποφασίσουμε', 'правильный глагол')")

#c.execute("INSERT INTO past VALUES ('я купил', 'εγώ αγόρασα', 'правильный глагол')")
#c.execute("INSERT INTO past VALUES ('он прочитал', 'αυτός διάβασε', 'правильный глагол')")
#c.execute("INSERT INTO past VALUES ('мы решили', 'εμείς αποφασίσαμε', 'правильный глагол')")

#c.execute("INSERT INTO imperative VALUES ('не покупайте', 'μην αγοράσετε', 'правильный глагол')")
#c.execute("INSERT INTO imperative VALUES ('читай', 'διάβασις', 'правильный глагол')")
#c.execute("INSERT INTO imperative VALUES ('решите', 'αποφασίστε', 'правильный глагол')")

#c.execute("INSERT INTO present VALUES ('мы покупаем', 'εμείς αγοράζουμε', 'правильный глагол')")
#c.execute("INSERT INTO present VALUES ('она читает', 'αυτή διαβάζει', 'правильный глагол')")
#c.execute("INSERT INTO present VALUES ('оно решает', 'αυτό αποφασίζει', 'правильный глагол')")

#c.execute("DELETE FROM present WHERE rowid = 21")

#c.execute("""ALTER TABLE present
#ADD hint TEXT DEFAULT 'используйте глагол αγοράζω' ;""")

#c.execute("""ALTER TABLE past
#ADD hint TEXT DEFAULT 'используйте глагол έρχομαι' ;""")

#c.execute("""ALTER TABLE future
#ADD hint TEXT DEFAULT 'используйте глагол αγοράζω' ;""")

#c.execute("UPDATE present SET comment = 'глагол типа α' WHERE question = 'он живет' OR question = 'они живут' OR question = 'мы живем' OR question = 'вы живете' OR question = 'ты живешь'")

#c.execute("""UPDATE present SET hint = 'используйте глагол διαβάζω αποφασίζω πηγαίνω μένω έρχομαι'
#WHERE
#question = 'она читает' """)




c.execute(f"SELECT rowid from present ")
items = c.fetchall()
b = np.array(items)
b = b.reshape(b.shape[0])
rowid_rand = np.random.choice(b)


#c.execute("SELECT rowid, question, answer from future WHERE rowid <> 5 ORDER BY rowid DESC")
#c.execute("SELECT rowid, question, answer, comment from present WHERE rowid == 15")
c.execute("SELECT  ROW_NUMBER() OVER (ORDER BY rowid) rowid, question, answer, comment FROM present;")
#c.execute("SELECT rowid, question, answer, comment from present WHERE question == 'я слушаю' ")
#c.execute("SELECT * from future")
#print (c.fetchall())
#print (c.fetchmany(1))
#print (c.fetchone())
items = c.fetchall()
#for el in items:
    #print(el[0], el[1], '->', el[2], '   ', el[3])


#c.execute("SELECT rowid, question, answer, comment from present WHERE question == 'я слушаю' ")
c.execute("SELECT rowid, question, answer, comment from present")
#print (c.fetchall())
#print (c.fetchmany(1))
#print (c.fetchone())
items = c.fetchall()
#for el in items:
#    print(el[0], el[1], '->', el[2], '   ', el[3])


c.execute("SELECT COUNT(*) FROM future")
(res,) = c.fetchone()
print(res)

qu = 'мы решим'
an = 'εμείς Θα αποφασίσουμε'
print(qu.lower(), an.lower())
c.execute("SELECT rowid, question, answer from future WHERE question = ? AND answer = ?", (qu, an, ))
items = c.fetchall()
for el in items:
    print(el[0], el[1], '->', el[2])

c.execute("SELECT COUNT(*) FROM future WHERE question = ? AND answer = ?", (qu, an, ))
(res,) = c.fetchone()
print(res)

print(' ')
print ('test form exel')
df = pd.DataFrame({'question':[], 'answer':[], 'comment':[]})
#print(df)
c.execute("SELECT rowid, question, answer, comment from past ORDER BY rowid")
items = c.fetchall()
for el in items:
    #print(el[0], el[1], '->', el[2], '   ', el[3])
    df = pd.concat([df, pd.DataFrame({'question':[el[1]], 'answer':[el[2]], 'comment':[el[3]]})])
    #print(df)

df = df.reset_index(drop=True)
print(df)
print('_'.join(str(datetime.datetime.now()).split(' ')))
db.commit()

db.close()


db = sqlite3.connect('users_all.db')

c = db.cursor()
#c.execute(""" CREATE TABLE users (
#    chat_id BIGINT NOT NULL PRIMARY KEY,
#    name TEXT
#)""")

#c.execute("INSERT INTO users VALUES (555, 'noname')")
#c.execute("DELETE FROM users WHERE rowid = 1")
c.execute("SELECT rowid, chat_id, name from users")
items = c.fetchall()
for el in items:
    print(el[0], el[1], el[2])
c.execute("SELECT COUNT(chat_id) FROM users")
items = c.fetchall()
print(items[0][0])

db.commit()
db.close()