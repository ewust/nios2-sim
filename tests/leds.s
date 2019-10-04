_start:
	movia	r4, 0xff200000
    movi	r5, 0xaaa
    stw		r5, 0(r4)
	break
