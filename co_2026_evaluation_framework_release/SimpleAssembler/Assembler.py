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
