.text
_start:

	movia	r4, ARR
    movia	r5, N
    
    
    ldw 	r5, 0(r5)		# r5 = N 
    ldw		r6, 0(r4)		# r6 = ARR[0]
    
loop:
	ble		r5, r0, end		# if r5 <= 0 goto end
    
    ldw		r7, 0(r4)		# r7 = *r4

	bgt		r7, r6, not_lt
    mov		r6, r7			# new minimum
not_lt:
 	addi	r4, r4, 4		# r6+=4   
    subi	r5, r5, 1		# r5--
    br 		loop
end:
	movia	r4, MIN
    stw		r6, 0(r4)
    break

.data
MIN: .word 0
N:   .word 5
ARR: .word 5, -8, -1, 12, 6

