
#define PY_SSIZE_T_CLEAN
#include "Python.h"

#define MAX_MMIOS       16
#define MAX_CLOBBERED   100

struct mmio {
    uint32_t    addr;
    PyObject    *callback;
    void        *arg;
};

struct callee_saved {
    uint32_t            pc;
    uint32_t            regs[32];
    struct callee_saved *prev;
};

struct clobbered {
    uint32_t    pc;
    int         reg_id;
    int         interrupt;
};

struct nios2 {
    int                 halted;
    char                *error;

    uint32_t            pc;
    uint32_t            regs[32];
    uint32_t            ctl[32];    // control registers (Some overriden)

    struct callee_saved *callee_stack_head;

    int                 clobbered_idx;
    struct clobbered    clobbered_history[MAX_CLOBBERED];

    unsigned char       *mem;
    size_t              mem_len;
    struct mmio         mmios[MAX_MMIOS];
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
void     _interrupt_cpu(long obj);
void     _one_step(long obj);
int      _run_until_halted(long obj, int instr_limit);
void     _set_pc(long obj, uint32_t val);
uint32_t _get_pc(long obj);
uint32_t _get_ctl_reg(long cpu, long reg);
void     _set_ctl_reg(long cpu, long reg, uint32_t val);

PyObject *_get_clobbered(long obj);

