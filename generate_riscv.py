from z3 import *
from riscv_ast import *
from run_riscv import *
from typing import Tuple


class RiscvGen():
    c_min = -10
    c_max = 10
    max_depth = 10
    consts = []
    all_regs = [Reg(x) for x in Reg.const_regs] + [Zero(), ReturnReg()]
    arith_ops_imm: List[str] = ["addi", "subi"]
    arith_ops: List[str] = ["add", "sub"]
    arg_regs: List[Reg]

    def __init__(self, args: List[str]):
        self.args = args
        self.arg_regs = [Regvar(i, x) for i, x in zip(ReturnReg().var_regs, args)]
        self.s = Solver()


    def replace_consts(self, instrs: List[Instr]):
        result = []
        for instr in instrs:
            match instr:
                case Instr(op, [dest, arg1, ArithRef() as c]):
                    c_eval = self.s.model().eval(c)
                    result += [Instr(op, dest, arg1, int(c_eval.as_string()))]
                case i:
                    result += [i]
        return result


    # NOTE: Maybe leave the naive solver like this. 2-line solutions are the limit
    def naive_gen(self, examples: List[Tuple[List[int], int]]) -> List[Instr]:
        # TODO: find out if we can avoid running the solver as often!
        i = Int('i')
        count = 0
        possibilities = self.code_sketches()
        for p in possibilities:
            self.s.push()
            for (inputs, output) in examples:  # note that there needs to always be at least one example
                success = True
                # match p:
                #     case [Instr("sub", [_, Regvar(), Regvar()]), Instr("addi", [_, _, _])]:
                #         pass
                try:
                    r = run_riscv(p, {self.args[i]: inputs[i] for i in range(len(self.args))})
                    self.s.add(r == output)
                except:  # this means the code was invalid. skip to the next one
                    success = False
                    break
            if not success:
                self.s.pop()
                continue
            count += 1
            if self.s.check() == sat:
                return self.replace_consts(p)
            self.s.pop()

        raise Exception("oh no")

    def code_sketches(self) -> List[List[Instr]]:
        possibilities = []
        c = Int('c')
        self.s.add(c >= self.c_min)
        self.s.add(c <= self.c_max)

        # Important: start list with simple solutions and get more complex later on
        # all one-liner possibilties
        for op in self.arith_ops_imm:
            for arg in self.all_regs + self.arg_regs:
                possibilities.append([Instr(op, ReturnReg(), arg, c)])
        for op in self.arith_ops:
            for arg1 in self.all_regs + self.arg_regs:
                for arg2 in self.all_regs + self.arg_regs:
                    possibilities.append([Instr(op, ReturnReg(), arg1, arg2)])

        copy = possibilities.copy()
        c2 = Int('c2')
        self.s.add(c2 >= self.c_min)
        self.s.add(c2 <= self.c_max)
        # all possible two-liners:
        # NOTE: if the if-clause is removed, the list length goes from 57.288 to 627.528
        # reduction of the search space is definitely needed!
        for op in self.arith_ops_imm:
            for dest in self.all_regs:
                for arg in self.all_regs + self.arg_regs:
                    possibilities += [[Instr(op, dest, arg, c2)] + x for x in copy if x[0].args[1] == dest]
        for op in self.arith_ops:
            for dest in self.all_regs:
                for arg1 in self.all_regs + self.arg_regs:
                    for arg2 in self.all_regs + self.arg_regs:
                        possibilities += [[Instr(op, dest, arg1, arg2)] + x for x in copy if x[0].args[1] == dest]

        return possibilities

    # smart meaning: only try valid code. also don't generate duplicates
    def smart_sketches(self, depth: int):
        possibilities = []
        c = Int('c' + str(depth))
        self.consts += [c]
        avail_regs = ([Reg.const_regs[i] for i in range((depth) + 1)] if depth <= len(Reg.const_regs) else Reg.const_regs) + \
            [Zero(), ReturnReg()] + self.arg_regs

        option = []




if __name__ == "__main__":
    gen = RiscvGen(['x', 'y'])  # NOTE: order of arguments always has to be the same in the lists
    r = gen.naive_gen([([1, 2], 0), ([6, 6], 1)])
    print(repr(r))