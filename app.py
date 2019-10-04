#!/usr/bin/env python
import sys, os, bottle
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from bottle import route, run, default_app, debug, template, request, get, post, jinja2_view
import tempfile
import subprocess
from sim import Nios2, flip_word_endian
import json
import copy
import numpy as np

#from hashlib import sha256


app = application = default_app()

@app.route('/nios2/')
def nios2():
    return '''
<html>
<body>
<form action="/nios2/as" method="POST">
<textarea name="asm"></textarea><br/>
<input type="submit" value="Submit"/></form>
</body></html>'''



def nios2_as(asm):
    asm_f = tempfile.NamedTemporaryFile()
    asm_f.write(asm)
    asm_f.flush()

    obj_f = tempfile.NamedTemporaryFile()

    ########## Assemble
    p = subprocess.Popen(['bin/nios2-elf-as', \
                          asm_f.name, \
                          '-o', obj_f.name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() != 0:
        return ('Assembler error: %s' % p.stderr.read())
    asm_f.close()


    p = subprocess.Popen(['cp', obj_f.name, './test.o'])
    p.wait()

    ######### Link
    exe_f = tempfile.NamedTemporaryFile()
    p = subprocess.Popen(['bin/nios2-elf-ld', \
                          '-T', 'de10.ld', \
                          obj_f.name, '-o', exe_f.name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    if p.wait() != 0:
        return ('Linker error: %s' % p.stderr.read())
    obj_f.close()

    p = subprocess.Popen(['cp', exe_f.name, './test.out'])
    p.wait()

    ######## objdump
    p = subprocess.Popen(['./gethex.sh', exe_f.name], \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() != 0:
        return ('Objdump error: %s' % p.stderr.read())

    return json.loads(p.stdout.read().decode('ascii'))


@post('/nios2/as')
def post_as():
    asm = request.forms.get("asm")
    return json.dumps(nios2_as(asm.encode('utf-8')))


# Returns (correct_bool, feedback)

def check_find_min(obj):

    symbols = obj['symbols']

    if 'MIN' not in symbols:
        return (False, 'MIN not found in memory (did you enter any instructions?)')
    if 'ARR' not in symbols:
        return (False, 'ARR not found in memory (did you enter any instructions?)')

    feedback = ''
    ##########
    # Test case 1: run what ya got
    cpu = Nios2(init_mem=flip_word_endian(bytes.fromhex(obj['prog'])),
                start_pc=obj['symbols']['_start'])
    inst = 0
    while not(cpu.halted) and inst < 10000:
        cpu.one_step()
        inst += 1

    their_ans = np.int32(cpu.loadword(symbols['MIN']))
    if their_ans != -8:
        feedback += 'Failed test case 1: MIN should be -8 (0xfffffff8) for testcase 5,-8,-1,12,6. Your code produced MIN=0x%08x' % np.uint32(their_ans)
        return (False, feedback)

    feedback += 'Passed test case 1<br/>\n'

    # Reset
    cpu = Nios2(init_mem=flip_word_endian(bytes.fromhex(obj['prog'])),
                start_pc=obj['symbols']['_start'])
    ##########
    # Test case 2: 5,3,9,2
    arr = symbols['ARR']
    test_case = [5, 3, 9, 2, 0, 0, 0]
    for i in range(len(test_case)):
        cpu.storeword(arr+i*4, test_case[i])
    cpu.storeword(symbols['N'], 4)
    inst = 0
    while not(cpu.halted) and inst < 10000:
        cpu.one_step()
        inst += 1

    their_ans = np.uint32(cpu.loadword(symbols['MIN']))
    if their_ans != 2:
        feedback += 'Failed test case 2: MIN should be 2 (0x00000002) for testcase 5,3,9,2. Your code produced MIN=0x%08x' % np.uint32(their_ans)
        return (False, feedback)

    feedback += 'Passed test case 2<br/>\n'

    return (True, feedback)


def check_array_sum(obj):

    symbols = obj['symbols']

    if 'SUM' not in symbols:
        return (False, 'SUM not found in memory (did you enter any instructions?)')
    if 'ARR' not in symbols:
        return (False, 'ARR not found in memory (did you enter any instructions?)')

    feedback = ''
    ##########
    # Test case 1: run what ya got
    cpu = Nios2(init_mem=flip_word_endian(bytes.fromhex(obj['prog'])),
                start_pc=obj['symbols']['_start'])
    cpu.dump_mem(0, 0x80)
    inst = 0
    while not(cpu.halted) and inst < 10000:
        cpu.one_step()
        inst += 1

    their_ans = np.int32(cpu.loadword(symbols['SUM']))
    if their_ans != 63:
        feedback += 'Failed test case 1: SUM should be 63 (0x0000003f) for testcase 1. Your code produced SUM=0x%08x' % np.uint32(their_ans)
        return (False, feedback)

    feedback += 'Passed test case 1<br/>\n'

    cpu = Nios2(init_mem=flip_word_endian(bytes.fromhex(obj['prog'])),
                start_pc=obj['symbols']['_start'])
    arr = symbols['ARR']
    test_case = [5, 3, 9, 2, -1, 0, 0]
    for i in range(len(test_case)):
        cpu.storeword(arr+i*4, np.uint32(np.int32(test_case[i])))
    cpu.storeword(symbols['N'], 5)
    inst = 0
    while not(cpu.halted) and inst < 10000:
        cpu.one_step()
        inst += 1

    their_ans = np.uint32(cpu.loadword(symbols['SUM']))
    if their_ans != 19:
        feedback += 'Failed test case 2: SUM should be 19 (0x00000013) for testcase 5,3,9,2,-1 Your code produced MIN=0x%08x' % np.uint32(their_ans)
        return (False, feedback)

    feedback += 'Passed test case 2<br/>\n'

    return (True, feedback)




exercises = {
    ###############
    # Find Minimum
    'find-min': {
        'title': 'Find minimum in an array',
        'desc': '''For a given array of words starting at ARR for length N,
                   find the lowest signed value in the array. Write the value
                   to the word MIN in memory, and then call the <code>break</code>
                   instruction.''',
        'code': '''.text
_start:

.data
MIN: .word 0
N:   .word 5
ARR: .word 5, -8, -1, 12, 6
''',
        'checker': check_find_min
    },
    ##############
    # Sum the array
    'sum-array': {
        'title': 'Array Sum',
        'desc': '''You are given an array of signed words starting at ARR for length N.
                   Find the sum of all the positive integers, and write the value to the word
                   SUM in memory, then call the <code>break</code> instruction.''',
        'code':'''.text
_start:

.data
SUM: .word 0
N:   .word 6
ARR: .word 14, 22, 0, -9, -12, 27
''',
        'checker': check_array_sum
    },

}


@get('/nios2/examples/<eid>')
@jinja2_view('example.html')
def get_example(eid):

    if eid not in exercises:
        return {'asm_error': 'Exercise ID not found'}
    ex = exercises[eid]

    return {'eid': eid,
            'exercise_title': ex['title'],
            'exercise_desc':  ex['desc'],
            'exercise_code':  ex['code'],
           }


@post('/nios2/examples/<eid>')
@jinja2_view('example.html')
def post_example(eid):
    asm = request.forms.get('asm')
    obj = nios2_as(asm.encode('utf-8'))

    if eid not in exercises:
        return {'asm_error': 'Exercise ID not found'}

    ex = exercises[eid]

    if not(isinstance(obj, dict)):
        return {'eid': eid, \
                'exercise_code': asm,\
                'exercise_title': ex['title'],\
                'exercise_desc':  ex['desc'],\
                'asm_error': obj,}

    if '_start' not in obj['symbols']:
        return {'eid': eid, \
                'exercise_code': asm,\
                'exercise_title': ex['title'],\
                'exercise_desc':  ex['desc'],\
                'asm_error': 'No _start in your code (did you forget to enter instructions?)<br/>%s' % (json.dumps(obj)),}


    success, feedback = ex['checker'](obj)


    #success, feedback = ex['checker'](cpu, obj['symbols'])


    return {'eid': eid,
            'exercise_code': asm,
            'exercise_title': ex['title'],
            'exercise_desc':  ex['desc'],
            'feedback': feedback,
            'success': success,
            }


debug(True)
if __name__ == '__main__':
    debug(True)
    run(reloader=True)
