
import tempfile
import subprocess
import json
from collections import defaultdict
import struct

def nios2_as(asm):
    asm_f = tempfile.NamedTemporaryFile()
    asm_f.write(asm)
    asm_f.flush()

    obj_f = tempfile.NamedTemporaryFile()

    ########## Assemble
    p = subprocess.Popen(['bin/nios2-elf-as', \
                          asm_f.name, \
                          '-o', obj_f.name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() != 0:
        ret = 'Assembler error: %s' % p.stderr.read()
        try:
            obj_f.close()
            asm_f.close()
            p.stdout.close()
            p.stderr.close()
        except:
            pass
        return ret

    asm_f.close()
    p.stdout.close()
    p.stderr.close()


    ######### Link
    exe_f = tempfile.NamedTemporaryFile()
    p = subprocess.Popen(['bin/nios2-elf-ld', \
                          '-T', 'de10.ld', \
                          obj_f.name, '-o', exe_f.name],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE) 
    if p.wait() != 0:
        ret = 'Linker error: %s' % p.stderr.read()
        p.stderr.close()
        p.stdout.close()
        obj_f.close()
        return ret

    obj_f.close()
    p.stdout.close()
    p.stderr.close()

    ######## objdump
    p = subprocess.Popen(['./gethex.sh', exe_f.name], \
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.wait() != 0:
        ret = 'Objdump error: %s' % p.stderr.read()
        p.stderr.close()
        p.stdout.close()
        exe_f.close()
        return ret

    obj = json.loads(p.stdout.read().decode('ascii'))
    p.stdout.close()
    p.stderr.close()
    exe_f.close()

    return obj

def get_clobbered(cpu):
    feedback = ''
    for addr,rid,interrupt in cpu.get_clobbered():
        s = 'function'
        if interrupt:
            s = 'interrupt'
        feedback += 'Error: %s @0x%08x clobbered r%d<br/>\n' % (s, addr, rid)
    return feedback

def get_debug(cpu, mem_len=0x100, show_stack=False):
    out = '<br/>\n'
    out += cpu.get_error()
    out += '<br/>Memory:<br/><pre>'
    out += cpu.dump_mem(0, mem_len)
    out += '\nSymbols:\n' + cpu.dump_symbols()
    out += '</pre>'
    if show_stack:
        sp = cpu.get_reg(27)
        fp = cpu.get_reg(28)
        out += '<br/>Stack:<br/><pre>'
        out += 'sp = 0x%08x\nfp = 0x%08x\n\n' % (sp, fp)
        diff = 0x04000000 - (sp-0x80)
        out += cpu.dump_mem(sp-0x80, min(0x100, diff))
        out += '\n</pre>'
    return out

def hotpatch(obj, new_start_asm):
    hp = '.text\n'
    # fill symbols
    rev_map = defaultdict(list) # addr => [list_of_symbols]
    # TODO: this will only work for word-aligned labels...
    for s,addr in obj['symbols'].items():
        #hp += '.equ %s, 0x%08x\n' % (s, addr)
        if s != '_start':
            rev_map[addr].append(s)

    # fill bytes
    p = bytes.fromhex(obj['prog'])
    for i in range(len(p)>>2):
        addr = 4*i
        word, = struct.unpack('>I', p[4*i:4*i+4])
        for sym in rev_map[addr]:
            hp += '%s:\n' % sym
        hp += ' .word 0x%08x\n' % (word)
    hp += new_start_asm
    return nios2_as(hp.encode('utf-8'))

def require_symbols(obj, symbols):
    if not(isinstance(obj, dict)):
        return str(obj)
    #if '_start' not in obj['symbols']:
    for s in symbols:
        if s not in obj['symbols']:
            return '%s not found in memory (did you enter any instructions?)' % (s)
    return None

