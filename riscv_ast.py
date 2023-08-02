# base class for arithmetic RISC V assembly instructions
from typing import List, Callable, Any


def match_op(op: str) -> Callable[[Any, Any], Any]:
    match op:
        case "add" | "addi":
            return lambda x, y: x + y
        case "sub" | "subi":
            return lambda x, y: x - y
        case "mul" | "muli":
            return lambda x, y: x * y
        case "div" | "divi":
            return lambda x, y: x // y
        case _:
            raise Exception("Could not match Instruction Operator")


# Representation for Registers in RISC V. Does not consider floating point registers because we never use those
class Reg:
    num: int
    const_regs: List[int] = [5, 6, 7, 28, 29, 30, 31]

    def __init__(self, num: int):
        self.num = num
        assert num in self.const_regs

    def __repr__(self):
        return "x" + str(self.num)


class Var(Reg):
    var_regs: List[int] = list(range(2, 8))
    name: str

    def __init__(self, num: int, name: str):
        self.num = num
        self.name = name
        assert num in self.var_regs

    def py_name(self) -> str:
        return self.name

    def __repr__(self):  # TODO: include check that number is valid
        return "a" + str(self.num)


class Zero(Reg):
    def __init__(self):
        self.num = 0


class ReturnReg(Var):
    def __init__(self):
        self.num = 0


def py_name(r: Reg) -> str:
    return r.py_name() if type(r) == Var else repr(r)


# Representation of instructions with a variable number of arguments. Only represents instructions with a destination
class Instr:
    __match_args__ = ("instr", "args")
    instr: str
    # args: Tuple[Reg | int]  # register or immediate

    def __init__(self, instr: str, *args: Reg | int):
        self.instr = instr.lower()
        self.args = args

    def __repr__(self):
        return self.instr + " " + ", ".join(repr(a) for a in self.args)


class Regassign(Instr):
    def __init__(self, reg: Reg, num: int):
        self.instr = "addi"
        self.args = (reg, Zero(), num)


prog_start: List[Instr] = [Instr(".global _start"), Instr(""), Instr("_start:")]
prog_end: List[Instr] = [Instr("addi", Var(7, 'null'), Zero(), 93), Instr("ecall")]