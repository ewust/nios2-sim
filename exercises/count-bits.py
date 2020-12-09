from exercises import *
import numpy as np

def count_bits(asm):

    new_start = '''.text
    _start:
        movia   sp, 0x3fffffc
        # Test cases will set r4

        call    bits

        break
        '''

    hp = new_start + asm
    obj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(obj, ['_start', 'bits'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)

    def bits(n):
        b = 0
        while n>0:
            b += (n & 1)
            n>>=1
        return b


    tests = [5, 21, 0, 0x55555555, 0x7fff0fff, 0x80000000, 0x0000ffff, 0xaaaaaaaa, 0xdeadbeef, 0x7d8fc784]

    feedback = ''
    cur_test = 1
    tot_instr = 0
    for tc in tests:
        cpu.reset()
        ans = bits(tc)

        cpu.set_reg(4, np.uint32(tc))

        instrs = cpu.run_until_halted(5000)
        tot_instr += instrs

        # Read back out what they return
        their_ans = np.uint32(cpu.get_reg(2))

        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'Provided 0x%08x<br/>\n' % (tc)
            feedback += 'Your answer: %d<br/>\n' % their_ans
            feedback += 'Correct answer: %d<br/>\n' % ans
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
Exercises.addExercise('count-bits',
    {
        'public': False,
        'title': 'Count bits',
        'diff': 'medium',
        'desc': '''
        Write an ABI-compliant Nios2 assembly function <code>bits</code> that counts the number of 1 bits in the provided argument.<br/><br/>

        Your function will take exactly one unsigned 32-bit integer <code>N</code>, and should return the number of set bits. For instance, if you
        are given N=21 (binary 0b00010101), you should return 3, since 3 bits are set to 1.
        ''',
        'code':'''.text
bits:
    # Your code here
''',
        'checker': count_bits,
    })
