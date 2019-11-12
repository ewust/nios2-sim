
from exercises import *
import struct

##########
# caller-saved
def check_caller_saved(asm):
    # Need to insert a _start symbol
    new_start = '''.text
    test_A:  .word 12
    test_B:  .word 42
    test_C:  .word 3
    test_D:  .word 8
    op_two:
        mul     r2, r4, r5
        # Pollute caller saved
        movi    r3, 898
        movi    r4, 898
        movi    r5, 898
        movi    r6, 898
        movi    r7, 898
        movi    r8, 898
        movi    r9, 898
        movi    r10, 898
        #movi    r11. 898
        movi    r11, 899
        movi    r12, 898
        movi    r13, 898
        movi    r14, 898
        movi    r15, 898
        ret

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


        movia   r4, test_A
        ldw     r4, 0(r4)
        movia   r5, test_B
        ldw     r5, 0(r5)
        movia   r6, test_C
        ldw     r6, 0(r6)
        movia   r7, test_D
        ldw     r7, 0(r7)

        call    op_four

        break
    '''
    hp = new_start + asm    # asm.replace('roll:', '_roll:') hmm..
    nobj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(nobj, ['op_four', '_start'])
    if r is not None:
        return (False, r)

    tests = [((10, 20, 30, 40), 10*20*30*40),
             ((3, 6, 0, 1), 0),
             ((1, 4, 1, 12), 4*12)]

    cpu = Nios2(obj=nobj)
    feedback = ''
    for i,tc in enumerate(tests):
        cpu.reset()

        a, b, c, d = tc[0]
        soln = tc[1]

        cpu.write_symbol_word('test_A', a)
        cpu.write_symbol_word('test_B', b)
        cpu.write_symbol_word('test_C', c)
        cpu.write_symbol_word('test_D', d)

        cpu.run_until_halted(1000)

        passed = (cpu.get_reg(2) == soln) and len(cpu.get_clobbered())==0
        if passed:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d<br/>\n' % (i+1)
            for addr,rid in cpu.get_clobbered():
                feedback += 'Error: function @0x%08x clobbered r%d\n<br/>' % (addr, rid)
            feedback += '<br/>'
            feedback += get_debug(cpu, show_stack=True)
            return (False, feedback, None)
    return (True, feedback, None)



Exercises.addExercise('caller-saved',
    {
        'public': False,
        'title': 'Caller Saved',
        'diff': 'medium',
        'desc': '''You are given the following function, but it is missing two parts for you to fill in: saving registers in the function prologue and restoring them in the epilogue.
        ''',
        'code':'''.text


# int op_four(int a, b, c, d)
op_four:
    addi    sp, sp, -8
    stw     ra, 4(sp)
                            # r4 = a
                            # r5 = b
    call    op_two          # x = op_two(a, b)
    stw     r2, 0(sp)       # store x

    mov     r4, r6          # r4 = c
    mov     r5, r7          # r5 = d
    call    op_two          # y = op_two(c, d)

    ldw     r4, 4(sp)     # r4 = x
    mov     r5, r2          # r5 = y
    call    op_two          # op_two(x, y)

    ldw     ra, 4(sp)
    addi    sp, sp, 8
    ret
''',

        'checker': check_caller_saved
    })
