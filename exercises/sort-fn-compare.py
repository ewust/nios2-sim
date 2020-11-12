from exercises import *
import numpy as np
import random

def check_sort_fn_contest(asm):
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
        return (False, r, '')

    cpu = Nios2(obj=obj)

    cpu.reset()
    random.seed(12701296428285791133)
    tc = [random.randint(-2000,2000) for i in range(2500)]

    ans = sorted(tc)
    cpu.write_symbol_word('N', len(tc))
    for i,t in enumerate(tc):
        cpu.write_symbol_word('ARR', t, offset=i*4)

    instrs = cpu.run_until_halted(500000000)


    # Read back out SORT
    their_ans = [np.int32(cpu.get_symbol_word('ARR', offset=i*4)) for i in range(len(tc))]

    if their_ans != ans:
        feedback = 'Failed contest test case'
        # feedback += 'Sorting %s<br/>\n' % tc
        # feedback += 'Code provided: %s<br/>\n' % their_ans
        # feedback += 'Correct answer: %s<br/>\n' % ans
        # feedback += get_debug(cpu)
        del cpu
        return (False, feedback, None)
    feedback = 'Passed constest test case'

    del cpu
    return (True, feedback, instrs)


#########
# Sort
Exercises.addExercise('sort-fn-contest',
    {
        'public': False,
        'title': 'Sort an array',
        'diff': 'hard',
        'desc': '''Write a function that sorts an array. Your function should take two arguments: first, a pointer to an array of <b>signed</b> words, and second, an integer specifying the number of words in the array. Your task is to <b>sort</b> this array, overwriting the current array with one that is sorted. Once done, your code should return.

                We suggest you implement a very simple in-place sort, such as <a href="https://en.wikipedia.org/wiki/Bubble_sort">Bubble sort</a>, but you are welcome to implement any sorting algorithm.''',
        'code':'''.text
# void sort(signed int *array, unsigned int length);
sort:

    ret
    ''',
        'checker': check_sort_fn_contest
    })
