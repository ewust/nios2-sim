
from exercises import *

###########
# Project 1
def check_proj1(asm):
    obj = nios2_as(asm.encode('utf-8'))
    cpu = Nios2(obj=obj)

    class p1grader(object):
        def __init__(self, test_cases=[]):
            # Array of (sw_val, expected_led_val)
            self.test_cases = test_cases
            self.cur_test = 0
            self.feedback = ''
            self.num_passed = 0

        def write_led(self, val):
            # Assert correct answer
            sw, expected = self.test_cases[self.cur_test]
            if val != expected: # Check that they wrote to LEDs exactly
                if (val&0x3ff) != expected: # only warn if the LEDs would have masked for them..

                    self.feedback += 'Failed test case %d: ' % (self.cur_test+1)
                    self.feedback += 'LEDs set to %s (should be %s) for SW %s' % \
                                (bin(val&0x3ff), bin(expected), bin(sw))
                    self.feedback += get_debug(cpu)
                    cpu.halt()
                    return
                self.feedback += 'Test case %d: ' %(self.cur_test+1)
                self.feedback += 'Warning: wrote 0x%08x (instead of 0x%08x) to LEDs for SW %s;' %\
                                (val, expected, bin(sw))
                self.feedback += ' upper bits ignored.\n'
            self.feedback += 'Passed test case %d<br/>\n' % (self.cur_test+1)
            self.cur_test += 1
            self.num_passed += 1
            if self.cur_test >= len(self.test_cases):
                cpu.halt()

        def read_sw(self):
            if self.cur_test > len(self.test_cases):
                print('Error: read_sw after we should have halted?')
                return 0    # ??
            sw, led = self.test_cases[self.cur_test]
            return sw

    tests = [(0, 0),
            (0b0000100001, 2),
            (0b0001100010, 5),
            (0b1011101110, 37),
            (0b1111111111, 62),
            (0b1111011111, 61),
            (0b0000111111, 32)]

    p1 = p1grader(tests)

    cpu.add_mmio(0xFF200000, p1.write_led)
    cpu.add_mmio(0xFF200040, p1.read_sw)

    #cpu.mmios[0xFF200000] = p1.write_led
    #cpu.mmios[0xFF200040] = p1.read_sw

    instrs = cpu.run_until_halted(10000)

    print('Passed %d of %d' % (p1.num_passed, len(tests)))
    err = cpu.get_error()
    del cpu
    return (p1.num_passed==len(tests), err + p1.feedback)

Exercises.addExercise('proj1',
    {
        'public': True,
        'title': 'Project 1',
        'diff': 'medium',
        'desc': '''Project 1 adder.s''',
        'code':'''.text
_start:
    movia   r4, 0xFF200000
    movia   r5, 0xFF200040

loop:
    ldwio   r6, 0(r5)


    stwio   r6, 0(r4)
    br      loop
''',
        'checker': check_proj1
    })
