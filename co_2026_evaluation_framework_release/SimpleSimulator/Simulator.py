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


    while True:
        idx = pc // 4
        if idx < 0 or idx >= len(instructions):
            break

        inst = instructions[idx]

        # Virtual Halt: beq zero, zero, 0
        if inst == "00000000000000000000000001100011":
            bin_out.append(bin_trace(pc, regs))
            dec_out.append(dec_trace(pc, regs))
            break

        next_pc = pc + 4
        opcode = inst[25:32]

        try:

            # R-TYPE
            if opcode == "0110011":
                f7  = inst[0:7]
                rs2 = int(inst[7:12], 2)
                rs1 = int(inst[12:17], 2)
                f3  = inst[17:20]
                rd  = int(inst[20:25], 2)

                a = regs[rs1]
                b = regs[rs2]

                if f3 == "000":
                    if f7 == "0100000":
                        res = to_signed(a) - to_signed(b)   # sub
                    else:
                        res = a + b                          # add
                elif f3 == "001":
                    res = a << (b & 31)                      # sll
                elif f3 == "010":
                    res = 1 if to_signed(a) < to_signed(b) else 0   # slt
                elif f3 == "011":
                    res = 1 if (a & 0xFFFFFFFF) < (b & 0xFFFFFFFF) else 0  # sltu
                elif f3 == "100":
                    res = a ^ b                              # xor
                elif f3 == "101":
                   res = (a & 0xFFFFFFFF) >> (b & 31)  # srl (logical)
                elif f3 == "110":
                    res = a | b                              # or
                elif f3 == "111":
                    res = a & b                              # and
                else:
                    raise Exception("Invalid R-type funct3")

                write_reg(regs, rd, res)

            # I-TYPE 
            elif opcode == "0010011":
                imm = sign_extend(int(inst[0:12], 2), 12)
                rs1 = int(inst[12:17], 2)
                f3  = inst[17:20]
                rd  = int(inst[20:25], 2)

                if f3 == "000":
                    res = regs[rs1] + imm                  
                elif f3 == "011":
                    res = 1 if (regs[rs1] & 0xFFFFFFFF) < (imm & 0xFFFFFFFF) else 0  # sltiu
                  
                else:
                    raise Exception("Invalid I-type funct3")

                write_reg(regs, rd, res)
# LOAD (LW)
            elif opcode == "0000011":
                imm = sign_extend(int(inst[0:12], 2), 12)
                rs1 = int(inst[12:17], 2)
                f3  = inst[17:20]
                rd  = int(inst[20:25], 2)

                addr = (regs[rs1] + imm) & 0xFFFFFFFF
                if f3 == "010":                             # lw
                    val = read_mem(data_mem, stack_mem, addr)
                else:
                    raise Exception(f"Unsupported load funct3={f3}")
                write_reg(regs, rd, val)

            # STORE (SW)
            elif opcode == "0100011":
                imm = sign_extend(int(inst[0:7] + inst[20:25], 2), 12)
                rs1 = int(inst[12:17], 2)
                rs2 = int(inst[7:12], 2)
                f3  = inst[17:20]

                addr = (regs[rs1] + imm) & 0xFFFFFFFF
                if f3 == "010":                             # sw
                    data_mem, stack_mem = write_mem(data_mem, stack_mem, addr, regs[rs2])
                else:
                    raise Exception(f"Unsupported store funct3={f3}")

            # BRANCH
            elif opcode == "1100011":
                imm = (int(inst[0])   << 12) | \
                      (int(inst[24])  << 11) | \
                      (int(inst[1:7], 2) << 5) | \
                      (int(inst[20:24], 2) << 1)
                imm = sign_extend(imm, 13)

                rs1 = int(inst[12:17], 2)
                rs2 = int(inst[7:12], 2)
                f3  = inst[17:20]

                cond = False
                if f3 == "000":
                    cond = regs[rs1] == regs[rs2]                               # beq
                elif f3 == "001":
                    cond = regs[rs1] != regs[rs2]                               # bne
                elif f3 == "100":
                    cond = to_signed(regs[rs1]) < to_signed(regs[rs2])          # blt
                elif f3 == "101":
                    cond = to_signed(regs[rs1]) >= to_signed(regs[rs2])         # bge
                elif f3 == "110":
                    cond = (regs[rs1] & 0xFFFFFFFF) < (regs[rs2] & 0xFFFFFFFF) # bltu
                elif f3 == "111":
                    cond = (regs[rs1] & 0xFFFFFFFF) >= (regs[rs2] & 0xFFFFFFFF)# bgeu
                else:
                    raise Exception(f"Invalid branch funct3={f3}")

                next_pc = pc + (imm if cond else 4)

            # JAL
            elif opcode == "1101111":
                imm = (int(inst[0])        << 20) | \
                      (int(inst[1:11], 2)  << 1)  | \
                      (int(inst[11])       << 11) | \
                      (int(inst[12:20], 2) << 12)
                imm = sign_extend(imm, 21)

                rd = int(inst[20:25], 2)
                write_reg(regs, rd, pc + 4)
                next_pc = pc + imm

