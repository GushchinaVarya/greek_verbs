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

c.execute("""UPDATE past SET hint = 'используйте глагол αγοράζω'
WHERE
question = 'я купил' """)

c.execute("""UPDATE past SET hint = 'используйте глагол διαβάζω'
WHERE
question = 'он прочитал' """)

c.execute("""UPDATE past SET question = 'ты положил'
WHERE
answer = 'εσύ έβαλες' """)

c.execute("""UPDATE past SET question = 'вы положили'
WHERE
answer = 'εσείς βάλατε' """)

c.execute("""UPDATE past SET hint = 'используйте глагол αποφασίζω'
WHERE
question = 'мы решили' """)

c.execute("""UPDATE past SET hint = 'используйте глагол βάζω' 
WHERE 
question = 'я положил' OR
question = 'он положил' OR
question = 'она положила' OR
question = 'они положили' OR
question = 'вы положили' OR
question = 'ты положил' OR
question = 'мы положили' OR
question = 'оно положило' """)

c.execute("""UPDATE past SET hint = 'используйте глагол βγάζω' 
WHERE 
question = 'я удалил/достал' OR
question = 'он удалил/достал' OR
question = 'она удалила/достала' OR
question = 'они удалили/достали' OR
question = 'вы удалили/достали' OR
question = 'ты удалил/достал' OR
question = 'мы удалили/достали' OR
question = 'оно удалило/достало' """)

c.execute("""UPDATE past SET hint = 'используйте глагол δίνω' 
WHERE 
question = 'я дал' OR
question = 'он дал' OR
question = 'она дала' OR
question = 'они дали' OR
question = 'вы дали' OR
question = 'ты дал' OR
question = 'мы дали' OR
question = 'оно дало' """)

c.execute("""UPDATE present SET hint = 'используйте глагол πίνω' 
WHERE 
question = 'я пью' OR
question = 'он пьет' OR
question = 'она пьет' OR
question = 'они пьют' OR
question = 'вы пьете' OR
question = 'ты пьешь' OR
question = 'мы пьем' OR
question = 'оно пьет' """)

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
for el in items:
    print(el[0], el[1], '->', el[2], '   ', el[3])


#c.execute("SELECT rowid, question, answer, comment from present WHERE question == 'я слушаю' ")
c.execute("SELECT rowid, question, answer, comment from present")
#print (c.fetchall())
#print (c.fetchmany(1))
#print (c.fetchone())
items = c.fetchall()
for el in items:
    print(el[0], el[1], '->', el[2], '   ', el[3])


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
print(df)
c.execute("SELECT rowid, question, answer, comment from past ORDER BY rowid")
items = c.fetchall()
for el in items:
    print(el[0], el[1], '->', el[2], '   ', el[3])
    df = pd.concat([df, pd.DataFrame({'question':[el[1]], 'answer':[el[2]], 'comment':[el[3]]})])
    print(df)

df = df.reset_index(drop=True)
print(df)
print('_'.join(str(datetime.datetime.now()).split(' ')))
db.commit()



db.close()