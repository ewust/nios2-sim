from exercises import *

def check_mmio(asm):
    nobj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(nobj, ['_start'])
    if r is not None:
        return (False, r)
    cpu = Nios2(obj=nobj)


    class Dice(object):
        def __init__(self, rolls=[]):
            self.idx = 0
            self.rolls = rolls
            self.feedback = ''
            self.missiles = 'unlaunched'


        def roll(self, val=None):
            if val is not None:
                # launching the missiles...
                if self.idx != len(self.rolls):
                    self.feedback += 'Didn\'t roll the dice enough times\n<br/>'
                    cpu.halt()
                    return 888
                if val != 1:
                    self.feedback += 'Missiles exploded in place. KABOOM!\n<br/>'
                    cpu.halt()
                    self.missiles = 'exploded'
                    return 777
                self.missiles = 'launched'
                return 0

            if self.idx >= len(self.rolls):
                self.feedback += 'Rolled the dice too many times\n<br/>'
                cpu.halt()
                return 999
            r = self.rolls[self.idx]
            self.idx += 1
            return r

    tests = [([1, 4], False),
             ([3, 2], False),
             ([1, 1], True),
             ([3, 1], False),
             ([6, 6], False),
             ([3, 3], False),
            ]

    feedback = ''
    for i,tc in enumerate(tests):
        rolls, launch = tc
        dice = Dice(rolls=rolls)
        cpu.reset()
        cpu.add_mmio(0xFF203300, dice.roll)

        cpu.run_until_halted(10000)

        passed = (launch and dice.missiles == 'launched') or (not(launch) and dice.missiles == 'unlaunched')
        passed &= dice.feedback==''
        if passed:
            feedback += 'Passed test case %d<br/>\n' % (i+1)
        else:
            feedback += 'Failed test case %d<br/>\n' % (i+1)
            feedback += dice.feedback + '<br/>\n'
            feedback += get_debug(cpu)
            del cpu
            return (False, feedback, None)
    del cpu
    return (True, feedback, None)


##########
# Function that calls another function
Exercises.addExercise('exam-mmio',
    {
        'public': False,
        'title': '',
        'diff': 'easy',
        'desc': '''Na
        ''',
        # MMIO at 0xFF203300
        # read a word from it, and you get a single dice roll from it (1-6)
        # write a word to it, and the missiles launch if you write 1 to it
        #   otherwise explode in place.
        # (Carefully!!) Write code to roll the dice twice, and if you get
        # snake eyes (1 and 1), launch the missiles. Otherwise, call break (and don't write
        # to the MMIO address!!)
        'code':'''
.equ    MAGIC_MMIO_ADDR,     0xFF203300
.text
_start:
    # Write your code here

''',
        'checker': check_mmio
    })

