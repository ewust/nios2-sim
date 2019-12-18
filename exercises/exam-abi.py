
from exercises import *
import numpy as np
import struct
import math

##########
# callee-saved
def check_exam_abi(asm):
    # Need to insert a _start symbol
    new_start = '''.text
    sqrt:
        # check that they didn't save too much to the stack...
        #movia   r2, 0x04000000 - 4 - 12     # ra, r16, r18
        #blt    sp, r2, broken
        # Cheat and use an MMIO device :p
        movia   r2, 0x13371337
        stwio   r4, 0(r2)

        # Trash caller saved
        movui    r1, 0x1337
        movui    r3, 0x1338
        movui    r4, 0x9999
        movui    r5, 0x1010
        movui    r6, 0x2233
        movui    r7, 0x8765
        movui    r8, 0x9999
        movui    r9, 0x1234
        movui    r10, 0x8875
        movui    r11, 0x1818
        movui    r12, 0x4949
        movui    r13, 0x4141
        movui    r14, 0x3456
        movui    r15, 0x4af2
        movui    r16, 0xaaaa
        movui    r17, 0xbbbb

        ldwio   r2, 0(r2)
      broken:
        ret

    _start:
        movia   sp, 0x04000000 -4

        # assumes we setup
        call    dist

        break
    '''
    hp = new_start + asm
    nobj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(nobj, ['dist', '_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)


    class SQ(object):
        def __init__(self):
            self.val = 0

        def sqrt(self, val=None):
            if val is not None:
                #print('setting val %d' % val)
                self.val = val
            return int(math.sqrt(self.val))

    sq = SQ()

    tests = [(1, 1, 2, 2),
             (4, 8, 2, -1),
             (-1, -1, 8, -8),
             (2, 2, 1, 1),
             (123, -456, -987, 654)]

    feedback = ''
    for i,tc in enumerate(tests):
        cpu.reset()
        cpu.add_mmio(0x13371337, sq.sqrt)

        # init callee's so they can be trashed..
        for r in range(16, 24):
            cpu.set_reg(r, 0x8675309+r*0x111)

        cpu.set_reg(4, np.uint32(tc[0]))
        cpu.set_reg(5, np.uint32(tc[1]))
        cpu.set_reg(6, np.uint32(tc[2]))
        cpu.set_reg(7, np.uint32(tc[3]))

        ans = int(math.sqrt((tc[3] - tc[1])**2 + (tc[2] - tc[0])**2))

        cpu.run_until_halted(1000)

        got = cpu.get_reg(2)
        passed = (got == ans) and len(cpu.get_clobbered())==0 and len(cpu.get_error())==0
        if passed:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d<br/>\n' % (i+1)
            if got != ans:
                feedback += 'Got 0x%08x expected 0x%08x<br/>\n' % (got, ans)
            for addr,rid,_ in cpu.get_clobbered():
                feedback += 'Error: function @0x%08x clobbered r%d\n<br/>' % (addr, rid)
            feedback += '<br/>'
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, None)
    del cpu
    return (True, feedback, None)



Exercises.addExercise('exam-abi',
    {
        'public': False, #final f19
        'title': 'ABI',
        'diff': 'medium',
        'desc': '''You are given the following function to compute distance between two points. The function takes four parameters: x1, y1, x2, y2 and computes sqrt((x2-x1)**2 + (y2-y1)**2)
        Make this function ABI compliant.
        ''',
        'code':'''.text
dist:

    sub     r14, r6, r4
    sub     r15, r7, r5

    mul     r16, r14, r14
    mul     r17, r15, r15
    add     r4, r16, r17

    call    sqrt

    ret
''',
        'checker': check_exam_abi
    })
