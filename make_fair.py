import sqlite3

from util import nios2_as
from exercises import Exercises

db = sqlite3.connect('leaderboard.db')

rows = db.execute('SELECT user,timestamp,code,instructions FROM leaders')

for row in rows:
    user,ts,code,instrs = row

    print('User %s, ts %d, instrs %d' % (user,ts, instrs))

    ex = Exercises.getExercise('sort-fn-contest')
    success, feedback, instrs = ex['checker'](code)

    print('  updated to %d' % (instrs))

    if not(success):
        continue

    db.execute('UPDATE leaders SET instructions=? WHERE user=? AND timestamp=?', (instrs, user, ts))

db.commit()
