from exercises import *
import numpy as np

def fizz_buzz(n):
    def multiples(k, n):
        return set(filter(lambda x: (x%k)==0, range(1,n+1)))
    return sum(multiples(3, n) ^ multiples(5, n))

def check_fizz_buzz(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [16, 29, 30, 34, 36, 42, 50, 100, 384, 511]

    feedback = ''
    cur_test = 1
    tot_instr = 0
    for tc in tests:
        cpu.reset()

        ans = fizz_buzz(tc)

        cpu.write_symbol_word('N', tc)

        instrs = cpu.run_until_halted(50000)
        tot_instr += instrs

        their_ans = np.int32(cpu.get_reg(2))

        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'N=%d<br/>' % tc
            feedback += 'Your answer: %s<br/>\n' % their_ans
            feedback += 'Correct answer: %s<br/>\n' % ans
            feedback += get_debug(cpu)
            feedback += get_regs(cpu)
            del cpu
            return (False, feedback, None)
        feedback += 'Passed test case %d<br/>\n' % cur_test
        cur_test += 1
    del cpu
    extra_info = '%d total instructions' % tot_instr
    return (True, feedback, extra_info)


#########
# If/else
Exercises.addExercise('fizz-buzz',
    {
        'public': True,
        'title': 'Fizz Buzz sum',
        'diff': 'medium',
        'desc': '''
        Given <b>N</b>, sum the integers 1 to <b>N</b> that are multiples of 3, or multiples of 5, but not both. <br/><br/>

        For example, if <b>N</b>=16, you would return <code>3+5+6+9+10+12 = 45</code>. Note that you would not include 15 in the sum, as it is a multiple of both 3 and 5.
        <br/><br/>
        Put the sum in <code>r2</code>, then execute the <code>break</code> instruction.<br/><br/>''',
        'code':'''.text
_start:
    # Loading N into r4:
    movia   r4, N
    ldw     r4, 0(r4)
    movi    r2, 0

    # Your code here

.data
N:  .word 16
''',
        'checker': check_fizz_buzz,
    })
