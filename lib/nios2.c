#include <stdio.h>
#include <stdlib.h>
#include "nios2.h"
#include <stdint.h>
#include <string.h>

#define NIOS_RAM_SIZE (64*1024*1024)

long _new_nios2(const char *mem, size_t mem_len)
{
    struct nios2 *cpu = malloc(sizeof(struct nios2));
    if (cpu == NULL) {
        return 0;
    }
    cpu->halted = 0;
    cpu->error = NULL;


    // Init memory
    cpu->mem = malloc(NIOS_RAM_SIZE);
    if (cpu->mem == NULL) {
        return 0;
    }
    memset(cpu->mem, 0xaa, NIOS_RAM_SIZE);
    cpu->mem_len = NIOS_RAM_SIZE;
    memcpy(cpu->mem, mem, mem_len);


    // Init registers
    cpu->pc = 0;
    memset(cpu->regs, 0, sizeof(uint32_t)*32);

    memset(cpu->ctl, 0, sizeof(uint32_t)*32);


    // Init internal tracking
    memset(cpu->clobbered_history, 0, sizeof(struct clobbered)*MAX_CLOBBERED);
    cpu->clobbered_idx = 0;
    cpu->callee_stack_head = NULL;


    // setup mmio
    int i;
    for (i=0; i<MAX_MMIOS; i++) {
        cpu->mmios[i].addr = 0;
        cpu->mmios[i].callback = NULL;
        cpu->mmios[i].arg = NULL;
    }

    return (long )cpu;
}


PyObject *_get_error(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    PyObject *ret = Py_BuildValue("s", cpu->error);
    return ret;
}

uint32_t _get_pc(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    return cpu->pc;
}
void _set_pc(long obj, uint32_t pc)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    cpu->pc = pc;
}

uint32_t get_reg(struct nios2 *cpu, int reg)
{
    return cpu->regs[reg & 0x1f];
}

void set_reg(struct nios2 *cpu, int reg, uint32_t val)
{
    reg &= 0x1f;
    if (reg != 0) {
        cpu->regs[reg] = val;
    }
}

uint32_t get_ctl_reg(struct nios2 *cpu, int reg)
{
    return cpu->ctl[reg & 0x1f];
}

void set_ctl_reg(struct nios2 *cpu, int reg, uint32_t val)
{
    cpu->ctl[reg & 0x1f] = val;
}

uint32_t _get_ctl_reg(long obj, long reg)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    return get_ctl_reg(cpu, reg);
}

void _set_ctl_reg(long obj, long reg, uint32_t val)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    set_ctl_reg(cpu, reg, val);
}

void _del_nios2(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;

    if (cpu == NULL) {
        return;
    }

    if (cpu->mem != NULL) {
        free(cpu->mem);
    }

    free(cpu);
}

uint32_t _get_reg(long obj, long reg)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    return get_reg(cpu, reg);
}

void _set_reg(long obj, long reg, uint32_t val)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    set_reg(cpu, reg, val);
}

void _print_regs(long obj)
{
    struct nios2 *cpu = (struct nios2*)obj;
    printf(" pc = 0x%08x\n", cpu->pc);
    int i;
    for (i=0; i<32; i++) {
        if (i < 10) {
            printf(" r%d = 0x%08x\n", i, get_reg(cpu, i));
        } else {
            printf("r%d = 0x%08x\n", i, get_reg(cpu, i));
        }
    }
}

// Don't use, just call loadword a bunch
void _print_mem(long obj)
{
    struct nios2 *cpu = (struct nios2*)obj;
    int i;
    uint32_t *p = (uint32_t*)cpu->mem;
    for (i=0; i<0x100; i+=4) {
        if ((i % 16)==0) {
            printf("\n0x%08x:", i);
        }
        printf("  %08x", p[i/4]);
    }
    printf("\n");
    _print_regs(obj);
}

// Like printf, but output is cpu->error
void error_printf(struct nios2 *cpu, const char *fmt, ...)
{
    va_list ap;
    int size = 0;

    va_start(ap, fmt);
    size = vsnprintf(NULL, size, fmt, ap);
    va_end(ap);

    if (size < 0) {
        return;
    }

    size++;     // For \0
    //size += strlen(cpu->error);
    int cur_size = 0;
    if (cpu->error != NULL) {
        cur_size = strlen(cpu->error);
    }

    cpu->error = realloc(cpu->error, size + cur_size);
    if (cpu->error == NULL) {
        return;
    }

    va_start(ap, fmt);
    size = vsnprintf(&cpu->error[cur_size], size, fmt, ap);
    if (size < 0) {
        free(cpu->error);
        return;
    }
    va_end(ap);

    return;
}

//////////////////////
// Memory Access
uint32_t access_mmio(struct nios2 *cpu, uint32_t addr, uint32_t val, int is_store)
{
    int i;
    for (i=0; i<MAX_MMIOS; i++) {
        if (cpu->mmios[i].addr == addr) {
            //printf("Found at %d, callback %p\n", i, cpu->mmios[i].callback);

            uint32_t ret = 0;
            PyObject *args;
            if (is_store) {
               args = Py_BuildValue("(l)", val);
            } else {
                //Py_INCREF(Py_None);
                args = Py_BuildValue("()");
            }
            PyObject *result = PyEval_CallObject(cpu->mmios[i].callback, args);
            if (result && PyLong_Check(result)) {
                ret = PyLong_AsLong(result);
            }
            Py_XDECREF(result);
            Py_DECREF(args);
            return ret;
        }
    }
    // MMIO not found...halt cpu
    cpu->halted = 1;

    error_printf(cpu, "ERROR: access out of bound memory: 0x%08x\n", addr);
    return 0;
}

uint32_t loadword(struct nios2 *cpu, uint32_t addr)
{

    uint32_t *p = (uint32_t *)cpu->mem;
    uint32_t off = addr/4;

    if (addr > cpu->mem_len) {
        // lookup mmio
        return access_mmio(cpu, addr, 0, 0);
    }
    return p[off];
}

void storeword(struct nios2 *cpu, uint32_t addr, uint32_t val)
{
    uint32_t *p = (uint32_t *)cpu->mem;
    uint32_t off = addr/4;

    if (addr > cpu->mem_len) {
        // lookup mmi
        access_mmio(cpu, addr, val, 1);
        return;
    }
    p[off] = val;
}

uint32_t _loadword(long obj, uint32_t addr)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    return loadword(cpu, addr);
}

void _storeword(long obj, uint32_t addr, uint32_t val)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    storeword(cpu, addr, val);
}


void _add_mmio(long obj, uint32_t addr, PyObject *callback)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    int i;
    for (i=0; i<MAX_MMIOS; i++) {
        if ((cpu->mmios[i].addr == addr) || cpu->mmios[i].addr == 0) {
            //printf("Adding MMIO 0x%08x to mmios[%d], callback %p\n", addr, i, callback);
            if (cpu->mmios[i].callback != NULL) {
                Py_XDECREF(cpu->mmios[i].callback);
            }
            Py_XINCREF(callback);
            cpu->mmios[i].addr = addr;
            cpu->mmios[i].callback = callback;
            return;
        }
    }
}

uint16_t loadhalfword(struct nios2 *cpu, uint32_t addr)
{
    uint16_t *p = (uint16_t *)cpu->mem;
    uint32_t off = addr/2;

    if (addr > cpu->mem_len) {
        return (uint16_t)access_mmio(cpu, addr, 0, 0);
    }
    return p[off];
}

void storehalfword(struct nios2 *cpu, uint32_t addr, uint16_t val)
{
    uint16_t *p = (uint16_t *)cpu->mem;
    uint32_t off = addr/2;

    if (addr > cpu->mem_len) {
        access_mmio(cpu, addr, val, 1);
        return;
    }
    p[off] = val;
}

uint8_t loadbyte(struct nios2 *cpu, uint32_t addr)
{
    uint8_t *p = (uint8_t *)cpu->mem;
    uint32_t off = addr;

    if (addr > cpu->mem_len) {
        return (uint8_t)access_mmio(cpu, addr, 0, 0);
    }
    return p[off];
}

void storebyte(struct nios2 *cpu, uint32_t addr, uint8_t val)
{
    uint8_t *p = (uint8_t *)cpu->mem;
    uint32_t off = addr;

    if (addr > cpu->mem_len) {
        access_mmio(cpu, addr, val, 1);
        return;
    }
    p[off] = val;
}


///////////////
// Helpers
uint32_t rotate_l32(uint32_t n, int m)
{
    uint64_t r = ((uint64_t)n) << (m & 0x1f);
    return (uint32_t)(r | (uint32_t)(r>>32));
}

uint32_t rotate_r32(uint32_t n, int m)
{
    uint64_t r = ((uint64_t)n) << 32;
    r >>= (m & 0x1f);
    return (uint32_t)((r>>32) | r);
}

// Called on call or callr
void push_callees(struct nios2 *cpu)
{
    struct callee_saved *head = cpu->callee_stack_head;
    struct callee_saved *new = malloc(sizeof(struct callee_saved));

    // Just copy all the registers, only check the ones
    // we care about. This costs us 128+4(+4) bytes per frame....
    new->pc = cpu->pc;
    memcpy(new->regs, cpu->regs, sizeof(uint32_t)*32);

    // Push this stack frame
    new->prev = head;
    cpu->callee_stack_head = new;
}

void mark_clobbered(struct nios2 *cpu, uint32_t pc, int reg_id, int interrupt)
{
    int i;
    for (i=0; i<cpu->clobbered_idx; i++) {
        if (cpu->clobbered_history[i].pc == pc &&
            cpu->clobbered_history[i].reg_id == reg_id) {
            // Already in the history
            return;
        }
    }
    // Add to history and log
    cpu->clobbered_history[cpu->clobbered_idx].pc = pc;
    cpu->clobbered_history[cpu->clobbered_idx].reg_id = reg_id;
    cpu->clobbered_history[cpu->clobbered_idx].interrupt = interrupt;
    //error_printf(cpu, "Function @0x%08x clobbered r%d\n", cpu->pc, reg_id);
    //printf("Function @0x%08x clobbered r%d\n", cpu->pc, reg_id);
    cpu->clobbered_idx++;
    cpu->clobbered_idx %= MAX_CLOBBERED;
}


PyObject *_get_clobbered(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    PyObject *list = PyList_New(cpu->clobbered_idx);
    if (!list) {
        return NULL;
    }
    int i;
    for (i = 0; i<cpu->clobbered_idx; i++) {
        PyObject *elt = Py_BuildValue("(lll)",
                                       cpu->clobbered_history[i].pc,
                                       cpu->clobbered_history[i].reg_id,
                                       cpu->clobbered_history[i].interrupt);
        if (!elt) {
            Py_DECREF(list);
            return NULL;
        }
        PyList_SET_ITEM(list, i, elt);
    }
    return list;
}

// Called on ret
void check_callees(struct nios2 *cpu, int interrupt)
{
    struct callee_saved *head = cpu->callee_stack_head;

    if (head == NULL) {
        // weird...but okay
        //printf("Warning: No callee stack on ret @0x%08x\n", cpu->pc);
        return;
    }

    // Callee-saved regs to check:
    int check_interrupt[] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                             17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 31};
    int check_func[]      = {16, 17, 18, 19, 20, 21, 22, 23, 27, 28, 31};

    // Default to interrupt
    int to_check_n = sizeof(check_interrupt)/sizeof(int);
    int *to_check = check_interrupt;
    if (!interrupt) {
        to_check_n = sizeof(check_func)/sizeof(int);
        to_check = check_func;
    }
    int i;
    for (i=0; i<to_check_n; i++) {
        int rid = to_check[i];
        if (cpu->regs[rid] != head->regs[rid]) {
            mark_clobbered(cpu, cpu->pc - 4, rid, interrupt);  // -4 because we already incremented PC
        }
    }

    // Pop this stack frame
    cpu->callee_stack_head = head->prev;
    free(head);
}

void do_interrupt(struct nios2 *cpu)
{

    //printf("Doing an interrupt at PC 0x%08x\n", cpu->pc);
    // estatus = status
    // PIE = 0
    // U = 0
    // ea = PC + 4
    // PC = 0x20
    uint32_t status = get_ctl_reg(cpu, 0);
    set_ctl_reg(cpu, 1, status);   // estatus = status
    set_ctl_reg(cpu, 0, status & ~3);   // PIE/U = 0
    set_reg(cpu, 29, cpu->pc);  // ea = PC+4 (assume pc+4 already happened)
    cpu->pc = 0x20;
    push_callees(cpu);
}

void _interrupt_cpu(long obj)
{
    do_interrupt((struct nios2 *)obj);
}

// Returns 1 if we are doing an interrupt (abort your current instruction)
// or 0 otherwise
int check_interrupt(struct nios2 *cpu)
{
    int PIE = get_ctl_reg(cpu, 0) & 1;
    uint32_t ienable = get_ctl_reg(cpu, 3);
    uint32_t ipending = get_ctl_reg(cpu, 4);

    if (PIE && (ipending&ienable)) {
        do_interrupt(cpu);
        return 1;
    }
    return 0;
}

////////////////
// R-types
void handle_r_type(struct nios2 *cpu, uint32_t opx, uint32_t rA, uint32_t rB, uint32_t rC, int imm5)
{
    switch (opx) {
        case 0x01: // eret
            check_callees(cpu, 1);
            set_ctl_reg(cpu, 0, get_ctl_reg(cpu, 1));   // status = estatus
            cpu->pc = get_reg(cpu, 29); // PC = ea
            break;
        case 0x02: // roli,
            set_reg(cpu, rC, rotate_l32(get_reg(cpu, rA), imm5));
            break;
        case 0x03: // rol,
            set_reg(cpu, rC, rotate_l32(get_reg(cpu, rA), get_reg(cpu, rB) & 0x1f));
            break;
        case 0x04: // flushp,
            break;
        case 0x05: // ret,
            check_callees(cpu, 0);
            cpu->pc = get_reg(cpu, 31);
            break;
        case 0x06: // nor,
            set_reg(cpu, rC, ~(get_reg(cpu, rA) | get_reg(cpu, rB)));
            break;
        case 0x07: // mulxuu,
            set_reg(cpu, rC, (((uint64_t)get_reg(cpu, rA)) * ((uint64_t)get_reg(cpu, rB))) >> 32);
            break;
        case 0x08: // cmpge,
            if (((int32_t)get_reg(cpu, rA)) >= ((int32_t)get_reg(cpu, rB))) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x09: // _bret,
            break;  // unimplemented
        case 0x0b: // ror,
            set_reg(cpu, rC, rotate_r32(get_reg(cpu, rA), get_reg(cpu, rB) & 0x1f));
            break;
        case 0x0c: // flushi,
            break;  // no cache
        case 0x0d: // jmp,
            cpu->pc = get_reg(cpu, rA);
            break;
        case 0x0e: // _and,
			set_reg(cpu, rC, get_reg(cpu, rA) & get_reg(cpu, rB));
			break;
        case 0x10: // cmplt,
            if (((int32_t)get_reg(cpu, rA)) < ((int32_t)get_reg(cpu, rB))) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x12: // slli,
            set_reg(cpu, rC, get_reg(cpu, rA) << imm5);
            break;
        case 0x13: // sll,
            set_reg(cpu, rC, get_reg(cpu, rA) << (get_reg(cpu, rB) & 0x1f));
            break;
        case 0x14: // wrprs,
            break;  //unimplemented
        case 0x16: // _or,
            set_reg(cpu, rC, get_reg(cpu, rA) | get_reg(cpu, rB));
            break;
        case 0x17: // mulxsu,
            set_reg(cpu, rC, (((int64_t)get_reg(cpu, rA)) * ((uint64_t)get_reg(cpu, rB))) >> 32);
            break;
        case 0x18: // cmpne,
            if (get_reg(cpu, rA) != get_reg(cpu, rB)) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x1a: // srli,
            set_reg(cpu, rC, get_reg(cpu, rA) >> imm5);
            break;
        case 0x1b: // srl,
            set_reg(cpu, rC, get_reg(cpu, rA) >> (get_reg(cpu, rB) & 0x1f));
            break;
        case 0x1c: // nextpc,
            set_reg(cpu, rC, cpu->pc);
            break;
        case 0x1d: // callr,
            set_reg(cpu, 31, cpu->pc);
            push_callees(cpu);
            cpu->pc = get_reg(cpu, rA);
            break;
        case 0x1e: // xor,
            set_reg(cpu, rC, get_reg(cpu, rA) ^ get_reg(cpu, rB));
            break;
        case 0x1f: // mulxss,
            set_reg(cpu, rC, (((int64_t)get_reg(cpu, rA)) * ((int64_t)get_reg(cpu, rB))) >> 32);
            break;
        case 0x20: // cmpeq,
            if (get_reg(cpu, rA) == get_reg(cpu, rB)) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x24: // divu,
            if (get_reg(cpu, rB) != 0) {
                set_reg(cpu, rC, get_reg(cpu, rA) / get_reg(cpu, rB));
            }
            break;
        case 0x25: // div,
            if (get_reg(cpu, rB) != 0) {
                set_reg(cpu, rC, (uint32_t)((int32_t)get_reg(cpu, rA) / ((int32_t)get_reg(cpu, rB))));
            }
            break;
        case 0x26: // rdctl
            set_reg(cpu, rC, get_ctl_reg(cpu, imm5));
            break;
        case 0x27: // mul,
            set_reg(cpu, rC, get_reg(cpu, rA) * get_reg(cpu, rB));
            break;
        case 0x28: // cmpgeu,
            if (get_reg(cpu, rA) >= get_reg(cpu, rB)) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x29: // initi,
            break;
        case 0x2d: // trap,
            do_interrupt(cpu);
            break;
        case 0x2e: // wrctl,
            set_ctl_reg(cpu, imm5, get_reg(cpu, rA));
            break;
        case 0x30: // cmpltu,
            if (get_reg(cpu, rA) < get_reg(cpu, rB)) {
                set_reg(cpu, rC, 1);
            } else {
                set_reg(cpu, rC, 0);
            }
            break;
        case 0x31: // add,
			set_reg(cpu, rC, get_reg(cpu, rA) + get_reg(cpu, rB));
			break;
        case 0x34: // _break,
			cpu->halted = 1;
			break;
        case 0x36: // sync,
            break;
        case 0x39: // sub,
            set_reg(cpu, rC, get_reg(cpu, rA) - get_reg(cpu, rB));
            break;
        case 0x3a: // srai,
            set_reg(cpu, rC, ((int32_t)get_reg(cpu, rA)) >> imm5);
            break;
        case 0x3b: // sra,
            set_reg(cpu, rC, ((int32_t)get_reg(cpu, rA)) >> (get_reg(cpu, rB) & 0x1f));
            break;
    }
}

void one_instr(struct nios2 *cpu)
{
    uint32_t instr = loadword(cpu, cpu->pc);
    int op = instr & 0x3f;

    uint32_t imm26   = (instr >> 6) & 0x3ffffff;
    uint32_t rA      = (instr >> 27);
    uint32_t rB      = (instr >> 22) & 0x1f;
    uint32_t rC      = (instr >> 17) & 0x1f;
    uint32_t opx     = (instr >> 11) & 0x3f;
    uint32_t imm5    = (instr >> 6) & 0x1f;
    int16_t  imm16   = (instr >> 6) & 0xffff;
    uint32_t ea      = get_reg(cpu, rA) + imm16;

    // Increment PC
    cpu->pc += 4;

    // Maybe interrupt here...
    if (check_interrupt(cpu) == 1) {
        return;
    }

    switch (op) {
        /////////////////
        // J-types:
        case 0x00:  // call
            set_reg(cpu, 31, cpu->pc);
            push_callees(cpu);
            cpu->pc = (cpu->pc & 0xf0000000) | (imm26 << 2);
            break;
        case 0x01:  // jmpi
            cpu->pc = (cpu->pc & 0xf0000000) | (imm26 << 2);
            break;
        case 0x38:  // rdprs
            // Unimplemented
            break;

        /////////////////
        // R-types:
        case 0x3a:
            handle_r_type(cpu, opx, rA, rB, rC, imm5);
            break;

        ////////////////
        // I-types:
        case 0x03: //ldbu,
            set_reg(cpu, rB, loadbyte(cpu, ea));
            break;
        case 0x04: //addi,
			set_reg(cpu, rB, get_reg(cpu, rA) + (int32_t)imm16);
			break;
        case 0x05: //stb,
            storebyte(cpu, ea, get_reg(cpu, rB) & 0xff);
            break;
        case 0x06: //br,
            cpu->pc += imm16;
            break;
        case 0x07: //ldb,
            set_reg(cpu, rB, (int8_t)loadbyte(cpu, ea));
            break;
        case 0x08: //cmpgei,
            if (((int32_t)get_reg(cpu, rA)) >= imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x0b: //ldhu,
            set_reg(cpu, rB, loadhalfword(cpu, ea));
            break;
        case 0x0c: //andi,
            set_reg(cpu, rB, get_reg(cpu, rA) & (uint32_t)imm16);
            break;
        case 0x0d: //sth,
            storehalfword(cpu, ea, get_reg(cpu, rB) & 0xffff);
            break;
        case 0x0e: //bge,
            if (((int32_t)get_reg(cpu, rA)) >= ((int32_t)get_reg(cpu, rB))) {
                cpu->pc += imm16;
            }
            break;
        case 0x0f: //ldh,
            set_reg(cpu, rB, (int16_t)loadhalfword(cpu, ea));
            break;
        case 0x10: //cmplti,
            if (((int32_t)get_reg(cpu, rA)) < imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x13: //initda,
            break;
        case 0x14: //ori,
            set_reg(cpu, rB, get_reg(cpu, rA) | ((uint32_t)imm16));
            break;
        case 0x15: //stw,
            storeword(cpu, ea, get_reg(cpu, rB));
            break;
        case 0x16: //blt,
            if (((int32_t)get_reg(cpu, rA)) < ((int32_t)get_reg(cpu, rB))) {
                cpu->pc += imm16;
            }
            break;
        case 0x17: //ldw,
            set_reg(cpu, rB, loadword(cpu, ea));
            break;
        case 0x18: //cmpnei,
            if (get_reg(cpu, rA) != imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x1b: //flushda,
            break;
        case 0x1c: //xori,
            set_reg(cpu, rB, get_reg(cpu, rA) ^ (uint32_t)imm16);
            break;
        case 0x1e: //bne,
            if (get_reg(cpu, rA) != get_reg(cpu, rB)) {
                cpu->pc += imm16;
            }
            break;
        case 0x20: //cmpeqi,
            if (get_reg(cpu, rA) == imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x23: //ldbu,   # ldbuio
            set_reg(cpu, rB, (uint8_t)loadbyte(cpu, ea));
            break;
        case 0x24: //muli,
            set_reg(cpu, rB, get_reg(cpu, rA) * (int32_t)imm16);
            break;
        case 0x25: //stb,    # stbio
            storebyte(cpu, ea, get_reg(cpu, rB) & 0xff);
            break;
        case 0x26: //beq,
            if (get_reg(cpu, rA) == get_reg(cpu, rB)) {
                cpu->pc += imm16;
            }
            break;
        case 0x27: //ldb,    # ldbio
            set_reg(cpu, rB, (int8_t)loadbyte(cpu, ea));
            break;
        case 0x28: //cmpgeui,
            if (get_reg(cpu, rA) >= (uint32_t)imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x2b: //ldhu,   # ldhuio
            set_reg(cpu, rB, loadhalfword(cpu, ea));
            break;
        case 0x2c: //andhi,
            set_reg(cpu, rB, get_reg(cpu, rA) & (((uint32_t)imm16) << 16));
            break;
        case 0x2d: //sth,    # sthio
            storehalfword(cpu, ea, get_reg(cpu, rB) & 0xffff);
            break;
        case 0x2e: //bgeu,
            if (get_reg(cpu, rA) >= get_reg(cpu, rB)) {
                cpu->pc += imm16;
            }
            break;
        case 0x2f: //ldh,    # ldhio
            set_reg(cpu, rB, (int16_t)loadhalfword(cpu, ea));
            break;
        case 0x30: //cmpltui,
            if (get_reg(cpu, rA) < (uint32_t)imm16) {
                set_reg(cpu, rB, 1);
            } else {
                set_reg(cpu, rB, 0);
            }
            break;
        case 0x33: //initd,
            break;
        case 0x34: //orhi,
            set_reg(cpu, rB, get_reg(cpu, rA) | (((uint32_t)imm16) << 16));
            break;
        case 0x35: //stw,    # stwio
            storeword(cpu, ea, get_reg(cpu, rB));
        case 0x36: //bltu,
            if (get_reg(cpu, rA) < get_reg(cpu, rB)) {
                cpu->pc += imm16;
            }
            break;
        case 0x37: //ldw,    # ldwio
            set_reg(cpu, rB, loadword(cpu, ea));
            break;
        case 0x3b: //flushd,
            break;
        case 0x3c: //xorhi,
            set_reg(cpu, rB, get_reg(cpu, rA) ^ (((uint32_t)imm16) << 16));
            break;
    }
}

void _one_step(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    one_instr(cpu);
}

int _run_until_halted(long obj, int instr_limit)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    int n = 0;
    while (cpu->halted==0 && (instr_limit==-1 || n<instr_limit)) {
        one_instr(cpu);
        n++;
    }
    if (n == instr_limit) {
        cpu->halted = 1;
        error_printf(cpu, "Instruction limit reached: %d\n", n);
    }
    return n;
}

void _halt_cpu(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    cpu->halted = 1;
}

void _unhalt_cpu(long obj)
{
    struct nios2 *cpu = (struct nios2 *)obj;
    cpu->halted = 0;
}
