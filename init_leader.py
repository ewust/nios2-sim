import sqlite3
db = sqlite3.connect('leaderboard.db')


db.execute("CREATE TABLE leaders (id INTEGER PRIMARY KEY AUTOINCREMENT, user char(10) NOT NULL, timestamp INTEGER, code BLOB, instructions INTEGER, size INTEGER, public bool NOT NULL)")
db.commit()
