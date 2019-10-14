from exercises import *
import numpy as np

##########
# Linked list sum
def check_list_sum(asm):
    obj = nios2_as(asm.encode('utf-8'))
    r = require_symbols(obj, ['SUM', 'HEAD', '_start'])
    if r is not None:
        return (False, r)

    cpu = Nios2(obj=obj)


    tests = [([3, 2, 1], 6),
             ([1, 0, 4], 5),
             ([-1, 2, 15, 8, 6], 30)]

    head_addr = obj['symbols']['HEAD']

    feedback = ''

    cur_test = 1
    for tc,ans in tests:
        cpu.reset()
        for ii,n in enumerate(tc):

            next_ptr = head_addr + (ii+1)*8
            if ii == len(tc)-1:
                # Last element, write null for pointer
                next_ptr = 0
            cpu.storeword(head_addr+ii*8, next_ptr)
            cpu.storeword(head_addr+ii*8+4, np.uint32(n))

        instrs = cpu.run_until_halted(1000000)

        their_ans = np.int32(cpu.get_symbol_word('SUM'))
        if their_ans != ans:
            feedback += 'Failed test case %d: ' % cur_test
            feedback += 'SUM was %d (0x%08x), should be %d (0x%08x)' % \
                    (their_ans, np.uint32(their_ans), ans, np.uint32(ans))
            feedback += get_debug(cpu)
            del cpu
            return (False, feedback)

        feedback += 'Passed test case %d<br/>\n' % cur_test

        cur_test += 1

    del cpu
    return (True, feedback)


Exercises.addExercise('list-sum',
    {
        'public': True,
        'title': 'Sum a Linked List',
        'diff':  'medium',
        'desc': '''You are given a linked list node at addr <code>HEAD</code>.
                   Each list node consists of a word <code>next</code> that points to
                   the next node in the list, followed by a word <code>value</code>. The last
                   node in the list has its <code>next</code> pointer set to 0 (NULL).<br/><br/>

                   You can think of each node as being equivalent to the following C struct:<br/>
<pre>struct node {
    struct node *next;
    int          value;
};</pre><br/><br/>

                   Your task is to find the sum of all the <code>value</code>s in the list,
                   and write this sum to <code>SUM</code>,
                   then call the <code>break</code> instruction''',
        'code':'''.text
_start:


.data
SUM:    .word 0
HEAD:   .word N1, 5
N1:     .word N2, 3
N2:     .word N3, 10
N3:     .word 0,  6
''',
        'checker': check_list_sum
    })
