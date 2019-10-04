#!/usr/bin/python3
import numpy as np
import struct
import sys

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

        # map of addr => handling function for mmios
        self.mmios = {
                0xFF200000: self.mmio_led,
                0xFF200040: self.mmio_sw,
                }
        self.reset()


    def reset(self):
        self.regs = [np.uint32(0)]*32
        self.pc = np.uint32(self.init_pc)
        self.mem = bytearray(self.init_mem + (64*1024*1024 - len(self.init_mem))*b'\xaa')
        self.ctls_regs = [np.uint32(0)]*32
        self.halted = False

    # 0xFF200000
    def mmio_led(self, value=None):
        if value is None:
            return 0x0
        print('Set LEDs to 0x%08x' % value)

    def new_rw_reg(self, init_val=np.uint32(0)):
        return Nios2.MMIO_Reg(init_val)


    def mmio_sw(self, value=None):
        if value is None:
            return 0x2aa # example switches

    def get_symbol_word(self, symbol, offset=0):
        return self.loadword(self.symbols[symbol] + offset)

    def write_symbol_word(self, symbol, val, offset=0):
        self.storeword(self.symbols[symbol] + offset, val)


    ########################
    # Loads and stores
    ########################
    def loadword(self, addr):
        # Word align
        addr = addr & 0xfffffffc
        if addr > len(self.mem):
            # check mmio
            if addr in self.mmios:
                return np.uint32(self.mmios[addr]())

        word, = struct.unpack('<I', self.mem[addr:addr+4])
        return np.uint32(word)

    def loadhalfword(self, addr):
        addr = addr & 0xfffffffe
        hw, = struct.unpack('<H', self.mem[addr:addr+2])
        return np.uint16(hw)

    def loadbyte(self, addr):
        by, = struct.unpack('<B', self.mem[addr:addr+1])
        return np.uint8(by)

    def storeword(self, addr, val):
        # Word align
        addr = addr & 0xfffffffc
        if addr > len(self.mem):
            if addr in self.mmios:
                self.mmios[addr](val)
                return
        self.mem[addr:addr+4] = bytearray(struct.pack('<I', val))

    def storehalfword(self, addr, val):
        addr = addr & 0xfffffffe
        self.mem[addr:addr+2] = bytearray(struct.pack('<H', val))

    def storebyte(self, addr, val):
        self.mem[addr] = val


    ########################
    # General purpose registers
    ########################
    def get_reg(self, rA):
        return self.regs[rA]

    def set_reg(self, rA, val):
        if rA > 0:
            self.regs[rA] = np.uint32(val)


    ########################
    # TODO: control registers require special handling
    ########################
    def get_ctl_reg(self, n):
        return self.ctl_regs[n]

    def set_ctl_reg(self, n, val):
        self.ctl_regs[n] = val

    ########################
    # I-type instructions
    ########################
    def addi(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) + np.int16(offset))

    def andi(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) & offset)

    def andhi(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rB) & np.uint32(offset << 16))

    def inc_pc16(self, offset):
        self.pc = np.uint32(self.pc + np.int16(offset))

    def beq(self, rA, rB, offset):
        if self.get_reg(rA) == self.get_reg(rB):
            self.inc_pc16(offset)

    def bge(self, rA, rB, offset):
        if np.int32(self.get_reg(rA)) >= np.int32(self.get_reg(rB)):
            self.inc_pc16(offset)

    def bgeu(self, rA, rB, offset):
        if np.uint32(self.get_reg(rA)) >= np.uint32(self.get_reg(rB)):
            self.inc_pc16(offset)

    def blt(self, rA, rB, offset):
        if np.int32(self.get_reg(rA)) < np.int32(self.get_reg(rB)):
            self.inc_pc16(offset)

    def bltu(self, rA, rB, offset):
        if np.uint32(self.get_reg(rA)) < np.uint32(self.get_reg(rB)):
            self.inc_pc16(offset)

    def bne(self, rA, rB, offset):
        if self.get_reg(rA) != self.get_reg(rB):
            self.inc_pc16(offset)

    def br(self, rA, rB, offset):
        self.inc_pc16(offset)

    def cmpeqi(self, rA, rB, offset):
        if self.get_reg(rA) == np.uint32(np.int16(offset)):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def cmpgei(self, rA, rB, offset):
        if np.int32(self.get_reg(rA)) >= np.int32(np.int16(offset)):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def cmpgeui(self, rA, rB, offset):
        if self.get_reg(rA) >= np.uint32(offset):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def cmplti(self, rA, rB, offset):
        if np.int32(self.get_reg(rA)) < np.int32(np.int16(offset)):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def cmpltui(self, rA, rB, offset):
        if self.get_reg(rA) < np.uint32(offset):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def cmpnei(self, rA, rB, offset):
        if self.get_reg(rA) != np.uint32(np.int16(offset)):
            self.set_reg(rB, 1)
        else:
            self.set_reg(rB, 0)

    def flushd(self, rA, rB, offset):
        # No cache, okay.
        pass
    def flushda(self, rA, rB, offset):
        pass
    def initd(self, rA, rB, offset):
        pass
    def initda(self, rA, rB, offset):
        pass

    def ldb(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.set_reg(rB, np.int8(self.loadbyte(ea)))

    def ldbu(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.set_reg(rB, np.uint8(self.loadbyte(ea)))

    def ldh(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.set_reg(rB, np.int16(self.loadhalfword(ea)))

    def ldhu(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.set_reg(rB, np.uint16(self.loadbyte(ea)))

    def ldw(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.set_reg(rB, self.loadword(ea))

    def muli(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) * np.int32(np.int16(offset)))

    def orhi(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) | (np.uint32(offset)<<16))
    def ori(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) | np.uint32(offset))

    def stb(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.storebyte(ea, self.get_reg(rB) & 0xff)

    def sth(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.storehalfword(ea, self.get_reg(rB) & 0xffff)

    def stw(self, rA, rB, offset):
        ea = self.get_reg(rA) + np.int16(offset)
        self.storeword(ea, self.get_reg(rB))

    def xorhi(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) ^ np.uint32(np.uint32(offset) << 16))

    def xori(self, rA, rB, offset):
        self.set_reg(rB, self.get_reg(rA) ^ np.uint32(offset))

    def itype(self, op, rA, rB, offset):
        d = {0x03: self.ldbu,
             0x04: self.addi,
             0x05: self.stb,
             0x06: self.br,
             0x07: self.ldb,
             0x08: self.cmpgei,
             0x0b: self.ldhu,
             0x0c: self.andi,
             0x0d: self.sth,
             0x0e: self.bge,
             0x0f: self.ldh,
             0x10: self.cmplti,
             0x13: self.initda,
             0x14: self.ori,
             0x15: self.stw,
             0x16: self.blt,
             0x17: self.ldw,
             0x18: self.cmpnei,
             0x1b: self.flushda,
             0x1c: self.xori,
             0x1e: self.bne,
             0x20: self.cmpeqi,
             0x23: self.ldbu,   # ldbuio
             0x24: self.muli,
             0x25: self.stb,    # stbio
             0x26: self.beq,
             0x27: self.ldb,    # ldbio
             0x28: self.cmpgeui,
             0x2b: self.ldhu,   # ldhuio
             0x2c: self.andhi,
             0x2d: self.sth,    # sthio
             0x2e: self.bgeu,
             0x2f: self.ldh,    # ldhio
             0x30: self.cmpltui,
             0x33: self.initd,
             0x34: self.orhi,
             0x35: self.stw,    # stwio
             0x36: self.bltu,
             0x37: self.ldw,    # ldwio
             0x3b: self.flushd,
             0x3c: self.xorhi,
            }
        if op not in d:
            self.halted = True
            self.error = 'Invalid instruction opcode: 0x%08x' % (self.loadword(self.pc))
            return
        d[op](rA, rB, offset)


    ###############################
    # R-type
    ##############################
    def add(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) + self.get_reg(rB))

    def _and(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) & self.get_reg(rB))

    def _break(self, rA, rB, rC, imm5):
        # Debug breakpoint...
        # bstatus = status
        # PIE = 0, U = 0
        # ba = PC (+4, but already happened)
        # PC = break handler addr
        self.halted = True
        pass

    def _bret(self, rA, rB, rC, imm5):
        # PC = ba
        # status = bstatus
        pass

    def callr(self, rA, rB, rC, imm5):
        # ra = PC (+4)
        # PC = rA
        self.set_reg(31, self.pc)
        self.pc = self.get_reg(rA)

    def cmpeq(self, rA, rB, rC, imm5):
        if self.get_reg(rA) == self.get_reg(rB):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def cmpge(self, rA, rB, rC, imm5):
        if np.int32(self.get_reg(rA)) >= np.int32(self.get_reg(rB)):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def cmpgeu(self, rA, rB, rC, imm5):
        if np.uint32(self.get_reg(rA)) >= np.uint32(self.get_reg(rB)):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def cmplt(self, rA, rB, rC, imm5):
        if np.int32(self.get_reg(rA)) < np.int32(self.get_reg(rB)):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def cmpltu(self, rA, rB, rC, imm5):
        if np.uint32(self.get_reg(rA)) < np.uint32(self.get_reg(rB)):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def cmpne(self, rA, rB, rC, imm5):
        if self.get_reg(rA) != self.get_reg(rB):
            self.set_reg(rC, 1)
        else:
            self.set_reg(rC, 0)

    def div(self, rA, rB, rC, imm5):
        if self.get_reg(rB) != 0:
            self.set_reg(rC, np.int32(np.int32(self.get_reg(rA)) / np.int32(self.get_reg(rB))))

    def divu(self, rA, rB, rC, imm5):
        if self.get_reg(rB) != 0:
            self.set_reg(rC, np.uint32(np.uint32(self.get_reg(rA)) / np.uint32(self.get_reg(rB))))

    def eret(self, rA, rB, rC, imm5):
        # status = estatus
        # PC = ea
        pass

    def flushi(self, rA, rB, rC, imm5):
        pass
    def flushp(self, rA, rB, rC, imm5):
        pass
    def initi(self, rA, rB, rC, imm5):
        pass

    def jmp(self, rA, rB, rC, imm5):
        self.pc = self.get_reg(rA)

    def mul(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) * self.get_reg(rB))

    def mulxss(self, rA, rB, rC, imm5):
        res = np.int64(self.get_reg(rA)) * np.int64(self.get_reg(rB))
        self.set_reg(rC, np.uint32(res >> 32))

    def mulxsu(self, rA, rB, rC, imm5):
        res = np.int64(self.get_reg(rA)) * np.uint64(self.get_reg(rB))
        self.set_reg(rC, np.uint32(res >> 32))

    def mulxuu(self, rA, rB, rC, imm5):
        res = np.uint64(self.get_reg(rA)) * np.uint64(self.get_reg(rB))
        self.set_reg(rC, np.uint32(res >> 32))

    def nextpc(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.pc)

    def nor(self, rA, rB, rC, imm5):
        self.set_reg(rC, ~(self.get_reg(rA) | self.get_reg(rB)))

    def _or(self, rA, rB, rC, imm5):
        self.set_reg(rC, (self.get_reg(rA) | self.get_reg(rB)))

    def rdctl(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_ctl_reg(imm5))


    def ret(self, rA, rB, rC, imm5):
        self.pc = self.get_reg(31)

    def rotate32(self, n, m):
        r = np.uint64(n) << (m & 0x1f)
        return np.uint32(r) | np.uint32(r >> 32)

    def rotate_r32(self, n, m):
        # Put 32 bits of 0s to the right of our number (as a 64-bit number):
        r = n << 32
        # then shift it m bits to the right.
        r >>= (m & 0x1f)
        # things in 63..32 are our "right most" bits, and things in 31..0 are the upper bits
        return np.uint32(r>>32) | np.uint32(r)

    def rol(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.rotate32(self.get_reg(rA), (self.get_reg(rB) & 0x1f)))

    def roli(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.rotate32(self.get_reg(rA), imm5))

    def ror(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.rotate_r32(self.get_reg(rA), (self.get_reg(rB) & 0x1f)))

    #def rori(self, rA, rB, rC, imm5):
    #    self.set_reg(rC, self.rotate_r32(self.get_reg(rA), imm5))

    def sll(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) << (self.get_reg(rB) & 0x1f))

    def slli(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) << imm5)

    def sra(self, rA, rB, rC, imm5):
        self.set_reg(rC, np.int32(self.get_reg(rA)) >> (self.get_reg(rB) & 0x1f))

    def srai(self, rA, rB, rC, imm5):
        self.set_reg(rC, np.int32(self.get_reg(rA)) >> imm5)


    def srl(self, rA, rB, rC, imm5):
        self.set_reg(rC, np.uint32(self.get_reg(rA)) >> (self.get_reg(rB) & 0x1f))

    def srli(self, rA, rB, rC, imm5):
        self.set_reg(rC, np.uint32(self.get_reg(rA)) >> imm5)

    def sub(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) - self.get_reg(rB))

    def sync(self, rA, rB, rC, imm5):
        pass

    def trap(self, rA, rB, rC, imm5):
        #estatus = status
        # PIE = 0
        # U = 0
        # ea = PC (+4)
        # PC = exception handler
        pass
    def wrctl(self, rA, rB, rC, imm5):
        self.set_ctl_reg(imm5, self.get_reg(rA))

    def wrprs(self, rA, rB, rC, imm5):
        pass

    def xor(self, rA, rB, rC, imm5):
        self.set_reg(rC, self.get_reg(rA) ^ self.get_reg(rB))


    def rtype(self, opx, rA, rB, rC, imm5=0):
        d = {0x01: self.eret,
             0x02: self.roli,
             0x03: self.rol,
             0x04: self.flushp,
             0x05: self.ret,
             0x06: self.nor,
             0x07: self.mulxuu,
             0x08: self.cmpge,
             0x09: self._bret,
             0x0b: self.ror,
             0x0c: self.flushi,
             0x0d: self.jmp,
             0x0e: self._and,
             0x10: self.cmplt,
             0x12: self.slli,
             0x13: self.sll,
             0x14: self.wrprs,
             0x16: self._or,
             0x17: self.mulxsu,
             0x18: self.cmpne,
             0x1a: self.srli,
             0x1b: self.srl,
             0x1c: self.nextpc,
             0x1d: self.callr,
             0x1e: self.xor,
             0x1f: self.mulxss,
             0x20: self.cmpeq,
             0x24: self.divu,
             0x25: self.div,
             0x27: self.mul,
             0x28: self.cmpgeu,
             0x29: self.initi,
             0x2d: self.trap,
             0x2e: self.wrctl,
             0x30: self.cmpltu,
             0x31: self.add,
             0x34: self._break,
             0x36: self.sync,
             0x39: self.sub,
             0x3a: self.srai,
             0x3b: self.sra,
             }
        d[opx](rA, rB, rC, imm5)

    ###############################
    # J-type
    ###############################
    def call(self, imm26):
        self.set_reg(31, self.pc) # Set ra = PC (+4)
        self.pc = (self.pc & np.uint32(0xf0000000)) | np.uint32(imm26 << 2)

    def jmpi(self, imm26):
        self.pc = (self.pc & np.uint32(0xf0000000)) | np.uint32(imm26 << 2)

    def rdprs(self, imm26):
        pass


    def one_step(self):
        instr = self.loadword(self.pc)
        jtypes = {0x00: self.call,
                  0x01: self.jmpi,
                  0x38: self.rdprs}

        self.pc += np.uint32(4)
        # decode
        op = instr & 0x3f
        if op == 0x3a:
            # R-type:
            rA = instr >> 27
            rB = (instr >> 22) & 0x1f
            rC = (instr >> 17) & 0x1f
            opx = (instr >> 11) & 0x3f
            imm5 = (instr >> 6) & 0x1f
            self.rtype(opx, rA, rB, rC, imm5)
        else:
            if op in jtypes:
                # J-type:
                imm26 = (instr >> 6) & 0x3ffffff
                jtypes[op](imm26)
            else:
                # I-type:
                rA = instr >> 27
                rB = (instr >> 22) & 0x1f
                imm16 = np.uint16((instr >> 6) & 0xffff)
                self.itype(op, rA, rB, imm16)


    def run_until_halted(self, instr_limit=None):
        instr = 0
        while not(self.halted) and (instr_limit is None or instr < instr_limit):
            self.one_step()
            instr += 1
        return instr


    def get_regs(self, n_regs=32):
        out = ' pc 0x%08x\n' % (self.pc)
        for r in range(n_regs):
            out += '% 3s 0x%08x\n' % ('r%d'%r, self.regs[r])
        return out

    def print_regs(self, n_regs=32):
        print(self.get_regs(n_regs))

    # returns a string hexdump of memory starting at addr_min
    # to addr_min+byte_len
    # displays in words or bytes depedning on if words=True or False (TODO)
    def dump_mem(self, addr_min, byte_len, words=True):
        s = addr_min & 0xfffffffc
        out = ''
        for addr in range(s, s+byte_len, 4):

            # Print address at beginning of row
            if (addr & 0xf) == 0:
                out += '\n0x%08x: ' % addr

            word, = struct.unpack('<I', self.mem[addr:addr+4])
            out += '%08x  ' % word
        out += '\n'
        return out

    def dump_symbols(self):
        out = ''
        max_sym_len = max([len(s) for s,v in self.symbols.items()])
        fmt = '%% %ds: 0x%%08x\n' % max_sym_len
        for s,v in sorted(self.symbols.items(), key=lambda x: x[1]):
            out += fmt % (s, v)
        return out


def flip_word_endian(s):
    out = b''
    for i in range(len(s)>>2):
        word, = struct.unpack('>I', s[4*i:4*i+4])
        out += struct.pack('<I', word)
    return out


'''
.text
.global _start
_start:
    addi  r3, r0, 5
    addi  r4, r3, 2
    addi  r5, r4, -1
    andi  r6, r3, 0x1


    .data
    bar: .word 0x41414141
    foo: .word 1, 5, 9
'''
#prog = bytes.fromhex('00c0014419000084217fffc41980004c41414141000000010000000500000009')

'''
.text
.global _start
_start:
	movia r4, foo
    movia r5, bar
    movia r6, N
    ldw	  r6, 0(r6)
    
loop:
	ble   r6, r0, end
    
    ldw	  r7, 0(r4)
    stw	  r7, 0(r5)
    
    addi  r4, r4, 4
    addi  r5, r5, 4
    
    subi  r6, r6, 1
	br 	  loop
end:
	break
	br end


.data
foo: .word 3, 8, 10, -1, 0x41424344
bar: .word 0, 0, 0, 0, 0
N:   .word 5'''
# prog = bytes.fromhex('010000342100100401400034294015040180003431801a04318000170180060e21c0001729c00015210001042940010431bfffc4003ff906003da03a003ffe0600000003000000080000000affffffff41424344000000000000000000000000000000000000000000000005')

if __name__ == '__main__':
    test_prog = '010000342100100401400034294015040180003431801a04318000170180060e21c0001729c00015210001042940010431bfffc4003ff906003da03a003ffe0600000003000000080000000affffffff41424344000000000000000000000000000000000000000000000005'
    start_pc = 0
    if len(sys.argv) > 1:
        test_prog = sys.argv[1]
    if len(sys.argv) > 2:
        start_pc = int(sys.argv[2], 16)

    prog = bytes.fromhex(test_prog)
    cpu = Nios2(init_mem=flip_word_endian(prog), start_pc=start_pc)
    print(cpu.dump_mem(0x00, 0x100))

    inst = 0
    while not(cpu.halted):
        #print('===============')
        #print('  Instruction %d' % inst)
        #cpu.print_regs(9)
        cpu.one_step()
        inst += 1
    print('===========')
    print('%d instructions' % inst)
    cpu.print_regs()
    print(cpu.dump_mem(0x00, 0x100))
