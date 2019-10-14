from exercises import *
import collections
import html


def check_uart(asm):
    obj = nios2_as(asm.encode('utf-8'))
    cpu = Nios2(obj=obj)

    class uart(object):
        def __init__(self, name='', step_roll=(1,1)):
            self.name = name + '\n'
            self.idx = 0
            self.rx_fifo = collections.deque()
            self.tx_fifo = collections.deque()
            self.recvd = ''
            self.tx_step = 0
            self.rx_step = 0
            self.tx_step_roll = step_roll[0]
            self.rx_step_roll = step_roll[1]
            self.feedback = ''
            self.extra_info = ''

        def step(self):
            self.tx_step += 1
            self.rx_step += 1
            if self.tx_step == self.tx_step_roll:
                self.tx_step = 0
                # Read from the tx_fifo
                if len(self.tx_fifo) > 0:
                    self.recvd += chr(self.tx_fifo.popleft())

            if self.rx_step == self.rx_step_roll:
                self.rx_step = 0
                # Write to the rx_fifo
                if self.idx < len(self.name):
                    self.rx_fifo.append(ord(self.name[self.idx]))
                    self.idx += 1

        def uart_data(self, val=None):
            self.step()
            if val is not None:
                # stwio
                chr_data = val & 0xff
                if len(self.tx_fifo) >= 64:
                    # Lost the data!
                    self.extra_info += 'Warning: Wrote character \'%s\' (0x%02x) while transmit FIFO full!\n<br/>' %\
                            (html.escape(chr(chr_data)), chr_data)

                    self.extra_info += 'tx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.tx_fifo), html.escape(''.join([chr(c) for c in self.tx_fifo])))
                    self.extra_info += 'rx_fifo: %s <code>%s</code>\n<br/><br/>' % \
                        (list(self.rx_fifo), html.escape(''.join([chr(c) for c in self.rx_fifo])))
                    #self.feedback += 'Received so far: \'%s\'\n</br>' % (self.recvd)

                    #cpu.halt()
                    return
                self.tx_fifo.append(chr_data)
            else:
                # ldwio
                if len(self.rx_fifo) == 0:
                    return (len(self.rx_fifo) << 16) | (0x0<<15) | 0x41

                # Get next chr
                chr_data = self.rx_fifo.popleft()
                return (len(self.rx_fifo) << 16) | (0x1<<15) | chr_data

        def uart_ctrl(self, val=None):
            self.step()
            if val is None:
                # ldwio
                return (64 - len(self.tx_fifo)) << 16

        def result(self, test_no=1):
            while len(self.tx_fifo) > 0:
                self.recvd += chr(self.tx_fifo.popleft())
            if self.recvd == 'Hello, %s' % self.name:
                return (True, 'Test case %d passed\n<br/>' % test_no, self.extra_info)
            else:
                err = cpu.get_error()
                self.feedback += 'Failed test case %d\n<br/>' % test_no
                self.feedback += 'Name: <code>%s</code><br/>' % html.escape(self.name)
                self.feedback += 'Got back <code>%s</code> %s<br/>' % (html.escape(self.recvd), self.recvd.encode('ascii').hex())
                self.feedback += get_debug(cpu)
                self.feedback += 'tx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.tx_fifo), html.escape(''.join([chr(c) for c in self.tx_fifo])))
                self.feedback += 'rx_fifo: %s <code>%s</code>\n<br/>' % \
                        (list(self.rx_fifo), html.escape(''.join([chr(c) for c in self.rx_fifo])))
                return (False, err + self.feedback, self.extra_info)





    tests = [('test', (10,1)),
             ('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789~!@#$%^&*()', (50,1)),
             ('Alan Turing', (10, 10))]
    extra_info = ''
    feedback = ''

    tot_ins = 0
    for i,tc in enumerate(tests):
        u = uart(tc[0], step_roll=tc[1])
        cpu.reset()
        cpu.add_mmio(0xFF201000, u.uart_data)
        cpu.add_mmio(0xFF201004, u.uart_ctrl)

        tot_ins += cpu.run_until_halted(100000)

        res, fb, extra = u.result(i+1)
        feedback += fb
        if extra is not None:
            extra_info += extra
        if not res:
            return (False, feedback, extra_info)

    extra_info += 'Executed %d instructions' % tot_ins
    return (True, feedback, extra_info)




###########
# JTAG UART
Exercises.addExercise('uart-name',
    {
        'public': True,
        'title': 'Write "Hello, &lt;name&gt;" to UART',
        'diff': 'medium',
        'desc': '''Write a program that reads a name from the JTAG UART port until you reach a linebreak (<code>\\n</code> ASCII <code>0x0a</code>) character.
        After the linebreak is received, you should write the message <code>Hello, &lt;name&gt;</code> where <code>&lt;name&gt;</code> is the name read from the UART
        port previously. Your message should include the linebreak read as part of the name.
        ''',
        'code':'''.text
_start:
        ''',
        'checker': check_uart
    })
