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


def require_symbols(obj, symbols):
    for s in symbols:
        if s not in obj['symbols']:
            return '%s not found in memory (did you enter any instructions?)' % (s)
    return None

# Returns (correct_bool, feedback)
def check_find_min(obj):
    r = require_symbols(obj, ['MIN', 'ARR'])
    if r is not None:
        return (False, r)

    feedback = ''

    test_cases = [
        ([5, 3, 9, 2], 2),
        ([5, -8, 1, 12, 6], -8),
        ]

    cpu = Nios2(obj=obj)

    cur_test = 1
    for arr, ans in test_cases:

        # Reset and initialize
        cpu.reset()
        for i, val in enumerate(arr):
            cpu.write_symbol_word('ARR', np.uint32(val), offset=i*4)
        cpu.write_symbol_word('N', len(arr))

        # Run
        instrs = cpu.run_until_halted(10000)

        # Check answer
        their_ans = np.int32(cpu.get_symbol_word('MIN'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % (cur_test)
            feedback += 'MIN should be %d (0x%08x) for ARR %s. ' % (ans, np.uint32(ans), arr)
            feedback += 'Your code produced MIN=0x%08x' % np.uint32(their_ans)
            feedback += '<br/><br/>Memory:<br/><pre>'
            feedback += cpu.dump_mem(0, 0x100)
            feedback += '\nSymbols:\n' + cpu.dump_symbols()
            feedback += '</pre>'

            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % (cur_test)
        cur_test += 1

    return (True, feedback)

def check_array_sum(obj):
    r = require_symbols(obj, ['SUM', 'ARR'])
    if r is not None:
        return (False, r)

    test_cases = [
        ([5, 3, 9, 2], 19),
        ([5, -8, 1, 12, 6], 24),
        ([1, -8, -1, 0, 1, 1], 3),
        ]

    cpu = Nios2(obj=obj)

    cur_test = 1
    for arr, ans in test_cases:

        # Reset and initialize
        cpu.reset()
        for i, val in enumerate(arr):
            cpu.write_symbol_word('ARR', np.uint32(val), offset=i*4)
        cpu.write_symbol_word('N', len(arr))

        # Run
        instrs = cpu.run_until_halted(10000)

        # Check answer
        their_ans = np.uint32(cpu.get_symbol_word('SUM'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % (cur_test)
            feedback += 'SUM should be %d (0x%08x) for ARR %s. ' % (ans, np.uint32(ans), arr)
            feedback += 'Your code produced SUM=0x%08x' % np.uint32(their_ans)
            feedback += '<br/><br/>Memory:<br/><pre>'
            feedback += cpu.dump_mem(0, 0x100)
            feedback += '\nSymbols:\n' + cpu.dump_symbols()
            feedback += '</pre>'

            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % (cur_test)
        cur_test += 1

    return (True, feedback)



def get_debug(cpu, mem_len=0x100):
    out = ''
    out += '<br/><br/>Memory:<br/><pre>'
    out += cpu.dump_mem(0, mem_len)
    out += '\nSymbols:\n' + cpu.dump_symbols()
    out += '</pre>'
    return out



def check_led_on(obj):
    cpu = Nios2(obj=obj)


    # Make a MMIO rw/register
    leds = Nios2.MMIO_Reg()
    # Set the cpu's LED MMIO callback to that reg's access function
    cpu.mmios[0xFF200000] = leds.access

    instrs = cpu.run_until_halted(10000)

    feedback = ''
    if (leds.load() & 0x3ff) != 0x3ff:
        feedback += 'Failed test case 1: '
        feedback += 'LEDs are set to %s (should be %s)' % (bin(leds.load()&0x3ff), bin(0x3ff))
        feedback += get_debug(cpu)
        return (False, feedback)

    return (True, 'Passed test case 1')


def check_proj1(obj):
    cpu = Nios2(obj=obj)

    class p1grader(object):
        def __init__(self, test_cases=[]):
            # Array of (sw_val, expected_led_val)
            self.test_cases = test_cases
            self.cur_test = 0
            self.feedback = ''
            self.passed = True

        def write_led(self, val):
            # Assert correct answer
            sw, expected = self.test_cases[self.cur_test]
            if val != expected: # Check that they wrote to LEDs exactly
                if (val&0x3ff) != expected: # only warn if the LEDs would have masked for them..

                    self.feedback += 'Failed test case %d: ' % (self.cur_test+1)
                    self.feedback += 'LEDs set to %s (should be %s) for SW %s' % \
                                (bin(val&0x3ff), bin(expected), bin(sw))
                    self.feedback += get_debug(cpu)
                    self.passed = False
                    cpu.halted = True
                    return
                self.feedback += 'Test case %d: ' %(self.cur_test+1)
                self.feedback += 'Warning: wrote 0x%08x (instead of 0x%08x) to LEDs for SW %s;' %\
                                (val, expected, bin(sw))
                self.feedback += ' upper bits ignored.\n'
            self.feedback += 'Passed test case %d<br/>\n' % (self.cur_test+1)
            self.cur_test += 1
            if self.cur_test >= len(self.test_cases):
                cpu.halted = True

        def read_sw(self):
            sw, led = self.test_cases[self.cur_test]
            return sw

    tests = [(0, 0),
            (0b0000100001, 2),
            (0b0001100010, 5),
            (0b1011101110, 37),
            (0b1111111111, 62),
            (0b1111011111, 61),
            (0b0000111111, 32)]

    p1 = p1grader(tests)

    cpu.mmios[0xFF200000] = p1.write_led
    cpu.mmios[0xFF200040] = p1.read_sw

    instrs = cpu.run_until_halted(10000)

    return (p1.passed, p1.feedback)


def check_list_sum(obj):
    r = require_symbols(obj, ['SUM', 'HEAD'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)


    tests = [([3, 2, 1], 6),
             ([1, 0, 4], 5),
             ([-1, 2, 15, 8, 6], 30)]

    head_addr = obj['symbols']['HEAD']

    feedback = ''

    cur_test = 1
    for tc,ans in tests:
        cpu.reset()
        for ii,n in enumerate(tc):

            next_ptr = head_addr + (ii+1)*8
            if ii == len(tc)-1:
                # Last element, write null for pointer
                next_ptr = 0
            cpu.storeword(head_addr+ii*8, next_ptr)
            cpu.storeword(head_addr+ii*8+4, np.uint32(n))

        instrs = cpu.run_until_halted(10000)

        their_ans = np.int32(cpu.get_symbol_word('SUM'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'SUM was %d (0x%08x), should be %d (0x%08x)' % \
                    (their_ans, np.uint32(their_ans), ans, np.uint32(ans))
            feedback += get_debug(cpu)
            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % cur_test

        cur_test += 1

    return (True, feedback)



exercises = {
    ###############
    # Find Minimum
    'find-min': {
        'public': True,
        'diff': 'easy',
        'title': 'Find the minimum value in an array',
        'desc': '''You are given an array of words starting at <code>ARR</code>,
                    that contains <code>N</code> words in it.<br/>
                    <br/>
                    Your task is to write code to find the <b>lowest</b> signed value in the
                    array. Write the value to the word <code>MIN</code> in memory, and then
                    call the <code>break</code> instruction.''',
        'code': '''.text
_start:

.data
# Make sure ARR is the last label in .data
MIN: .word 0
N:   .word 5
ARR: .word 5, -8, -1, 12, 6
''',
        'checker': check_find_min
    },
    ##############
    # Sum the array
    'sum-array': {
        'public': True,
        'title': 'Array Sum',
        'diff':  'easy',
        'desc': '''You are given an array of signed words starting at <code>ARR</code> for length <code>N</code> words.
                   <br/><br/>
                   Find the sum of all the <b>positive</b> integers, and write the value to the word
                   <code>SUM</code> in memory, then call the <code>break</code> instruction.''',
        'code':'''.text
_start:

.data
# Make sure ARR is the last label in .data
SUM: .word 0
N:   .word 6
ARR: .word 14, 22, 0, -9, -12, 27
''',
        'checker': check_array_sum
    },
    ##########
    # Set the LEDs to all on
    'led-on': {
        'public': True,
        'title': 'Set LEDs on',
        'diff':  'easy',
        'desc': '''Turn on all 10 LEDs on the DE10-Lite, then call the <code>break</code> instruction.<br/><br/>
                    Hint: the LED MMIO address is <code>0xFF200000</code>''',
        'code':'''.text
_start:
''',
        'checker': check_led_on
    },
    ###########
    # Project 1
    'proj1': {
        'public': True,
        'title': 'Project 1',
        'diff': 'medium',
        'desc': '''Project 1 adder.s''',
        'code':'''.text
_start:
    movia   r4, 0xFF200000
    movia   r5, 0xFF200040

loop:
    ldwio   r6, 0(r5)


    stwio   r6, 0(r4)
    br      loop
''',
        'checker': check_proj1
    },
    ##########
    # Linked list sum
    'list-sum': {
        'public': True,
        'title': 'Sum a Linked List',
        'diff':  'medium',
        'desc': '''You are given a linked list node at addr <code>HEAD</code>.
                   Each list node consists of a word <code>next</code> that points to
                   the next node in the list, followed by a word <code>value</code>. The last
                   node in the list has its <code>next</code> pointer set to 0 (NULL).<br/><br/>

                   You can think of each node as being equivalent to the following C struct:<br/>
<pre>struct node {
    struct node *next;
    int          value;
};</pre><br/><br/>

                   Your task is to find the sum of all the <code>value</code>s in the list,
                   and write this sum to <code>SUM</code>,
                   then call the <code>break</code> instruction''',
        'code':'''.text
_start:


.data
SUM:    .word 0
HEAD:   .word N1, 5
N1:     .word N2, 3
N2:     .word N3, 10
N3:     .word 0,  6
''',
        'checker': check_list_sum
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

    return {'eid': eid,
            'exercise_code': asm,
            'exercise_title': ex['title'],
            'exercise_desc':  ex['desc'],
            'feedback': feedback,
            'success': success,
            }

@post('/nios2/examples.moodle/<eid>/<uid>')
def post_moodle(eid,uid):
    asm = request.forms.get('asm')
    obj = nios2_as(asm.encode('utf-8'))

    if eid not in exercises:
        return 'Exercise ID not found'

    ex = exercises[eid]

    if not(isinstance(obj, dict)):
        return 'Error: %s' % obj

    if '_start' not in obj['symbols']:
        return 'No _start in your code (did you forget to enter instructions?\n%s' % (json.dumps(obj))

    success, feedback = ex['checker'](obj)

    return 'Passed(%s): %s\n%s' % (uid, success, feedback)


@get('/nios2')
@jinja2_view('index.html')
def nios2():
    return {'exercises': exercises}


debug(True)
if __name__ == '__main__':
    debug(True)
    run(reloader=True)
