#!/usr/bin/env python
import sys, os, bottle
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from bottle import route, run, default_app, debug, template, request, get, post, jinja2_view, static_file, ext, jinja2_template, response
import json
import gc
from bs4 import BeautifulSoup
import bottle.ext.sqlite
import time
from datetime import datetime
import html

from util import nios2_as
from exercises import Exercises

from bottle import Jinja2Template

Jinja2Template.settings = {
'autoescape': True,
}



app = application = default_app()
plugin = ext.sqlite.Plugin(dbfile='./leaderboard.db')
app.install(plugin)


@post('/nios2/as')
@jinja2_view('as.html')
def post_as():
    asm = request.forms.get("asm")
    obj = nios2_as(asm.encode('utf-8'))

    if not(isinstance(obj, dict)):
        return {'prog': 'Error: %s' % obj,
                'success': False,
                'code': asm}

    return {'prog': json.dumps(obj),
            'success': True,
            'code': asm}

@get('/nios2/as')
@jinja2_view('as.html')
def get_as():
    return {}

@get('/nios2/examples/<eid>')
@jinja2_view('example.html')
def get_example(eid):
    gc.collect()

    ex = Exercises.getExercise(eid)
    if ex is None:
        return {'asm_error': 'Exercise ID not found'}

    return {'eid': eid,
            'exercise_title': ex['title'],
            'exercise_desc':  ex['desc'],
            'exercise_code':  ex['code'],
           }

@post('/nios2/examples/<eid>')
@jinja2_view('example.html')
def post_example(eid):
    gc.collect()
    asm = request.forms.get('asm')

    ex = Exercises.getExercise(eid)
    if ex is None:
        return {'asm_error': 'Exercise ID not found'}

    extra_info = ''
    res = ex['checker'](asm)
    if len(res) == 2:
        success, feedback = res
    elif len(res) == 3:
        success, feedback, extra_info = res

    if extra_info is None:
        extra_info = ''

    return {'eid': eid,
            'exercise_code': asm,
            'exercise_title': ex['title'],
            'exercise_desc':  ex['desc'],
            'feedback': feedback,
            'success': success,
            'extra_info': extra_info,
            }

@post('/nios2/examples.moodle/<eid>/<uid>')
def post_moodle(eid,uid):
    gc.collect()
    asm = request.forms.get('asm')
    #obj = nios2_as(asm.encode('utf-8'))

    ex = Exercises.getExercise(eid)
    if ex is None:
        return 'Exercise ID not found'

    # retry
    for retry in range(5):
        try:
            res = ex['checker'](asm)
            if len(res) == 2:
                success, feedback = res
            elif len(res) == 3:
                success, feedback, _ = res
            break
        except OSError as e:
            print('Retrying, got exception: %s'%e)
            gc.collect()
            continue


    # de-HTML
    soup = BeautifulSoup(feedback, features="html.parser")
    feedback = soup.get_text()

    if success:
        return 'Suite %s Passed:\n%s' % (uid, feedback)
    else:
        return 'Incorrect:\n%s' % (feedback)


@post('/nios2/leaderboard')
def post_leader(db):
    gc.collect()
    client_ip = request.environ.get('REMOTE_ADDR')
    asm = request.forms.get('asm')
    user = request.forms.get('user')
    response.set_cookie('user', user)

    def leader_template(user=user, code=asm, feedback=None):
        return jinja2_template('leaderboard.html',
                {'leaders': get_leaders(db),
                 'user': user,
                 'code': code,
                 'feedback': feedback,})

    #TODO: Make sure user is abcd1234 / in class?
    row = db.execute('SELECT count(*) FROM users where user=?', (user,)).fetchone()
    n_users = row[0]
    if n_users < 1:
        return leader_template(feedback='Unknown IdentiKey <b>' + html.escape(user) + '</b>. Please contact the instructor if you think this is an error')


    # Check if their code passes basic tests
    ex = Exercises.getExercise('sort-fn')
    res = ex['checker'](asm)

    if not(res[0]):
        return leader_template(feedback='<b>Your code does not pass the <a href="/nios2/examples/sort-fn">normal test cases</a>. Please pass those before attempting to submit here.</b><br/><br/>\n\n' + res[1])

    start = time.time()
    # Now check the main one
    ex = Exercises.getExercise('sort-fn-contest')
    success, feedback, instrs = ex['checker'](asm)
    delta = time.time() - start

    if not(success):
        return jinja2_template('leaderboard.html',
            {'leaders': get_leaders(db),
            'user': user,
            'code': asm,
            'feedback': feedback,
            'code_delta': delta,
            })

    # Get number of instructions in program
    obj = nios2_as(asm.encode('utf-8'))
    size = len(obj['prog'])/8


    # Passed tests, now see how it does compared to others!
    db.execute("INSERT INTO leaders (user,ip,instructions,size,public,timestamp,code) VALUES (?,?,?,?,?,strftime('%s', 'now'),?)", (user, client_ip, instrs, size, False, asm))
    db.commit()

    # Find our rank
    row = db.execute('SELECT COUNT(*) FROM (SELECT user, min(instructions) as ins FROM leaders GROUP BY user ORDER BY ins ASC) WHERE ins<?', (instrs,)).fetchone()
    rank = row[0]
    rank += 1

    return jinja2_template('leaderboard.html', {'leaders': get_leaders(db),
            'user': request.get_cookie('user'),
            'code': asm,
            'our_rank': rank,
            'instrs': instrs,
            'code_delta': delta,
            })


def get_leaders(db, N=10):
    rows = db.execute('SELECT user,min(instructions) as ins,size,timestamp FROM leaders GROUP BY user ORDER BY ins,timestamp ASC LIMIT 10')
    leaders = []
    for row in rows:
        leaders.append({'user': row[0],
                'instrs': row[1],
                'size': row[2],
                'time': datetime.fromtimestamp(row[3]).strftime('%b %d, %Y %H:%M:%S')})
    return leaders

#@jinja2_view('leaderboard.html')
@get('/nios2/leaderboard')
def leaderboard(db):
   return jinja2_template('leaderboard.html', {'leaders': get_leaders(db),
            'user': request.get_cookie('user'),
            'code': '',
            })

@get('/nios2')
@jinja2_view('index.html')
def nios2():
    return {'exercises': Exercises.getAllExercises()}



@route('/nios2/static/<path:path>')
def serve_static(path):
    return static_file(path, root="static/")


debug(True)
if __name__ == '__main__':
    debug(True)
    run(reloader=True)
