
#from exercises import Exercises
from exercises import *

##########
# Set the LEDs to all on
def check_sum_1_to_N(asm):
    obj = nios2_as(asm.encode('utf-8'))
    cpu = Nios2(obj=obj)


    # Make a MMIO rw/register
    leds = Nios2.MMIO_Reg()
    # Set the cpu's LED MMIO callback to that reg's access function
    cpu.add_mmio(0xFF200000, leds.access)
    #cpu.mmios[0xFF200000] = leds.access

    instrs = cpu.run_until_halted(1000000)

    feedback = ''
    if (leds.load() & 0x3ff) != 0x3ff:
        feedback += 'Failed test case 1: '
        feedback += 'LEDs are set to %s (should be %s)' % (format((leds.load()&0x3ff), '#012b'), bin(0x3ff))
        feedback += get_debug(cpu)
        del cpu
        return (False, feedback)

    del cpu
    return (True, 'Passed test case 1')


Exercises.addExercise('sum-1-N',
    {
        'public': True,
        'title': 'Sum integers from 1-N',
        'diff':  'easy',
        'desc': '''Sum the integers starting from 1 and ending at N, where N is an integer of your choice.<br/><br/>''',
        'code':'''.text
_start:
''',
        'checker': check_sum_1_to_N
    })
