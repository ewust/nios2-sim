# Copies foo into bar, one word at a time

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
	br	  loop
end:
	break
	br end


.data
foo: .word 3, 8, 10, -1, 0x41424344
bar: .word 0, 0, 0, 0, 0
N:   .word 5
