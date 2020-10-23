
from exercises import *

############
# Fib
def check_factorial(asm):
    new_start = '''.text
    TEST_N: .word 3
    _start:
        movia   sp, 0x04000000
        subi    sp, sp, 4

        # polute callee's
        movui    r16, 0xaaa2
        movui    r17, 0xbbb4
        movui    r18, 0xccc1
        movui    r19, 0xddd0
        movui    r20, 0xeee2
        movui    r21, 0x131f
        movui    r22, 0x831e
        movui    r23, 0x918c

        movia   r4, TEST_N
        ldw     r4, 0(r4)
        call    factorial
        break
    '''
    hp = new_start + asm    # asm.replace('roll:', '_roll:') hmm..
    nobj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(nobj, ['_start', 'TEST_N', 'factorial'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)

    tests = [(3, 6), (5, 120), (10, 3628800), (12, 479001600)]
    feedback = ''
    extra_info = ''
    cur_test = 1
    clobbered = set()
    for n,ans in tests:
        cpu.reset()
        cpu.write_symbol_word('TEST_N', n)

        instrs = cpu.run_until_halted(100000000)


        # Check for clobbered registers first
        # in case this is why they failed
        clobs = cpu.get_clobbered()
        if len(clobs) > 0:
            for pc,rid,_ in clobs:
                if (pc,rid) not in clobbered:
                    extra_info += 'Warning: Function @0x%08x clobbered r%d\n<br/>' % (pc, rid)
                    clobbered.add((pc, rid))

        # Check answer
        their_ans = cpu.get_reg(2)
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'factorial(%d) returned %d, should have returned %d' %\
                    (n, their_ans, ans)
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, extra_info)

        feedback += 'Passed test case %d<br/>\n' % cur_test
        cur_test += 1

    del cpu
    return (True, feedback, extra_info)

Exercises.addExercise('factorial',
    {
        'public': True,
        'title': 'Factorial',
        'diff':  'medium',
        'desc':  '''Factorial can be defined recursively as <code>f(n) = n*f(n-1)</code>, with a base case value of <code>f(0) = 1</code>.<br/><br/>
        Your task is to write a function <code>factorial</code> which takes a single number <code>n</code> and returns <code>f(n)</code>.''',
        'code':'''.text
factorial:
    # Write your code here

    ret
''',
        'checker': check_factorial
    })
