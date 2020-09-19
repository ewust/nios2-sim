
#from exercises import Exercises
from exercises import *

##########
# Computes the sum from 1-N
def sum_1_to_N(N):
    i = 1
    sum = 0
    while i <= N:
        sum += i
        i += 1
    return sum 

# Set the LEDs to all on
def check_sum_1_to_N(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['N', '_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=obj)
    # print(sum_1_to_N(20))
    #variables 
    cur_test = 0
    feedback = ''

    test_cases = [(10,55), (9, 45), (20,210)]
    for N, ans in test_cases:
        ## Reset and initialize
        cpu.reset()
        cpu.write_symbol_word('N', N)


        # Run
        instrs = cpu.run_until_halted(10000)

        # Check Answer
        their_ans = cpu.get_reg(2)
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % (cur_test)
            feedback += '<code>r2</code> should be %d for <b>N</b> = %d .' % (ans,N)
            feedback += 'Your code produced <code>r2</code> = %d' % (their_ans)
            # feedback += '<br/><br/>Memory:<br/><pre>'
            # feedback += cpu.dump_mem(0, 0x100)
            feedback += '\nSymbols:\n' + cpu.dump_symbols()
            feedback += '</pre>'
            return (False, feedback)
        feedback += 'Passed test case %d<br/>\n' % (cur_test)
        cur_test += 1  
    return (True, feedback)


Exercises.addExercise('sum-1-N',
    {
        'public': True,
        'title': 'Sum integers from 1-N',
        'diff':  'easy',
        'desc': '''Sum the integers starting from 1 and ending at N (inclusive).<br/><br/>
                   <b>N</b> and the instructions to load it into <code>r4</code> have been provided. Store the sum in <code>r2</code>.
                   \n<b>Note: Do not edit the provided code.</b>''',
        'code':'''.text
_start:
    movia   r4, N
    ldw     r4, 0(r4)
    movi    r2, 0

    # Your code here


    break

.data
N:  .word 9
''',
        'checker': check_sum_1_to_N
    })
