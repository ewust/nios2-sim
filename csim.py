
import pynios2
import numpy as np
import struct
from sim import flip_word_endian


class Nios2(object):

    class MMIO_Reg(object):
        def __init__(self, init_val=np.uint32(0)):
            self.val = init_val
        def store(self, val):
            self.val = val
        def load(self):
            return self.val
        def access(self, val=None):
            if val is None:
                return self.load()
            self.store(val)


    def __init__(self, init_mem=b'', start_pc=0, obj=None):
        if obj is not None:
            self.obj = obj
            self.symbols = obj['symbols']
            init_mem = flip_word_endian(bytes.fromhex(obj['prog']))
            start_pc = obj['symbols']['_start']

        self.init_mem = init_mem
        self.init_pc = start_pc

        self.c_obj = 0
        self.reset()

    def __del__(self):
        pynios2.py_del_nios2(self.c_obj)

    def reset(self):
        if (self.c_obj != 0):
            pynios2.py_del_nios2(self.c_obj)
        self.c_obj = pynios2.py_new_nios2(self.init_mem)
        self.set_pc(self.init_pc)

    def halt(self):
        pynios2.py_halt_cpu(self.c_obj)

    def get_clobbered(self):
        return pynios2.py_get_clobbered(self.c_obj)


    def get_reg(self, reg):
        return pynios2.py_get_reg(self.c_obj, reg)
    def set_reg(self, reg, val):
        pynios2.py_set_reg(self.c_obj, reg, val)

    def get_pc(self):
        return pynios2.py_get_pc(self.c_obj)
    def set_pc(self, val):
        pynios2.py_set_pc(self.c_obj, val)

    def print_regs(self, n_regs=32):
        print(' pc = 0x%08x' % self.get_pc())
        for i in range(n_regs):
            print('% 3s = 0x%08x' % ('r%d'%i, self.get_reg(i)))



    # TODO: do this with loadwords...
    def print_mem(self):
        pynios2.py_print_mem(self.c_obj)

    def dump_mem(self, min_addr, num_bytes):
        s = min_addr & 0xfffffffc
        out = ''
        for addr in range(s, s+num_bytes, 4):
            if (addr & 0xf) == 0:
                out += '\n0x%08x: ' % addr
            out += '%08x  ' % self.loadword(addr)
        out += '\n'
        return out

    def dump_symbols(self):
        out = ''
        max_sym_len = max([len(s) for s,v in self.symbols.items()])
        fmt = '%% %ds: 0x%%08x\n' % max_sym_len
        for s,v in sorted(self.symbols.items(), key=lambda x: x[1]):
            out += fmt % (s, v)
        return out



    def loadword(self, addr):
        return pynios2.py_loadword(self.c_obj, np.uint32(addr))

    def storeword(self, addr, val):
        pynios2.py_storeword(self.c_obj, np.uint32(addr), np.uint32(val))

    def get_symbol_word(self, symbol, offset=0):
        return self.loadword(self.symbols[symbol] + offset)

    def write_symbol_word(self, symbol, val, offset=0):
        self.storeword(self.symbols[symbol] + offset, val)

    def add_mmio(self, addr, cb):
        pynios2.py_add_mmio(self.c_obj, np.uint32(addr), cb)

    def one_step(self):
        pynios2.py_one_step(self.c_obj)

    def run_until_halted(self, limit=-1):
        return pynios2.py_run_until_halted(self.c_obj, limit)

    def get_error(self):
        return pynios2.py_get_error(self.c_obj)



def my_cb(arg=None):
    print('Python callback test: %s' % arg)
    return 0x01020304

def scope():
    cpu = Nios2(init_mem=b'foobar', start_pc=0)
    cpu.print_mem()
    print('Word @0: 0x%08x' % cpu.loadword(0))
    cpu.storeword(0, 0x01020304)
    print('Wrote word...')
    cpu.print_mem()

    cpu.add_mmio(0xFF200000, my_cb)

    cpu.loadword(0xFF200000)
    cpu.storeword(0xFF200000, 1515)

    print('okokoko')
    cpu.storeword(0, 0x210003c4)
    cpu.storeword(4, 0x003ffe06)
    cpu.print_mem()
    cpu.run_until_halted(10000000)

    print('')



if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        import json

        test_prog = sys.argv[1]
        obj = json.loads(test_prog)
        cpu = Nios2(obj=obj)
        print(cpu.dump_mem(0x00, 0x100))
        n = cpu.run_until_halted(10000)
        print('Ran %d instructions' % n)
        cpu.print_regs()
        print(cpu.dump_mem(0x00, 0x100))

    else:
        scope()

