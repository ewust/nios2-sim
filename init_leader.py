import sqlite3
import sqlite3, csv

db = sqlite3.connect('leaderboard.db')
cur = db.cursor()

# Make users table
cur.execute("CREATE TABLE IF NOT EXISTS users (user char(10))")

# Populate it
with open("users.csv", newline="") as f:
    for row in csv.reader(f):
        cur.execute("INSERT INTO users (user) VALUES (?)", (row[0],))


cur.execute("CREATE TABLE IF NOT EXISTS leaders (id INTEGER PRIMARY KEY AUTOINCREMENT, user char(10) NOT NULL, ip TEXT, timestamp INTEGER, code BLOB, instructions INTEGER, size INTEGER, time_us INTEGER, public bool NOT NULL)")


db.commit()
db.close()
