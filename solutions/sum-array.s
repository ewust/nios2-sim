.text
_start:
	movia	r4, ARR
	movia	r5, N
    movi	r7, 0
    ldw		r5, 0(r5)
loop:
	ble		r5, r0, end
    
    ldw		r6, 0(r4)
    blt		r6, r0, skip
    
    add		r7, r7, r6
    
skip:
    subi	r5, r5, 1
    addi	r4, r4, 4
    
   	br 		loop 
end:
	movia	r5, SUM
    stw		r7, 0(r5)
	break
.data
SUM: .word 0
N:   .word 6
ARR: .word 14, 22, 0, -9, -12, 27

