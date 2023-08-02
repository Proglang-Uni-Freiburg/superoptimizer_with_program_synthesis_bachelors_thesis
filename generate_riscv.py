from z3 import *
from riscv_ast import *
from run_riscv import *
from typing import Tuple


class NaiveGen():
    c_min = -10
    c_max = 10
    all_regs = [Reg(x) for x in Reg.const_regs] + [Zero(), ReturnReg()]
    arith_ops_imm: List[str] = ["addi", "subi"]
    arith_ops: List[str] = ["add", "sub"]
    arg_regs: List[Reg]

    def __init__(self, args: List[str], examples: List[Tuple[List[int], int]]):
        self.args = args
        self.examples = examples
        self.arg_regs = [Regvar(i, x) for i, x in zip(ReturnReg().var_regs, args)]
        self.s = Solver()

    def naive_gen(self) -> List[Instr]:
        i = Int('i')
        possibilities = self.code_sketches()
        for p in possibilities:
            self.s.push()
            for (inputs, output) in self.examples:  # note that there needs to always be at least one example
                success = True
                try:
                    match p:
                        case [Instr("sub", [ReturnReg(), Regvar(), Regvar()])]:
                            pass
                    r = run_riscv(p, {self.args[i]: inputs[i] for i in range(len(self.args))})
                    self.s.add(r == output)
                except:  # this means the code was invalid. skip to the next one
                    success = False
                    break
            if not success:
                self.s.pop()
                continue
            if self.s.check() == sat:
                print(self.s.model())
                return p
            self.s.pop()

        raise Exception("oh no")

    def code_sketches(self) -> List[List[Instr]]:
        possibilities = []
        c = Int('c')
        self.s.add(c >= self.c_min)
        self.s.add(c <= self.c_max)

        # all one-liner possibilties
        for op in self.arith_ops_imm:
            for arg in self.all_regs + self.arg_regs:
                possibilities.append([Instr(op, ReturnReg(), arg, c)])
        for op in self.arith_ops:
            for arg1 in self.all_regs + self.arg_regs:
                for arg2 in self.all_regs + self.arg_regs:
                    possibilities.append([Instr(op, ReturnReg(), arg1, arg2)])

        return possibilities

if __name__ == "__main__":
    gen = NaiveGen(['x', 'y'], [([1, 2], -1), ([6, 4], 2)])  # NOTE: order of arguments always has to be the same in the lists
    r = gen.naive_gen()
    print(repr(r))


# smart generation meaning: only try valid code.
def smart_gen():
    pass