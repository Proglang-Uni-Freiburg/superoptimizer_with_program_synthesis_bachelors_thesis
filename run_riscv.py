from riscv_dsl import *
from typing import List
from z3 import *

# optional argument for z3 solver, because rule to avoid division/modulo by zero might need to be added
def run_riscv(riscv: List[Instr], args: dict[str, int | BitVecRef], s = Solver()) -> int | BitVecRef:
    r = 0
    regs = args.copy()
    regs[py_name(Zero())] = 0
    for i in riscv:
        match i:
            case Instr(op, (Reg() as dest, Reg() as arg1, Reg() as arg2)):
                left = regs[py_name(arg1)]
                right = regs[py_name(arg2)]
                if op == 'div' or op == 'rem':
                    s.add(right != 0)
                regs[py_name(dest)] = match_op(op)(left, right)
            case Instr(op, (Reg() as dest, Reg() as arg, imm)):
                left = regs[py_name(arg)]
                if op == 'slli' or op == 'srai':
                    s.add(imm > 0)
                regs[py_name(dest)] = match_op(op)(left, imm)
            case _:  # ignore invalid code
                continue
        # lookup args if necessary (now add associated var name to Regvar in ast)
    return regs[py_name(ReturnReg())]