# base class for arithmetic RISC V assembly instructions
from typing import List, Callable, Any
from z3 import BitVecRef, BV2Int, SRem


pydiv =  lambda x, y: int(x / y) if type(x) is int and type(y) is int else x / y
pymod = lambda x, y: (x - (y * int(x / y))) if type(x) is int and type(y) is int else SRem(x, y)

def match_op(op: str) -> Callable[[Any, Any], Any]:
    match op:
        case "add" | "addi":
            return lambda x, y: x + y
        case "sub" | "subi":
            return lambda x, y: x - y
        case "slli":  # left shift (logical = arithmetic)
            return lambda x, y: x << y
        case "srai":  # right shift (arithmetic)
            return lambda x, y: x >> y
        case "mul":  # for this case and following, immediate values are not supported
            return lambda x, y: x * y
        case "div":
            return lambda x, y: pydiv(x, y)
        case "rem":  # remainder, signed
            return lambda x, y: pymod(x, y)
        case _:
            raise Exception("Could not match Instruction Operator")


# Representation for Registers in RISC V. Does not consider floating point registers because we never use those
class Reg:
    num: int
    const_regs: List[int] = [5, 6, 7, 28, 29, 30, 31]

    def __init__(self, num: int):
        self.num = num
        assert num in self.const_regs

    # the same as corresponding representation in actual risc-v assembly
    def __repr__(self):
        return "x" + str(self.num)

    # define equality on repr
    def __eq__(self, other):
        return repr(self) == repr(other)


class Regvar(Reg):
    var_regs: List[int] = list(range(1, 8))
    name: str

    def __init__(self, num: int, name: str):
        self.num = num
        self.name = name
        assert num in self.var_regs

    def py_name(self) -> str:
        return self.name

    def __repr__(self):
        return "a" + str(self.num)


class Zero(Reg):
    def __init__(self):
        self.num = 0


class ReturnReg(Regvar):
    def __init__(self):
        self.num = 0

class TempRes(Regvar):
    def __init__(self):
        self.num = 1

def py_name(r: Reg) -> str:
    return r.py_name() if type(r) == Regvar else repr(r)


# Representation of instructions with a variable number of arguments. Only represents instructions with a destination
class Instr:
    __match_args__ = ("op", "args")
    
    arith_ops = ['addi', 'subi', 'slli', 'srai', 'add', 'sub', 'mul', 'div', 'rem']
    op: str
    # args: Tuple[Reg | int]  # register or immediate

    def __init__(self, op: str, *args: Reg | int | BitVecRef):
        self.op = op.lower()
        self.args = args

    def __repr__(self):
        return self.op + " " + ", ".join(repr(a) for a in self.args)

    # define equality on components instead of object identity
    def __eq__(self, other):
        if type(other) is Instr:
            if self.op == other.op and len(self.args) == len(other.args):
                return (all(self.args[i] == other.args[i] for i in range(len(self.args))))
        else:
            return False


class Regassign(Instr):
    def __init__(self, reg: Reg, num: int):
        self.op = "addi"
        self.args = (reg, Zero(), num)


def only_arith_instrs(instrs: List[Instr]) -> List[Instr]:
    r = []
    for instr in instrs:
        if instr.op in Instr.arith_ops:
            r.append(instr)
    return r

prog_start: List[Instr] = [Instr(".global _start"), Instr(""), Instr("_start:")]
prog_end: List[Instr] = [Instr("addi", Regvar(7, 'null'), Zero(), 93), Instr("ecall")]