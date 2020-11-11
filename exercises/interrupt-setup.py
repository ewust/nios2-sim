
#from exercises import Exercises
from exercises import *

##########
# test_idx
#   = 0 - full check (did interrupt happen?)
#   = 1 - check for MMIO set
#   = 2 - check for ienable set
#   = 3 - check for global interrupts
def check_interrupt_setup(asm, test_idx=0):
    new_asm = '''
    .section .reset, "ax"
        br      _start

    .section .exceptions, "ax"
    isr:
        subi    sp, sp, 16
        stw     r4, 0(sp)
        stw     r5, 4(sp)

        rdctl   r4, ipending
        andi    r4, r4, 1<<3
        beq     r4, r0, out_isr

        movia   r5, 0x13371337
        stw     r0, 0(r5)

    out_isr:
        ldw     r5, 4(sp)
        ldw     r4, 0(sp)
        addi    sp, sp, 16
        eret
    '''


    hp = new_asm + asm    # asm.replace('roll:', '_roll:') hmm..
    nobj = nios2_as(hp.encode('utf-8'))
    r = require_symbols(nobj, ['_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)

    class MMObj(object):
        def __init__(self, imask=0):
            self.imask = imask
            self.rolls = []
            self.feedback = ''
            self.passed = False

        def intmask(self, val=None):
            if val is not None:
                self.imask = val
            return 0
        def nop(self, val=None):
            cpu.halt()
            return 0

        def data(self, val=None):
            return 0

        def winner(self, val=None):
            self.passed = True


    device = MMObj(imask=0)
    cpu.reset()
    cpu.add_mmio(0xFF201100, device.data)
    cpu.add_mmio(0xFF201104, device.nop)
    cpu.add_mmio(0xFF201108, device.intmask)
    cpu.add_mmio(0xFF20110c, device.nop)
    cpu.add_mmio(0x13371337, device.winner)

    # Run for a bit
    for i in range(1000):
        cpu.one_step()

    # setup an interrupt
    if device.imask == 1:
        cpu.set_ctl_reg(4, 1<<3)    # ipending = enable IRQ3

    for i in range(1000):
        cpu.one_step()


    passed = device.passed and len(cpu.get_clobbered())==0
    if test_idx == 1: # only check MMIO
        passed = (device.imask == 1)
    elif test_idx == 2: # only check ienable
        passed = ((cpu.get_ctl_reg(3)&(1<<3))!=0)
    elif test_idx == 3: # only check status
        passed = ((cpu.get_ctl_reg(0)&1)==1)


    if not(passed):
        feedback = 'Interrupt did not occur<br/>\n<br/>\n' 

        status = cpu.get_ctl_reg(0)
        ienable = cpu.get_ctl_reg(3)
        feedback += 'status:   0x%08x<br/>\n' % status
        feedback += 'estatus:  0x%08x<br/>\n' % cpu.get_ctl_reg(1)
        feedback += 'ienable:  0x%08x<br/>\n' % ienable
        feedback += 'ipending: 0x%08x<br/>\n' % cpu.get_ctl_reg(4)

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
    return (True, 'Passed test case %d'%test_idx)

Exercises.addExercise('interrupt-setup',
    {
        'public': False,
        'title': 'Interrupt Setup',
        'diff':  'medium',
        'desc': '''There's a new MMIO device that will generate an interrupt
        for IRQ 3 (remember: we start at IRQ0). Write code to <b>setup</b>
        interrupts. The MMIO's interrupt mask register is at address <code>0xFF201108</code>.
        Writing a 1 to this address will enable the device to generate interrupts. Make sure to remember all the steps in enabling interrupts!
        ''',
        'code':'''.text
.global _start
_start:
    movia   sp, 0x04000000 - 4
    # Write your interrupt setup code here.


    # Keep this busy loop
loop:
    br      loop
''',
        'checker': check_interrupt_setup
    })

for i in range(1,4):
    Exercises.addExercise('interrupt-setup-%d'%i,
        {'public':False,
        'title': 'Interrupt Setup - test %d'%i,
        'diff': 'medium',
        'desc': '',
        'code':'',
        'checker': lambda asm,tc=i: check_interrupt_setup(asm, tc) })

