
from exercises import *
import numpy as np

###############
# Find Minimum
def check_find_min(asm):
    obj = nios2_as(asm.encode('utf-8'))
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


Exercises.addExercise('find-min',
    {
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
    })
 
