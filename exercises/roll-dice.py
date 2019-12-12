from exercises import *

def check_roll_dice(asm):
    new_start = '''.text
    .equ    ROLL_MMIO, 0x13370000
    TEST_N: .word 3
    roll:
        movia   r4, ROLL_MMIO
        ldwio   r2, 0(r4)

        # pollute caller-saved
        movui   r5, 0xa0a0
        movui   r6, 0xbcbc
        movui   r7, 0x8889
        movui   r8, 0xccdc
        movui   r9, 0x3317
        movui   r10, 0x9981
        movui   r11, 0x4434
        movui   r12, 0x3a2c
        movui   r13, 0xaacc
        movui   r14, 0x44ee
        movui   r15, 0x4142
        ret
    _start:
        movia   sp, 0x04000000
        subi    sp, sp, 4

        # TODO: some students assuming registers start with a 0 value...could pollute those too
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
        call    sum_dice
        break
    '''
    #nobj = hotpatch(obj, new_start)
    hp = new_start + asm    # asm.replace('roll:', '_roll:') hmm..
    nobj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(nobj, ['TEST_N', '_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)

    class Dice(object):
        def __init__(self, rolls=[]):
            self.idx = 0
            self.rolls = rolls
            self.feedback = ''

        def roll(self, val=None):
            if self.idx >= len(self.rolls):
                self.feedback += 'Called roll() too many times\n<br/>'
                cpu.halt()
                return 999
            r = self.rolls[self.idx]
            self.idx += 1
            return r

    tests = [[1, 1],
             [3, 4, 2, 6, 6],
             [1, 1, 5, 2, 2, 3, 5, 2, 5],
            ]

    feedback = ''
    for i,tc in enumerate(tests):
        dice = Dice(rolls=tc)
        cpu.reset()
        cpu.write_symbol_word('TEST_N', len(tc))
        cpu.add_mmio(0x13370000, dice.roll)

        cpu.run_until_halted(100000)

        passed = (cpu.get_reg(2) == sum(tc)) and len(cpu.get_clobbered())==0 and dice.feedback==''
        if passed:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d<br/>\n' % (i+1)
            if (cpu.get_reg(2) != sum(tc)):
                feedback += 'Error: sum returned %d for test case %s. Expected %d' % (cpu.get_reg(2), tc, sum(tc))
            for addr,rid,_ in cpu.get_clobbered():
                feedback += 'Error: function @0x%08x clobbered r%d\n<br/>' % (addr, rid)
            feedback += '<br/>'
            feedback += dice.feedback + '<br/>\n'
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, None)
    del cpu
    return (True, feedback, None)


##########
# Function that calls another function
Exercises.addExercise('roll-dice',
    {
        'public': False,
        'title': 'Sum rolled dice',
        'diff': 'medium',
        'desc': '''We've defined a function <code>roll</code>
        ''',
        'code':'''.text

sum_dice:
    # Write your function here

''',
        'checker': check_roll_dice
    })

