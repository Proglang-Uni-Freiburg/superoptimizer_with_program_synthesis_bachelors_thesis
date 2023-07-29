# base class for arithmetic RISC V assembly instructions
from typing import Tuple


# Representation for Registers in RISC V. Does not consider floating point registers because we never use those
class Reg:
    num: int

    def __init__(self, num: int):
        self.num = num

    def __repr__(self):
        return "x" + str(self.num)


class Var(Reg):
    def __repr__(self):
        return "a" + str(self.num)


class Zero(Reg):
    def __init__(self):
        self.num = 0


# Representation of instructions with a variable number of arguments. Only represents instructions with a destination
class Instr:
    instr: str
    args: Tuple[Reg | int]  # register or immediate
    dest: Reg

    def __init__(self, instr: str, *args: Reg | int):
        self.instr = instr
        self.args = args

    def __repr__(self):
        return self.instr + " " + ", ".join(repr(a) for a in self.args)


class Assign:
    reg: Reg
    num: int

    def __init__(self, reg: Reg, num: int):
        self.reg = reg
        self.num = num

    def __repr__(self):
        return "addi " + repr(self.reg) + ", zero, " + repr(self.num)