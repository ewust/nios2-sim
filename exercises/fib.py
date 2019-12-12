
from exercises import *

############
# Fib
def check_fib(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['N', 'F', '_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    tests = [(10, 55), (15, 610), (12, 144), (30, 832040)]
    feedback = ''
    extra_info = ''
    cur_test = 1
    clobbered = set()
    for n,ans in tests:
        cpu.reset()
        cpu.write_symbol_word('N', n)

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
        their_ans = cpu.get_symbol_word('F')
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'fib(%d) returned %d, should have returned %d' %\
                    (n, their_ans, ans)
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, extra_info)

        feedback += 'Passed test case %d<br/>\n' % cur_test
        cur_test += 1

    del cpu
    return (True, feedback, extra_info)

Exercises.addExercise('fibonacci',
    {
        'public': True,
        'title': 'Fibonacci Sequence',
        'diff':  'medium',
        'desc':  '''The  Fibonacci Sequence is computed as <code>f(n) = f(n-1) + f(n-2)</code>. We must define two <b>base case</b> values: <code>f(0) = 0</code> and <code>f(1) = 1</code>.<br/><br/>

                Thus, the first values of this sequence are: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, etc.<br/><br/>

                Your task is to write a function <code>fib</code> which takes a single number <code>n</code> and returns <code>f(n)</code> as defined above by the Fibonacci Sequence.''',
        'code':'''.text
fib:
    # Write your code here

    ret

_start:
    # You should probably test your program!
    # Feel free to change the value of N, but leave the rest of
    # this code as is.
    movia   sp, 0x04000000  # Setup the stack pointer
    subi    sp, sp, 4

    movia   r4, N
    ldw     r4, 0(r4)

    call    fib             # fib(N)

    movia   r4, F
    stw     r2, 0(r4)       # store r2 to F
    break                   # r2 should be 55 here.
.data
N:  .word 10
F:  .word 0
''',
        'checker': check_fib
    })
