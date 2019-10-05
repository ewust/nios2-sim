from libc.stdint cimport uint32_t, int32_t, uint8_t


cdef extern from "nios2.h":
    unsigned int _new_nios2(const char *mem, size_t mem_len)
    void _del_nios2(long cpu)
    void _print_mem(long cpu)
    uint32_t _loadword(long cpu, uint32_t addr);
    void     _storeword(long cpu, uint32_t addr, uint32_t val);
    void     _add_mmio(long cpu, uint32_t addr, object callback);
    void     _one_step(long cpu);
    void     one_instr(void *cpu);
    long     _run_until_halted(long cpu, int limit);
    void     _set_pc(long cpu, uint32_t val);
    uint32_t _get_pc(long cpu);
    uint32_t _get_reg(long cpu, long reg);
    void     _set_reg(long cpu, long reg, uint32_t val);



def py_new_nios2(mem: bytes):
    return _new_nios2(mem, len(mem))

def py_del_nios2(cpu: long):
    return _del_nios2(cpu)

def py_print_mem(cpu: long) -> None:
    _print_mem(cpu)


def py_loadword(cpu: long, addr: long) -> long:
    return _loadword(cpu, addr)

def py_storeword(cpu: long, addr: long, val: long):
    return _storeword(cpu, addr, val)


def py_add_mmio(cpu: long, addr: long, cb: object):
    _add_mmio(cpu, addr, cb)

def py_one_step(cpu: long) -> None:
    _one_step(cpu)

def py_run_until_halted(cpu: long, limit: long):
    return _run_until_halted(cpu, limit)


def py_set_pc(cpu: long, val: long):
    _set_pc(cpu, val)
def py_get_pc(cpu: long):
    return _get_pc(cpu)

def py_set_reg(cpu: long, reg: long, val: long):
    _set_reg(cpu, reg, val)
def py_get_reg(cpu: long, reg: long):
    return _get_reg(cpu, reg)
