
#from exercises import Exercises
from exercises import *

##########
# test_idx
#   = 0 - full check (did interrupt happen?)
#   = 1 - check for MMIO set
#   = 2 - check for ienable set
#   = 3 - check for global interrupts
def check_interrupt_setup2(asm, test_idx=0):
    nobj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(nobj, ['_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)


    cpu.set_reg(27, 0x3fffffc)


    # Run for a bit
    for i in range(1000):
        cpu.one_step()


    passed = len(cpu.get_clobbered())==0
    passed &= cpu.get_ctl_reg(3) == ((1<<3) | (1<<5))
    passed &= (cpu.get_ctl_reg(0)&1)==1


    if not(passed):
        feedback = 'Interrupt not setup<br/>\n<br/>\n' 

        status = cpu.get_ctl_reg(0)
        ienable = cpu.get_ctl_reg(3)
        feedback += 'status:   0x%08x<br/>\n' % status
        feedback += 'ienable:  0x%08x<br/>\n' % ienable

        feedback += 'Global interrupts (PIE): '
        if (cpu.get_ctl_reg(0) & 1) == 0:
            feedback += 'disabled<br/>\n'
        else:
            feedback += 'enabled<br/>\n'

        feedback += 'IRQs enabled: '
        if ienable == 0:
            feedback += 'none<br/>\n'
        else:
            feedback += ', '.join(['IRQ %d' % d for d in range(32) if ienable&(1<<d)]) + '<br/>\n'

        feedback += get_debug(cpu) + get_clobbered(cpu)
        del cpu
        return (False, feedback)

    del cpu
    return (True, 'Passed test case 1')

Exercises.addExercise('interrupt-setup2',
    {
        'public': False,
        'title': 'Interrupt Setup',
        'diff':  'medium',
        'desc': '''
        Write code that enables interrupts from IRQ 3 and 5, and turns on interrupts globally. You may assume the stack and the relevant MMIO devices have been setup already.
        ''',
        'code':'''.text
.global _start
_start:
    # Write your interrupt setup code here.


    # Keep this busy loop
loop:
    br      loop
''',
        'checker': check_interrupt_setup2
    })

