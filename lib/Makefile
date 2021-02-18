
CC=gcc
INCLUDE=`python3-config --includes`

default=libnios2.a

install: libnios2.a
	cp ./libnios2.a /usr/local/lib

libnios2.a: nios2.o
	ar rcs $@ $^

nios2.o: nios2.c nios2.h
	$(CC) $(INCLUDE) -fPIC -c $<

clean:
	rm *.o *.a
