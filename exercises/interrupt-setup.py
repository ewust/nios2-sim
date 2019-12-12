
#from exercises import Exercises
from exercises import *

##########
# Set the LEDs to all on
def check_interrupt_setup(asm):
    new_asm = '''
    .section .reset, "ax"
        br      _start

    .section .exceptions, "ax"
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

    if not(device.passed) or len(cpu.get_clobbered())>0:
        feedback = 'Interrupt did not occur<br/>\n' + get_debug(cpu) + get_clobbered(cpu)
        del cpu
        return (False, feedback)

    del cpu
    return (True, 'Passed test case 1')

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
