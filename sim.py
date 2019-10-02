#!/usr/bin/python3
import numpy as np
import struct

class Nios2(object):
    def __init__(self, init_mem=b''):
        self.regs = [np.uint32(0)]*32
        self.pc = np.uint32(0)
        self.mem = bytearray(init_mem + (64*1024*1024 - len(init_mem))*b'\xaa')

    def loadword(self, addr):
        # Word align
        addr = addr & 0xfffffffc

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
        self.mem[addr:addr+4] = bytearray(struct.pack('<I', val))

    def storehalfword(self, addr, val):
        addr = addr & 0xfffffffe
        self.mem[addr:addr+2] = bytearray(struct.pack('<H', val))

    def storebyte(self, addr, val):
        self.mem[addr] = val


    def get_reg(self, rA):
        return self.regs[rA]

    def set_reg(self, rA, val):
        if rA > 0:
            self.regs[rA] = np.uint32(val)

    # sign extend offset
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
        d[op](rA, rB, offset)

    def rtype(self, opx, rA, rB, rC, imm5=0):
        
        pass


    def call(self, imm26):
        pass
    def jmpi(self, imm26):
        self.pc = (self.pc & np.uint32(0xf0000000)) | np.uint32(imm26 << 2)
    def rdprs(self, imm26):
        pass


    def jtype(self, op, imm26):
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



    def print_regs(self):
        print(' pc 0x%08x' % (self.pc))
        for r in range(32):
            print('% 3s 0x%08x' % ('r%d'%r, self.regs[r]))




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

if __name__ == '__main__':
    prog = bytes.fromhex('00c0014419000084217fffc41980004c41414141000000010000000500000009')
    cpu = Nios2(init_mem=flip_word_endian(prog))
    cpu.one_step()
    cpu.one_step()
    cpu.one_step()
    cpu.one_step()
    cpu.print_regs()
