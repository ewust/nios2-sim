#!/usr/bin/env python
import sys, os, bottle
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from bottle import route, run, default_app, debug, template, request, get, post, jinja2_view, static_file
import json
import gc
from bs4 import BeautifulSoup

from util import nios2_as
from exercises import Exercises

app = application = default_app()


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
