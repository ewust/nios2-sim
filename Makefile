LIB_DIR=lib

default: pynios2

pynios2: setup.py nios2.pyx $(LIB_DIR)/nios2.c $(LIB_DIR)/libnios2.a
	python3 setup.py build_ext --inplace


$(LIB_DIR)/libnios2.a:
		make -C $(LIB_DIR) libnios2.a

clean:
	rm -rf build && rm nios2.c
