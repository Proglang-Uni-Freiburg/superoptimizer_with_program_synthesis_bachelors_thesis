from riscv_ast import *
from typing import List
from z3 import *

def run_riscv(riscv: List[Instr], args: dict[str, int]) -> int:
    r = 0
    regs = args.copy()
    regs[py_name(Zero())] = 0
    for i in riscv:
        match i:
            case Instr(op, (Reg() as dest, Reg() as arg, imm)) if type(imm) != Reg:
                left = regs[py_name(arg)]
                regs[py_name(dest)] = match_op(op)(left, imm)
            case Instr(op, (Reg() as dest, Reg() as arg1, Reg() as arg2)):
                left = regs[py_name(arg1)]
                right = regs[py_name(arg2)]
                regs[py_name(dest)] = match_op(op)(left, right)
            case _:  # ignore invalid code
                continue
        # lookup args if necessary (now add associated var name to Regvar in ast)
    return regs[py_name(ReturnReg())]