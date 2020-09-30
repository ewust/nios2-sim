
#from exercises import Exercises
from exercises import *

##########
# Set the LEDs to all on

def check_led_sw_partial1(asm):
    return check_led_sw_partial(asm, False)
def check_led_sw_partial2(asm):
    return check_led_sw_partial(asm, True)

def check_led_sw_partial(asm, do_tcs=False):
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
            self.did_read_sw = False
            self.did_wrote_sw = False
            self.did_read_led = False
            self.did_wrote_led = False

        def write_led(self, val):
            if val is None:
                self.did_read_led = True
            self.did_wrote_led = True
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

        def read_sw(self, val=None):
            self.did_read_sw = True
            if val is not None:
                self.did_wrote_sw = True

            if self.cur_test > len(self.test_cases):
                print('Error: read_sw after we should have halted?')
                return 0
            sw, led = self.test_cases[self.cur_test]
            return sw

    tests = [(0, 0),
             (0b01, 0x3ff),
             (0b00, 0),
             (0b11, 0x3ff),
             (0b00, 0),
             (0b01, 0x3ff),
             (0b1111111111, 0x3ff),
             (0b0,  0)]

    mmio = BtnLeds(tests)

    cpu.add_mmio(0xFF200000, mmio.write_led)
    cpu.add_mmio(0xFF200040, mmio.read_sw)

    instrs = 0
    for i in range(len(tests)):
        instrs += cpu.run_until_halted(1000)
        if do_tcs:
            mmio.check()
            if mmio.failed:
                break
        cpu.unhalt()

    del cpu
    if do_tcs:
        return (mmio.num_passed==len(tests), mmio.feedback)
    else:
        feedback = ''
        passed = mmio.did_wrote_led and not(mmio.did_read_led) and mmio.did_read_sw and not(mmio.did_wrote_sw)
        feedback += 'Read switches<br/>\n' if mmio.did_read_sw else 'Did not read switches'
        feedback += 'Incorrectly wrote switches<br/>\n' if mmio.did_wrote_sw else ''

        feedback += 'Wrote LEDs<br/>\n' if mmio.did_wrote_led else 'Did not write LEDs'
        feedback += 'Incorrectly read LEDs<br/>\n' if mmio.did_read_led else ''

        return (passed, feedback)


Exercises.addExercise('led-on-sw-partial1',
    {
        'public': False,
        'title': 'Set LEDs on when switch is on',
        'diff':  'medium',
        'desc': '''
        Hint: the LED MMIO address is <code>0xFF200000</code>, and the switch is at <code>0xFF200040</code>''',
        'code':'''.text
_start:
''',
        'checker': check_led_sw_partial1
    })


Exercises.addExercise('led-on-sw-partial2',
    {
        'public': False,
        'title': 'Set LEDs on when switch is on',
        'diff':  'medium',
        'desc': '''
        Hint: the LED MMIO address is <code>0xFF200000</code>, and the switch is at <code>0xFF200040</code>''',
        'code':'''.text
_start:
''',
        'checker': check_led_sw_partial2
    })
