from exercises import *

##############
# Sum the array
def check_array_sum(asm):
    obj = nios2_as(asm.encode('utf-8'))
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

Exercises.addExercise('sum-array',
    {
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
    })


