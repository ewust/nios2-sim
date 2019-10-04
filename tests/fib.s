.text
.global _start
_start:

	movi	r4, 5
	movia	sp, 0x4000000
	subi	sp, sp, 8

	stw		ra, 4(sp)


	call	fib

	# r2 should be fib(5)
	break

fib:
	subi	sp, sp, 12
	stw		ra, 8(sp)
	stw		r4, 4(sp)

	# if fib(0) or fib(1) return 1
	cmpltui r2, r4, 2
	bne		r2, r0, base_case

	subi	r4, r4, 1
	call	fib				# fib(n-1)
	stw		r2,	0(sp)

	ldw		r4, 4(sp)		# restore n
	subi	r4, r4, 2
	call	fib				# fib(n-2)
	ldw		r3, 0(sp)		# restore fib(n-1)
	add		r2, r2, r3		# fib(n-1) + fib(n-2)
	br		fib_exit
base_case:
	movi	r2, r4

fib_exit:
	ldw		ra, 8(sp)
	addi	sp, sp, 12
	ret
