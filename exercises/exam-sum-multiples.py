from exercises import *
import numpy as np

##############
# Sum the array
def check_multiples(asm, test_cases):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['SUM', 'ARR', '_start'])
    if r is not None:
        return (False, r)

    feedback = ''
    cpu = Nios2(obj=obj)

    cur_test = 1
    for arr in test_cases:

        # Reset and initialize
        cpu.reset()
        for i, val in enumerate(arr):
            cpu.write_symbol_word('ARR', np.uint32(val), offset=i*4)
        cpu.write_symbol_word('N', len(arr))

        # Run
        instrs = cpu.run_until_halted(500000)

        # Check answer
        their_ans = np.uint32(cpu.get_symbol_word('SUM'))
        #ans = sum([x*x for x in arr])
        ans = sum([x for x in arr if x%3==0])
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




test_cases = [
        [1, 2, 4, 5, 7, 8],
        [3, 6, 9, 12],
        [1, 2, 3, 4, 5, 6],
        [1, 4, 3, 9, 6, 11, -1],
        [1, 3, -6, 9, 12, -15],
        [],
        range(1000),
        ]


Exercises.addExercise('exam-sum-multiples',
    {
        'public': False,
        'title': 'Array sum multiples',
        'diff':  'easy',
        'desc': '''No''',
        #'''You are given an array of signed words starting at <code>ARR</code> for length <code>N</code> words.
        #           <br/><br/>
        #           Find the sum of all <b>multiples of three</b> in the array
        #           and write the value to the word
        #           <code>SUM</code> in memory, then call the <code>break</code> instruction.''',
        'code':'''.text
_start:

.data
# Make sure ARR is the last label in .data
SUM: .word 0
N:   .word 5
ARR: .word 2, 4, 6, 8, 9
''',
    'checker': lambda asm: return check_multiples(asm, test_cases)
    })

for i,tc in enumerate(test_cases):
    Exercises.addExercise('exam-sum-multiples-%d'%i,
        {'public': False,
        'title': 'Array sum multiples - test case %d' % i,
        'diff': 'easy'
        'desc': '''See exam-sum-multiples''',
        'code':'',
        'checker': lambda asm: return check_multiples(asm, [tc])})





