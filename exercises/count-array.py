from exercises import *
import numpy as np

##############
# Sum the array
def check_array_count(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['COUNT', 'N', 'X', 'ARR', '_start'])
    if r is not None:
        return (False, r)

    test_cases = [
        ([1, 2, 1, 2, 1, 2, 2, 3, 0, 0], 2, 4),
        ([1, 1, 0, 0, 0, 0, 1], 1, 3),
        ([18, 3, 9, 2], 42, 0),
        ([], 0, 0),
        ([1], 1, 1),
        ([42]*42, 42, 42),
        ]

    cpu = Nios2(obj=obj)

    feedback = ''
    cur_test = 1
    for arr, x, ans in test_cases:

        # Reset and initialize
        cpu.reset()
        for i, val in enumerate(arr):
            cpu.write_symbol_word('ARR', np.uint32(val), offset=i*4)
        cpu.write_symbol_word('N', len(arr))
        cpu.write_symbol_word('X', x)

        # Run
        instrs = cpu.run_until_halted(10000)

        # Check answer
        their_ans = np.uint32(cpu.get_symbol_word('COUNT'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % (cur_test)
            feedback += 'COUNT should be %d (0x%08x) for ARR %s. ' % (ans, np.uint32(ans), arr)
            feedback += 'Your code produced COUNT=0x%08x' % np.uint32(their_ans)
            feedback += '<br/><br/>Memory:<br/><pre>'
            feedback += cpu.dump_mem(0, 0x100)
            feedback += '\nSymbols:\n' + cpu.dump_symbols()
            feedback += '</pre>'

            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % (cur_test)
        cur_test += 1

    return (True, feedback)

Exercises.addExercise('count-array',
    {
        'public': True,
        'title': 'Count occurances',
        'diff':  'easy',
        'desc': '''You are given an array of signed integer words starting at <code>ARR</code> for length <code>N</code> words. You are also given <code>X</code>. 

        <br/><br/>You are to count the number of times that <code>X</code> appears in <code>ARR</code>, and store the value in <code>COUNT</code> and then call the <code>break</code> instruction.''',
        'code':'''.text
_start:

.data
# Make sure ARR is the last label in .data
COUNT: .word 0
X:   .word 42
N:   .word 8
ARR: .word 11, 42, -3, 42, 0, 42, 42, 578
''',
        'checker': check_array_count
    })


