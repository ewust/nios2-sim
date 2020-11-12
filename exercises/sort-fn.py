from exercises import *
import numpy as np
import random

def check_sort_fn(asm):
    new_start = '''
.data
    N:  .word 0
    ARR: .word 0
    .rept 10000 .word 0
    .endr

.text
    _start:
        movia   sp, 0x3fffffc
        movia   r4, ARR
        movia   r5, N
        ldw     r5, 0(r5)

        call    sort

        break
    '''
    hp = new_start + asm
    obj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(obj, ['N', 'ARR', 'sort', '_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [[5, 4, 3, 2, 1],
             [5, 4, 2, 3, 1],
             [2, 8, 3, 9, 15, 10],
             [8, -1, 11, 14, 12, 14, 0],
             [9, -2, 5, 0, -2, 0, -1, -4, 1, 9, 10, 6, -3, 7, 5, 10, 9, -2, 2, 9, 0, 3, -3, 7, 7, 6, -5, -2, -1, -4]]

    final_test = [random.randint(-1000,1000) for i in range(2000)]
    tests += [final_test]

    feedback = ''
    cur_test = 1
    tot_instr = 0
    for tc in tests:
        cpu.reset()
        ans = sorted(tc)
        cpu.write_symbol_word('N', len(tc))
        for i,t in enumerate(tc):
            cpu.write_symbol_word('ARR', t, offset=i*4)

        instrs = cpu.run_until_halted(300000000)
        tot_instr += instrs

        # Read back out SORT
        their_ans = [np.int32(cpu.get_symbol_word('ARR', offset=i*4)) for i in range(len(tc))]

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
Exercises.addExercise('sort-fn',
    {
        'public': True,
        'title': 'Sort an array',
        'diff': 'hard',
        'desc': '''Write a function that sorts an array. Your function should take two arguments: first, a pointer to an array of <b>signed</b> words, and second, an integer specifying the number of words in the array. Your task is to <b>sort</b> this array, overwriting the current array with one that is sorted. Once done, your code should return.

                We suggest you implement a very simple in-place sort, such as <a href="https://en.wikipedia.org/wiki/Bubble_sort">Bubble sort</a>, but you are welcome to implement any sorting algorithm.''',
        'code':'''.text
# void sort(signed int *array, unsigned int length);
sort:

    ret
    ''',
        'checker': check_sort_fn
    })
