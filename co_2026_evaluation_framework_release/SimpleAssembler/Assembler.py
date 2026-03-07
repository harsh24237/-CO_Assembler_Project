import sys
import re

# instruction opcode table
opcode_table = {

    # R type
    "add": ("0110011","000","0000000"),
    "sub": ("0110011","000","0100000"),
    "or":  ("0110011","110","0000000"),
    "srl": ("0110011","101","0000000"),
    "slt": ("0110011","010","0000000"),
    "xor": ("0110011","100","0000000"),

    # I type
    "addi":("0010011","000"),
    "lw":  ("0000011","010"),
    "jalr":("1100111","000"),

    # S type
    "sw":("0100011","010"),

    # B type
    "beq": ("1100011","000"),
    "bne": ("1100011","001"),
    "blt": ("1100011","100"),
    "bge": ("1100011","101"),
    "bltu":("1100011","110"),

    # J type
    "jal":("1101111",)
}

# register table
reg_table = {
    "zero":0,"ra":1,"sp":2,"gp":3,"tp":4,
    "t0":5,"t1":6,"t2":7,
    "s0":8,"s1":9,
    "a0":10,"a1":11,"a2":12,"a3":13,"a4":14,
    "a5":15,"a6":16,"a7":17,
    "s2":18,"s3":19,"s4":20,"s5":21,
    "s6":22,"s7":23,"s8":24,"s9":25,
    "s10":26,"s11":27,
    "t3":28,"t4":29,"t5":30,"t6":31
}


def decode_line(line, pc, label_dict):

    temp = line.replace(",", " ")
    parts = re.split(r'\s+', temp.strip())

    if len(parts) == 0:
        return None

    inst = parts[0]

    if inst not in opcode_table:
        return None

    info = opcode_table[inst]

    # ---------- R TYPE ----------
    if inst in ["add","sub","slt","srl","or","xor"]:

        rd = reg_table[parts[1]]
        rs1 = reg_table[parts[2]]
        rs2 = reg_table[parts[3]]

        opcode = info[0]
        funct3 = info[1]
        funct7 = info[2]

        return funct7 + format(rs2,'05b') + format(rs1,'05b') + funct3 + format(rd,'05b') + opcode


    # ---------- I TYPE ----------
    if inst in ["addi","jalr"]:

        rd = reg_table[parts[1]]
        rs1 = reg_table[parts[2]]
        imm = int(parts[3])

        imm_bits = format(imm & 0xFFF,'012b')

        return imm_bits + format(rs1,'05b') + info[1] + format(rd,'05b') + info[0]


    # ---------- LOAD ----------
    if inst == "lw":

        rd = reg_table[parts[1]]

        m = re.match(r'(-?\d+)\((\w+)\)', parts[2])

        if m:
            offset = int(m.group(1))
            base = reg_table[m.group(2)]

            imm_bits = format(offset & 0xFFF,'012b')

            return imm_bits + format(base,'05b') + info[1] + format(rd,'05b') + info[0]


    # ---------- STORE ----------
    if inst == "sw":

        rs2 = reg_table[parts[1]]

        m = re.match(r'(-?\d+)\((\w+)\)', parts[2])

        if m:

            offset = int(m.group(1))
            base = reg_table[m.group(2)]

            imm_bits = format(offset & 0xFFF,'012b')

            return imm_bits[:7] + format(rs2,'05b') + format(base,'05b') + info[1] + imm_bits[7:] + info[0]


    # ---------- BRANCH ----------
    if inst in ["beq","bne","blt","bge","bltu"]:

        rs1 = reg_table[parts[1]]
        rs2 = reg_table[parts[2]]
        target = parts[3]

        if target in label_dict:
            offset = label_dict[target] - pc
        else:
            offset = int(target)

        if offset < 0:
            offset = (1 << 13) + offset

        imm = format(offset,'013b')

        return imm[0] + imm[2:8] + format(rs2,'05b') + format(rs1,'05b') + info[1] + imm[8:12] + imm[1] + info[0]


    # ---------- J TYPE ----------
    if inst == "jal":

        rd = reg_table[parts[1]]
        target = parts[2]

        if target in label_dict:
            offset = label_dict[target] - pc
        else:
            offset = int(target)

        if offset < 0:
            offset = (1 << 21) + offset

        imm = format(offset,'021b')

        return imm[0] + imm[10:20] + imm[9] + imm[1:9] + format(rd,'05b') + info[0]

    return None


def run_assembler(out_file, in_file):

    f = open(in_file)
    lines = f.readlines()

    label_dict = {}
    inst_list = []

    pc = 0

    for i in range(len(lines)):

        line = lines[i].strip()

        if line == "" or line.startswith("#"):
            continue

        if ":" in line:

            tag = line.split(":")[0].strip()
            label_dict[tag] = pc

            line = line.split(":")[1].strip()

        if line != "":
            inst_list.append(line)
            pc += 4

    results = []

    pc = 0

    for i in range(len(inst_list)):

        line = inst_list[i]

        binary = decode_line(line, pc, label_dict)

        if binary is None:
            print("Error in instruction:", line)
        else:
            results.append(binary)

        pc += 4

    out = open(out_file,"w")

    for i in range(len(results)):
        out.write(results[i] + "\n")

    print("Assembly finished")


if len(sys.argv) < 3:
    print("Usage: python assembler.py input.asm output.txt")
else:
    run_assembler(sys.argv[2], sys.argv[1])
