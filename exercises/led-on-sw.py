
#from exercises import Exercises
from exercises import *

##########
# Set the LEDs to all on
def check_led_sw(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=obj)


    class BtnLeds(object):
        def __init__(self, test_cases=[]):
            self.test_cases = test_cases
            self.cur_test = 0
            self.feedback = ''
            self.num_passed = 0
            self.failed = False
            self.leds = 0

        def write_led(self, val):
            self.leds = val
            #cpu.halt()

        def check(self):
            # Check for correct answer
            sw, expected = self.test_cases[self.cur_test]
            if self.leds != expected:
                if (self.leds&0x3ff) != expected: # fail only if even masked it wouldn't have worked
                    self.feedback += 'Failed test case %d: ' % (self.cur_test+1)
                    self.feedback += 'LEDs set to %s (should be %s) for BTN %s' %\
                            (bin(self.leds&0x3ff), bin(expected), bin(sw))
                    self.feedback += get_debug(cpu, show_error=False)
                    self.failed = True
                    cpu.halt()
                    return
                self.feedback += 'Test case %d: ' % (self.cur_test+1)
                self.feedback += 'Warning: wrote 0x%08x (instead of 0x%08x) to LEDs for BTN %s;' %\
                        (self.leds, expected, bin(sw))
                self.feedback += ' upper bits ignored.<br/>\n'
            self.feedback += 'Passed test case %d<br/>\n' % (self.cur_test+1)
            self.cur_test += 1
            self.num_passed += 1
            if self.cur_test >= len(self.test_cases):
                cpu.halt()

        def read_sw(self):
            if self.cur_test > len(self.test_cases):
                print('Error: read_sw after we should have halted?')
                return 0
            sw, led = self.test_cases[self.cur_test]
            return sw

    tests = [(0, 0),
             (0b01, 0x3ff),
             (0b00, 0),
             (0b10, 0x000),
             (0b11, 0x3ff),
             (0b00, 0),
             (0b01, 0x3ff),
             (0b1111111111, 0x3ff),
             (0b1111111110, 0),
             (0b0,  0)]

    mmio = BtnLeds(tests)

    cpu.add_mmio(0xFF200000, mmio.write_led)
    cpu.add_mmio(0xFF200040, mmio.read_sw)

    instrs = 0
    for i in range(len(tests)):
        instrs += cpu.run_until_halted(1000)
        mmio.check()
        if mmio.failed:
            break
        cpu.unhalt()

    #err = cpu.get_error()
    del cpu
    return (mmio.num_passed==len(tests), mmio.feedback)


Exercises.addExercise('led-on-sw',
    {
        'public': False,
        'title': 'Set LEDs on when switch is on',
        'diff':  'medium',
        'desc': '''
        Hint: the LED MMIO address is <code>0xFF200000</code>, and the switch is at <code>0xFF200040</code>''',
        'code':'''.text
_start:
''',
        'checker': check_led_sw
    })
