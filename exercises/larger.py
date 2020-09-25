from exercises import *
import numpy as np

def check_larger(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [[13, 40],
             [18, 13],
             [22, 13],
             [80, 18],
             [-8, -6],
             [-3, -2],
             [9, 9],
             [13, -13],
             [-13, 13],
             [0, 10],
            ]

    feedback = ''
    cur_test = 1
    tot_instr = 0
    for tc in tests:
        cpu.reset()
        ans = max(tc)

        cpu.set_reg(4, np.uint32(tc[0]))
        cpu.set_reg(5, np.uint32(tc[1]))

        instrs = cpu.run_until_halted(1000)
        tot_instr += instrs

        their_ans = np.int32(cpu.get_reg(2))

        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'r4=%d, r5=%d<br/>\n' % (tc[0], tc[1])
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
Exercises.addExercise('larger',
    {
        'public': False,
        'title': 'Which number is larger?',
        'diff': 'easy',
        'desc': '''
        You are given 2 signed integers in <code>r4</code> and <code>r5</code> respectively (don't set these, we will provide those values for you).<br/><br/>
        Write code to find the larger of these values, and put the result in <code>r2</code>, then execute the <code>break</code> instruction.<br/><br/>''',
        'code':'''.text
_start:
''',
        'checker': check_larger,
    })
