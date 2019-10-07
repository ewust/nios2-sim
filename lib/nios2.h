
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#define MAX_MMIOS   16

struct mmio {
    uint32_t    addr;
    PyObject    *callback;
    void        *arg;
};

struct nios2 {
    int             halted;
    char            *error;

    uint32_t        pc;
    uint32_t        regs[32];

    unsigned char   *mem;
    size_t          mem_len;
    struct mmio     mmios[MAX_MMIOS];
};

// Create/Delete
long _new_nios2(const char *mem, size_t mem_len);
void _del_nios2(long cpu);

// Deprecated
void _print_mem(long cpu);
void _print_regs(long cpu);

// Memory
uint32_t _loadword(long cpu, uint32_t addr);
void     _storeword(long cpu, uint32_t addr, uint32_t val);
uint32_t _get_reg(long cpu, long reg);
void     _set_reg(long cpu, long reg, uint32_t val);
PyObject *_get_error(long cpu);


// MMIO
void _add_mmio(long cpu, uint32_t addr, PyObject *callback);


// Control
void     one_instr(struct nios2 *cpu);
void     _halt_cpu(long cpu);
void     _one_step(long obj);
int      _run_until_halted(long obj, int instr_limit);
void     _set_pc(long obj, uint32_t val);
uint32_t _get_pc(long obj);

