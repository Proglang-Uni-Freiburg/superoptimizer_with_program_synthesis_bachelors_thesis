from z3 import *
from riscv_ast import *
from run_riscv import *
from typing import Tuple


class NaiveGen():
    c_min = -10
    c_max = 10
    all_regs = [Reg(x) for x in Reg.const_regs] + [Zero(), ReturnReg()]
    arith_ops: List[str] = ["addi", "add"]
    arg_regs: List[Reg]

    def __init__(self, args: List[str], examples: List[Tuple[List[int], int]]):
        self.args = args
        self.examples = examples
        self.arg_regs = [Regvar(i, x) for i, x in zip(ReturnReg().var_regs, args)]

    def naive_gen(self) -> List[Instr]:
        s = Solver()
        c = Int('c')
        s.add(c >= self.c_min)
        s.add(c <= self.c_max)
        r = [Instr("addi", ReturnReg(), self.arg_regs[0], c)]  # IMPORTANT currently only generates this type of expression
        for (inputs, output) in self.examples:
            s.add(run_riscv(r, {self.args[i]: inputs[i] for i in range(len(self.args))}) == output)
        if s.check() == sat:
            print(s.model())
            return r
        else:
            raise Exception("oh no")


if __name__ == "__main__":
    gen = NaiveGen(['x'], [([1], 1)])
    r = gen.naive_gen()
    print(repr(r))


# uses symbolic c instead of trying all possibilities
def symbolic_c_gen():
    pass


# smart generation meaning: only try valid code.
def smart_gen():
    pass