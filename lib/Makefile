
CC=gcc
INCLUDE=`python3-config --includes`

default=libnios2.a

libnios2.a: nios2.o
	ar rcs $@ $^

nios2.o: nios2.c nios2.h
	$(CC) $(INCLUDE) -fPIC -c $<

clean:
	rm *.o *.a
