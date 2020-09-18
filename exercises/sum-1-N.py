
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
    cpu = Nios2(obj=obj)
    
    #variables 
    cur_test = 0
    feedback = ''

    # Test case 0 (Test their value of N): 
    # cpu.reset()
    instrs = cpu.run_until_halted(10000)
   
    #verify that r4 is valid and is storing N
    N = cpu.get_reg(4)
    print(N)
    if N <= 1:
        feedback += 'Failed test case %d: ' % (cur_test)
        feedback += 'N was either not found in <code>r4</code> or not an integer greater than 1.'
        feedback += '<br/><br/>Memory:<br/><pre>'
        feedback += cpu.dump_mem(0, 0x100)
        feedback += '\nSymbols:\n' + cpu.dump_symbols()
        feedback += '</pre>'
        return (False, feedback)
    
    #check their answer
    ans = sum_1_to_N(N)
    their_ans = cpu.get_reg(2)
    if ans != their_ans:
        feedback += 'Failed test case %d: ' % (cur_test)
        feedback += '<code>r2</code> should be %d for <b>N</b> = %d .' % (ans,N)
        feedback += 'Your code produced <code>r2</code> = %d' % (their_ans)
        feedback += '<br/><br/>Memory:<br/><pre>'
        feedback += cpu.dump_mem(0, 0x100)
        feedback += '\nSymbols:\n' + cpu.dump_symbols()
        feedback += '</pre>'
        return (False, feedback)
    feedback += 'Passed test case %d<br/>\n' % (cur_test)
    cur_test += 1
    
    # Test cases 
    # test_cases = [(9,45)]

    # for N, ans in test_cases:
    #     # Reset and Initialize
    #     cpu.reset()

    #     #Set r4 to n
    #     cpu.set_reg(4,N)

    #     # Run
    #     instrs = cpu.run_until_halted(10000)

    #     # Check answer
    #     their_ans = cpu.get_reg(2)
    #     if their_ans != ans:
    #         feedback += 'Failed test case %d: ' % (cur_test)
    #         feedback += '<code>r2</code> should be %d for <b>N</b> = %d .' % (ans,N)
    #         feedback += 'Your code produced <code>r2</code> = %d' % (their_ans)
    #         feedback += '<br/><br/>Memory:<br/><pre>'
    #         feedback += cpu.dump_mem(0, 0x100)
    #         feedback += '\nSymbols:\n' + cpu.dump_symbols()
    #         feedback += '</pre>'

    #         return (False, feedback)
    #     feedback += 'Passed test case %d<br/>\n' % (cur_test)
    #     cur_test += 1
  
    return (True, feedback)


Exercises.addExercise('sum-1-N',
    {
        'public': True,
        'title': 'Sum integers from 1-N',
        'diff':  'easy',
        'desc': '''Sum the integers starting from 1 and ending at N, where N is an integer of your choice.<br/><br/>
                   <b>N</b> is stored in <code>r4</code> and the <b>sum</b> is stored in <code>r2</code>''',
        'code':'''.text
_start:



''',
        'checker': check_sum_1_to_N
    })
