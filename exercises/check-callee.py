
from exercises import *
import struct

##########
# callee-saved
def check_callee_saved(asm):
    obj = nios2_as(asm.encode('utf-8'))
    # Need to insert a _start symbol
    new_start = '''.text
    test_A:  .word 12
    test_B:  .word 42
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

        call    foo

        break
    '''
    nobj = hotpatch(obj, new_start)

    tests = [(12, 42, 10230),
             (5, 5, 730),
             (0, 0, 0)]

    cpu = Nios2(obj=nobj)
    feedback = ''
    for i,tc in enumerate(tests):
        cpu.reset()

        cpu.write_symbol_word('test_A', tc[0])
        cpu.write_symbol_word('test_B', tc[1])

        cpu.run_until_halted(1000)

        passed = (cpu.get_reg(2) == tc[2]) and len(cpu.get_clobbered())==0
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



Exercises.addExercise('callee-saved',
    {
        'public': False,
        'title': 'Callee Saved',
        'diff': 'medium',
        'desc': '''You are given the following function, but it is missing two parts for you to fill in: saving registers in the function prologue and restoring them in the epilogue.
        ''',
        'code':'''.text

foo:
    # Write your function prologue here

    add     r2, r4, r5
    mov     r6, r4
    slli    r12, r6, 4
    mul     r16, r2, r12
    sub     r18, r2, r12
    add     r2, r16, r18

    # Write your function epilogue here
    ret''',
        'checker': check_callee_saved
    })
