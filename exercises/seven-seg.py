
#from exercises import Exercises
from exercises import *

##########
# Set the LEDs to all on
def check_ee3350(asm):
    obj = nios2_as(asm.encode('utf-8'))
    cpu = Nios2(obj=obj)

    segs1 = Nios2.MMIO_Reg()
    segs2 = Nios2.MMIO_Reg()

    cpu.add_mmio(0xFF200020, segs1.access)
    cpu.add_mmio(0xFF200030, segs2.access)

    instrs = cpu.run_until_halted(10000)

    correct = [0x79, 0x79, 0x4f, 0x4f, 0x6d, 0x3f]
    s2 = segs2.load()
    s1 = segs1.load()
    provided = [((s2>>8)&0xff), (s2&0xff), ((s1>>24)&0xff), ((s1>>16)&0xff), ((s1>>8)&0xff), (s1&0xff)]


    feedback = ''
    if provided != correct:
        feedback += 'Failed test case 1: '
        for i in range(len(correct)):
            good = 'incorrect'
            if correct[i] == provided[i]:
                good = 'correct'
            feedback += 'HEX%d = 0x%02x (%s)<br/>\n' % ((5-i), provided[i], good)

        feedback += get_debug(cpu)
        del cpu
        return (False, feedback)

    del cpu
    return (True, 'Passed test case 1')


Exercises.addExercise('seven-seg',
    {
        'public': True,
        'title': 'Set 7 segments to EE3350',
        'diff':  'easy',
        'desc': '''
        Set the 7-segment displays to display <code>EE3350</code>, then call the <code>break</code> instruction.<br/><br/>
            Hint: the 7-segment MMIO address is <code>0xFF200020</code> for HEX0-HEX3, and <code>0xFF200030</code> for HEX4-HEX5.''',
        'code':'''.text
_start:
''',
        'checker': check_ee3350,
    })
