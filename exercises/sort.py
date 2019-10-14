from exercises import *
import numpy as np

def check_sort(asm):
    obj = nios2_as(asm.encode('utf-8'))
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


#########
# Sort
Exercises.addExercise('sort',
    {
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
    })
