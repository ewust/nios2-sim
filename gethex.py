#!/usr/bin/python3

import fileinput
import binascii
import re
import sys
import json

out = b''
cur_addr = 0
symbols = {}

for line in sys.stdin:
    m = re.match(r'\s+([0-9a-f]+):\s+([0-9a-f]{8})', line)
    if m is None:
        # search for <_start>
        m = re.match(r'([0-9a-f]+)\s+<(.*)>:', line)
        if m:
            addr = int(m.group(1),16)
            symbol = m.group(2)
            symbols[symbol] = addr
        continue

    addr = int(m.group(1), 16)
    val = m.group(2)

    while cur_addr < addr:
        out += b'\x00'
        cur_addr += 1

    out += bytes.fromhex(val) # val.encode(encoding='ascii')
    cur_addr += 4

prog = binascii.hexlify(bytearray(out)).decode('ascii')

if len(sys.argv) > 1 and sys.argv[1] == '-json':
    # show all symbols, return a json obj

    obj = {'prog': prog, 'symbols': symbols} 
    print(json.dumps(obj))

else:
    print(prog,end='')
    print('  %s' % symbols['_start'])

