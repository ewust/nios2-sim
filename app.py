#!/usr/bin/env python
import sys, os, bottle
os.chdir(os.path.dirname(os.path.abspath(__file__)))
from bottle import route, run, default_app, debug, template, request, get, post, jinja2_view, static_file
import tempfile
import subprocess
from csim import Nios2
import json
import copy
import numpy as np
import gc
import collections
import html
import struct
from collections import defaultdict
from bs4 import BeautifulSoup

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
        ret = 'Assembler error: %s' % p.stderr.read()
        obj_f.close()
        asm_f.close()
        p.stdout.close()
        p.stderr.close()
        return ret

    asm_f.close()
    p.stdout.close()
    p.stderr.close()


    ######### Link
    exe_f = tempfile.NamedTemporaryFile()
    p = subprocess.Popen(['bin/nios2-elf-ld', \
                          '-T', 'de10.ld', \
                          obj_f.name, '-o', exe_f.name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    if p.wait() != 0:
        ret = 'Linker error: %s' % p.stderr.read()
        p.stderr.close()
        p.stdout.close()
        obj_f.close()
        return ret

    obj_f.close()
    p.stdout.close()
    p.stderr.close()

    ######## objdump
    p = subprocess.Popen(['./gethex.sh', exe_f.name], \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() != 0:
        ret = 'Objdump error: %s' % p.stderr.read()
        p.stderr.close()
        p.stdout.close()
        exe_f.close()
        return ret

    obj = json.loads(p.stdout.read().decode('ascii'))
    p.stdout.close()
    p.stderr.close()
    exe_f.close()

    return obj


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

def require_symbols(obj, symbols):
    for s in symbols:
        if s not in obj['symbols']:
            return '%s not found in memory (did you enter any instructions?)' % (s)
    return None

# Returns (correct_bool, feedback)
def check_find_min(obj):
    r = require_symbols(obj, ['MIN', 'ARR', '_start'])
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
    r = require_symbols(obj, ['SUM', 'ARR', '_start'])
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



def get_debug(cpu, mem_len=0x100, show_stack=False):
    out = '<br/>\n'
    out += cpu.get_error()
    out += '<br/>Memory:<br/><pre>'
    out += cpu.dump_mem(0, mem_len)
    out += '\nSymbols:\n' + cpu.dump_symbols()
    out += '</pre>'
    if show_stack:
        sp = cpu.get_reg(27)
        fp = cpu.get_reg(28)
        out += '<br/>Stack:<br/><pre>'
        out += 'sp = 0x%08x\nfp = 0x%08x\n\n' % (sp, fp)
        diff = 0x04000000 - (sp-0x80)
        out += cpu.dump_mem(sp-0x80, min(0x100, diff))
        out += '\n</pre>'
    return out



def check_led_on(obj):
    cpu = Nios2(obj=obj)


    # Make a MMIO rw/register
    leds = Nios2.MMIO_Reg()
    # Set the cpu's LED MMIO callback to that reg's access function
    cpu.add_mmio(0xFF200000, leds.access)
    #cpu.mmios[0xFF200000] = leds.access

    instrs = cpu.run_until_halted(1000000)

    feedback = ''
    if (leds.load() & 0x3ff) != 0x3ff:
        feedback += 'Failed test case 1: '
        feedback += 'LEDs are set to %s (should be %s)' % (format((leds.load()&0x3ff), '#012b'), bin(0x3ff))
        feedback += get_debug(cpu)
        del cpu
        return (False, feedback)

    del cpu
    return (True, 'Passed test case 1')


def check_proj1(obj):
    cpu = Nios2(obj=obj)

    class p1grader(object):
        def __init__(self, test_cases=[]):
            # Array of (sw_val, expected_led_val)
            self.test_cases = test_cases
            self.cur_test = 0
            self.feedback = ''
            self.num_passed = 0

        def write_led(self, val):
            # Assert correct answer
            sw, expected = self.test_cases[self.cur_test]
            if val != expected: # Check that they wrote to LEDs exactly
                if (val&0x3ff) != expected: # only warn if the LEDs would have masked for them..

                    self.feedback += 'Failed test case %d: ' % (self.cur_test+1)
                    self.feedback += 'LEDs set to %s (should be %s) for SW %s' % \
                                (bin(val&0x3ff), bin(expected), bin(sw))
                    self.feedback += get_debug(cpu)
                    cpu.halt()
                    return
                self.feedback += 'Test case %d: ' %(self.cur_test+1)
                self.feedback += 'Warning: wrote 0x%08x (instead of 0x%08x) to LEDs for SW %s;' %\
                                (val, expected, bin(sw))
                self.feedback += ' upper bits ignored.\n'
            self.feedback += 'Passed test case %d<br/>\n' % (self.cur_test+1)
            self.cur_test += 1
            self.num_passed += 1
            if self.cur_test >= len(self.test_cases):
                cpu.halt()

        def read_sw(self):
            if self.cur_test > len(self.test_cases):
                print('Error: read_sw after we should have halted?')
                return 0    # ??
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

    cpu.add_mmio(0xFF200000, p1.write_led)
    cpu.add_mmio(0xFF200040, p1.read_sw)

    #cpu.mmios[0xFF200000] = p1.write_led
    #cpu.mmios[0xFF200040] = p1.read_sw

    instrs = cpu.run_until_halted(10000)

    print('Passed %d of %d' % (p1.num_passed, len(tests)))
    err = cpu.get_error()
    del cpu
    return (p1.num_passed==len(tests), err + p1.feedback)

def check_list_sum(obj):
    r = require_symbols(obj, ['SUM', 'HEAD', '_start'])
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

        instrs = cpu.run_until_halted(1000000)

        their_ans = np.int32(cpu.get_symbol_word('SUM'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'SUM was %d (0x%08x), should be %d (0x%08x)' % \
                    (their_ans, np.uint32(their_ans), ans, np.uint32(ans))
            feedback += get_debug(cpu)
            del cpu
            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % cur_test

        cur_test += 1

    del cpu
    return (True, feedback)

def check_fib(obj):
    r = require_symbols(obj, ['N', 'F', '_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [(10, 55), (15, 610), (12, 144), (30, 832040)]
    feedback = ''
    extra_info = ''
    cur_test = 1
    clobbered = set()
    for n,ans in tests:
        cpu.reset()
        cpu.write_symbol_word('N', n)

        instrs = cpu.run_until_halted(100000000)


        # Check for clobbered registers first
        # in case this is why they failed
        clobs = cpu.get_clobbered()
        if len(clobs) > 0:
            for pc,rid in clobs:
                if (pc,rid) not in clobbered:
                    extra_info += 'Warning: Function @0x%08x clobbered r%d\n<br/>' % (pc, rid)
                    clobbered.add((pc, rid))

        # Check answer
        their_ans = cpu.get_symbol_word('F')
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'fib(%d) returned %d, should have returned %d' %\
                    (n, their_ans, ans)
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, extra_info)

        feedback += 'Passed test case %d<br/>\n' % cur_test
        cur_test += 1

    del cpu
    return (True, feedback, extra_info)


def check_sort(obj):
    r = require_symbols(obj, ['N', 'SORT', '_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [[5, 4, 3, 2, 1],
             [5, 4, 2, 3, 1],
             [2, 8, 3, 9, 15, 10],
             [8, -1, 11, 14, 12, 14, 0],
             [9, -2, 5, 0, -2, 0, -1, -4, 1, 9, 10, 6, -3, 7, 5, 10, 9, -2, 2, 9, 0, 3, -3, 7, 7, 6, -5, -2, -1, -4]]
    feedback = ''
    cur_test = 1
    tot_instr = 0
    for tc in tests:
        cpu.reset()
        ans = sorted(tc)
        cpu.write_symbol_word('N', len(tc))
        for i,t in enumerate(tc):
            cpu.write_symbol_word('SORT', t, offset=i*4)

        instrs = cpu.run_until_halted(100000000)
        tot_instr += instrs

        # Read back out SORT
        their_ans = [np.int32(cpu.get_symbol_word('SORT', offset=i*4)) for i in range(len(tc))]

        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'Sorting %s<br/>\n' % tc
            feedback += 'Code provided: %s<br/>\n' % their_ans
            feedback += 'Correct answer: %s<br/>\n' % ans
            feedback += get_debug(cpu)
            del cpu
            return (False, feedback, None)
        feedback += 'Passed test case %d<br/>\n' % cur_test
        cur_test += 1
    del cpu
    extra_info = '%d total instructions' % tot_instr
    return (True, feedback, extra_info)

def check_uart(obj):
    cpu = Nios2(obj=obj)

    class uart(object):
        def __init__(self, name='', step_roll=(1,1)):
            self.name = name + '\n'
            self.idx = 0
            self.rx_fifo = collections.deque()
            self.tx_fifo = collections.deque()
            self.recvd = ''
            self.tx_step = 0
            self.rx_step = 0
            self.tx_step_roll = step_roll[0]
            self.rx_step_roll = step_roll[1]
            self.feedback = ''
            self.extra_info = ''

        def step(self):
            self.tx_step += 1
            self.rx_step += 1
            if self.tx_step == self.tx_step_roll:
                self.tx_step = 0
                # Read from the tx_fifo
                if len(self.tx_fifo) > 0:
                    self.recvd += chr(self.tx_fifo.popleft())

            if self.rx_step == self.rx_step_roll:
                self.rx_step = 0
                # Write to the rx_fifo
                if self.idx < len(self.name):
                    self.rx_fifo.append(ord(self.name[self.idx]))
                    self.idx += 1

        def uart_data(self, val=None):
            self.step()
            if val is not None:
                # stwio
                chr_data = val & 0xff
                if len(self.tx_fifo) >= 64:
                    # Lost the data!
                    self.extra_info += 'Warning: Wrote character \'%s\' (0x%02x) while transmit FIFO full!\n<br/>' %\
                            (html.escape(chr(chr_data)), chr_data)

                    self.extra_info += 'tx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.tx_fifo), html.escape(''.join([chr(c) for c in self.tx_fifo])))
                    self.extra_info += 'rx_fifo: %s <code>%s</code>\n<br/><br/>' % \
                        (list(self.rx_fifo), html.escape(''.join([chr(c) for c in self.rx_fifo])))
                    #self.feedback += 'Received so far: \'%s\'\n</br>' % (self.recvd)

                    #cpu.halt()
                    return
                self.tx_fifo.append(chr_data)
            else:
                # ldwio
                if len(self.rx_fifo) == 0:
                    return (len(self.rx_fifo) << 16) | (0x0<<15) | 0x41

                # Get next chr
                chr_data = self.rx_fifo.popleft()
                return (len(self.rx_fifo) << 16) | (0x1<<15) | chr_data

        def uart_ctrl(self, val=None):
            self.step()
            if val is None:
                # ldwio
                return (64 - len(self.tx_fifo)) << 16

        def result(self, test_no=1):
            while len(self.tx_fifo) > 0:
                self.recvd += chr(self.tx_fifo.popleft())
            if self.recvd == 'Hello, %s' % self.name:
                return (True, 'Test case %d passed\n<br/>' % test_no, self.extra_info)
            else:
                err = cpu.get_error()
                self.feedback += 'Failed test case %d\n<br/>' % test_no
                self.feedback += 'Name: <code>%s</code><br/>' % html.escape(self.name)
                self.feedback += 'Got back <code>%s</code> %s<br/>' % (html.escape(self.recvd), self.recvd.encode('ascii').hex())
                self.feedback += get_debug(cpu)
                self.feedback += 'tx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.tx_fifo), html.escape(''.join([chr(c) for c in self.tx_fifo])))
                self.feedback += 'rx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.rx_fifo), html.escape(''.join([chr(c) for c in self.rx_fifo])))
                return (False, err + self.feedback, self.extra_info)





    tests = [('test', (10,1)),
             ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789~!@#$%^&*()', (50,1)),
             ('Alan Turing', (10, 10))]
    extra_info = ''
    feedback = ''

    tot_ins = 0
    for i,tc in enumerate(tests):
        u = uart(tc[0], step_roll=tc[1])
        cpu.reset()
        cpu.add_mmio(0xFF201000, u.uart_data)
        cpu.add_mmio(0xFF201004, u.uart_ctrl)

        tot_ins += cpu.run_until_halted(100000)

        res, fb, extra = u.result(i+1)
        feedback += fb
        if extra is not None:
            extra_info += extra
        if not res:
            return (False, feedback, extra_info)

    extra_info += 'Executed %d instructions' % tot_ins
    return (True, feedback, extra_info)


def hotpatch(obj, new_start_asm):
    hp = '.text\n'
    # fill symbols
    rev_map = defaultdict(list) # addr => [list_of_symbols]
    # TODO: this will only work for word-aligned labels...
    for s,addr in obj['symbols'].items():
        #hp += '.equ %s, 0x%08x\n' % (s, addr)
        if s != '_start':
            rev_map[addr].append(s)

    # fill bytes
    p = bytes.fromhex(obj['prog'])
    for i in range(len(p)>>2):
        addr = 4*i
        word, = struct.unpack('>I', p[4*i:4*i+4])
        for sym in rev_map[addr]:
            hp += '%s:\n' % sym
        hp += ' .word 0x%08x\n' % (word)
    hp += new_start_asm
    return nios2_as(hp.encode('utf-8'))

def check_callee_saved(obj):
    # Need to insert a _start symbol
    new_start = '''.text
    test_A:  .word 12
    test_B:  .word 42
    _start:
        movia   sp, 0x04000000
        subi    sp, sp, 4

        movi    r18, 0xccc
        movi    r16, 0xddd
        movi    r17, 8
        movia   r4, test_A
        ldw     r4, 0(r4)
        movia   r5, test_B
        ldw     r5, 0(r5)

        call    foo

        break
    '''
    nobj = hotpatch(obj, new_start)

    tests = [(12, 42, 10230),
             (5, 5, 730),
             (0, 0, 0)]

    cpu = Nios2(obj=nobj)
    feedback = ''
    for i,tc in enumerate(tests):
        cpu.reset()

        cpu.write_symbol_word('test_A', tc[0])
        cpu.write_symbol_word('test_B', tc[1])

        cpu.run_until_halted(1000)

        passed = (cpu.get_reg(2) == tc[2]) and len(cpu.get_clobbered())==0
        if passed:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d<br/>\n' % (i+1)
            for addr,rid in cpu.get_clobbered():
                feedback += 'Error: function @0x%08x clobbered r%d\n<br/>' % (addr, rid)
            feedback += '<br/>'
            feedback += get_debug(cpu, show_stack=True)
            return (False, feedback, None)
    return (True, feedback, None)


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
    ############
    # Fib
    'fibonacci': {
        'public': True,
        'title': 'Fibonacci Sequence',
        'diff':  'medium',
        'desc':  '''The  Fibonacci Sequence is computed as <code>f(n) = f(n-1) + f(n-2)</code>. We must define two <b>base case</b> values: <code>f(0) = 0</code> and <code>f(1) = 1</code>.<br/><br/>

                Thus, the first values of this sequence are: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, etc.<br/><br/>

                Your task is to write a function <code>fib</code> which takes a single number <code>n</code> and returns <code>f(n)</code> as defined above by the Fibonacci Sequence.''',
        'code':'''.text
fib:
    # Write your code here

    ret

_start:
    # You should probably test your program!
    # Feel free to change the value of N, but leave the rest of
    # this code as is.
    movia   sp, 0x04000000  # Setup the stack pointer
    subi    sp, sp, 4

    movia   r4, N
    ldw     r4, 0(r4)

    call    fib             # fib(N)

    movia   r4, F
    stw     r2, 0(r4)       # store r2 to F
    break                   # r2 should be 55 here.
.data
N:  .word 10
F:  .word 0
''',
        'checker': check_fib
    },
    #########
    # Sort
    'sort': {
        'public': True,
        'title': 'Sort an array',
        'diff': 'hard',
        'desc': '''You are given an array of <b>signed</b> words starting at <code>SORT</code> that contains <code>N</code> words. Your task is to <b>sort</b> this array, overwriting the current array with one that is sorted. Once done, your code should call the <code>break</code> instruction.<br/><br/>
                We suggest you implement a very simple in-place sort, such as <a href="https://en.wikipedia.org/wiki/Bubble_sort">Bubble sort</a>, but you are welcome to implement any sorting algorithm.''',
        'code':'''.text
_start:


.data
N: .word 5
SORT: .word 8, 3, 7, 2, 9
# Padding
.rept 100 .word 0
.endr''',
        'checker': check_sort
    },
    ###########
    # JTAG UART
    'uart-name': {
        'public': True,
        'title': 'Write "Hello, &lt;name&gt;" to UART',
        'diff': 'medium',
        'desc': '''Write a program that reads a name from the JTAG UART port until you reach a linebreak (<code>\\n</code> ASCII <code>0x0a</code>) character.
        After the linebreak is received, you should write the message <code>Hello, &lt;name&gt;</code> where <code>&lt;name&gt;</code> is the name read from the UART
        port previously. Your message should include the linebreak read as part of the name.
        ''',
        'code':'''.text
_start:
        ''',
        'checker': check_uart
    },
    ##########
    # callee-saved
    'callee-saved': {
        'public': False,
        'title': 'Callee Saved',
        'diff': 'medium',
        'desc': '''Your are given the following function, but it is missing two parts for you to fill in: saving registers in the function prologue and restoring them in the epilogue.
        ''',
        'code':'''.text

foo:
    # Write your function prologue here

    add     r2, r4, r5
    mov     r6, r4
    slli    r12, r6, 4
    mul     r16, r2, r12
    sub     r18, r2, r12
    add     r2, r16, r18

    # Write your function epilogue here
    ret''',
        'checker': check_callee_saved
    },
}


@get('/nios2/examples/<eid>')
@jinja2_view('example.html')
def get_example(eid):
    gc.collect()
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
    gc.collect()
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

    #if '_start' not in obj['symbols']:
    #    return {'eid': eid, \
    #            'exercise_code': asm,\
    #            'exercise_title': ex['title'],\
    #            'exercise_desc':  ex['desc'],\
    #            'asm_error': 'No _start in your code (did you forget to enter instructions?)<br/>%s' % (json.dumps(obj)),}

    extra_info = ''
    res = ex['checker'](obj)
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
    obj = nios2_as(asm.encode('utf-8'))

    if eid not in exercises:
        return 'Exercise ID not found'

    ex = exercises[eid]

    if not(isinstance(obj, dict)):
        return 'Error: %s' % obj

    #if '_start' not in obj['symbols']:
    #    return 'No _start in your code (did you forget to enter instructions?\n%s' % (json.dumps(obj))

    #success, feedback = ex['checker'](obj)
    res = ex['checker'](obj)
    if len(res) == 2:
        success, feedback = res
    elif len(res) == 3:
        success, feedback, _ = res

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
    return {'exercises': exercises}



@route('/nios2/static/<path:path>')
def serve_static(path):
    return static_file(path, root="static/")


debug(True)
if __name__ == '__main__':
    debug(True)
    run(reloader=True)
