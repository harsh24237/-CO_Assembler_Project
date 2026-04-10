import sys
import os

def sign_extend(val, bits):
    sign = 1 << (bits - 1)
    return (val & (sign - 1)) - (val & sign)

def to_signed(val):
    val &= 0xFFFFFFFF
    return val if val < 0x80000000 else val - 0x100000000

def write_reg(regs, rd, val):
    if rd != 0:
        regs[rd] = val & 0xFFFFFFFF

def read_mem(data_mem, stack_mem, addr):
    addr &= 0xFFFFFFFF
    if 0x00010000 <= addr <= 0x0001007C:
        return data_mem[(addr - 0x00010000) // 4]
    return stack_mem.get(addr, 0)

def write_mem(data_mem, stack_mem, addr, val):
    addr &= 0xFFFFFFFF
    if 0x00010000 <= addr <= 0x0001007C:
        data_mem[(addr - 0x00010000) // 4] = val & 0xFFFFFFFF
    else:
        stack_mem[addr] = val & 0xFFFFFFFF
    return data_mem, stack_mem

def bin_trace(pc, regs):
    return "0b" + format(pc & 0xFFFFFFFF, '032b') + " " + \
           " ".join("0b" + format(r & 0xFFFFFFFF, '032b') for r in regs)

def dec_trace(pc, regs):
    return str(pc) + " " + " ".join(str(to_signed(r)) for r in regs)

def simulator(input_file):

    instructions = []
    with open(input_file, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            if len(line) != 32:
                print(f"Error at line {i}: Instruction not 32 bits")
                sys.exit(1)
            instructions.append(line)

    regs = [0] * 32
    regs[2] = 0x17C  # stack pointer = 0x0000017C per spec
    pc = 0

    data_mem = [0] * 32
    stack_mem = {}

    bin_out = []
    dec_out = []
