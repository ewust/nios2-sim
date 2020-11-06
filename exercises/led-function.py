
#from exercises import Exercises
from exercises import *
import numpy as np

##########
# Set the LEDs to all on
def check_led_fn(asm):
    new_start = '''.text

    _start:
        movia   sp, 0x3fffffc

        # Assumes code calls setup
        call    led_sum
        break

    '''
    hp = new_start + asm
    obj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(obj, ['_start', 'led_sum'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=obj)


    tests = [(0x300, 0xff),
            (0, 1),
            (0, 0),
            (0x2a0, 0x00a),
            (0x066, 0x100),
            (0x2aa, 0x166)]


    feedback = ''
    for i,tc in enumerate(tests):
        cpu.reset()
        leds = Nios2.MMIO_Reg()
        cpu.add_mmio(0xFF200000, leds.access)

        for r in range(16, 24):
            cpu.set_reg(r, 0x8234*(r+i*10)+0x424)
        cpu.set_reg(4, np.uint32(tc[0]))
        cpu.set_reg(5, np.uint32(tc[1]))
        ans = (tc[0] + tc[1]) & 0x3ff

        cpu.run_until_halted(1000)

        if (leds.load() & 0x3ff) == ans and len(cpu.get_clobbered())==0 and len(cpu.get_error())==0:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d:<br/>\n' % (i+1)
            if (leds.load() & 0x3ff) != ans:
                feedback  += 'Got 0x%03x expected 0x%03x (0x%03x + 0x%03x)<br/>\n' % (leds.load()&0x3ff, ans, tc[0], tc[1])
            for addr,rid,_ in cpu.get_clobbered():
                feedback += 'Error: function @0x%08x clobbered r%d<br/>\n' % (addr, rid)
            feedback += '<br/>\n'
            feedback += get_debug(cpu, show_stack=True)
            del cpu
            return (False, feedback, None)
    del cpu
    return (True, feedback, None)


Exercises.addExercise('led-sum-fn',  # Exam 2 f20
    {
        'public': False,
        'title': 'Set LEDs on - ABI compliant function',
        'diff':  'easy',
        'desc': '''Write an ABI-compliant function, <code>led_sum</code>, which takes two integer parameters <code>(int a, int b)</code>, and sets the LEDs to the binary value of the sum of <code>a+b</code>.<br/><br/>
                    Hint: the LED MMIO address is <code>0xFF200000</code>''',
        'code':'''.text
led_sum:
    # Your code here
''',
        'checker': check_led_fn
    })
