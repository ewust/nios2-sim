import sqlite3
import sys
import csv

db = sqlite3.connect('leaderboard.db')

db.execute('create table if not exists users (user varchar(10) PRIMARY KEY, name TEXT)')

with open(sys.argv[1], newline='') as csvfile:
    for row in csv.reader(csvfile):
        first_name, last_name, email, _ = row
        name = first_name + ' ' + last_name
        user = email.split('@')[0]
        db.execute('INSERT INTO users (user, name) VALUES (?, ?)', (user, name))

db.commit()
