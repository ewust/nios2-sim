#!/bin/bash


bin/nios2-elf-objdump -D $1 | ./gethex.py -json
#egrep '\s[0-9a-f]{8}' | ./gethex.py

