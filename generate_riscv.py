from z3 import *
from riscv_ast import *
from run_riscv import *
from typing import Tuple
import itertools


class RiscvGen():
    c_min = -10
    c_max = 10
    max_depth = 10
    consts = []
    all_regs = [Reg(x) for x in Reg.const_regs] + [Zero(), ReturnReg()]
    arith_ops_imm: List[str] = ["addi", "subi"]
    arith_ops: List[str] = ["add", "sub", "mul", "div", "rem"]  # prefer easier operations, first
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

        raise Exception("No posssible program was found!")
    
    def smart_gen(self, examples: List[Tuple[List[int], int]], min_prog_length: int) -> Tuple[List[Instr], int]:
        i = Int('i')
        count = 0
        possibilities = self.smart_sketches(min_prog_length)
        for p in possibilities:
            self.s.push()
            for (inputs, output) in examples:  # note that there needs to always be at least one example
                success = True
                # match p:
                #     case [Instr("sub", [_, Regvar(), Regvar()]), Instr("addi", [_, _, _])]:
                #         pass
                try:
                    r = run_riscv(p, {self.args[i]: inputs[i] for i in range(len(self.args))}, self.s)
                    self.s.add(r == output)
                except Exception as ex:  # this means the code was invalid. skip to the next one
                    success = False
                    count += 1
                    break
            if not success:
                self.s.pop()
                continue
            if self.s.check() == sat:
                print("Number of invalid programs checked:", count)
                return self.replace_consts(p), min_prog_length
            self.s.pop()

        if min_prog_length < 10:
            return self.smart_gen(examples, min_prog_length + 1)
        raise Exception("No posssible program was found!")

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
        # NOTE: if the if-clauses in the list comprehensions are removed, the list length goes from 57.288 to 627.528 (add/addi/sub/subi only)
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

    # NOTE: avoid calling this from the start each time, i.e. only generate starting once and then just add onto it if nothing fitting is found
    # smart meaning: only try valid code. also don't generate duplicates
    def smart_sketches(self, depth: int) -> Iterable:
        possibilities = []
        for i in range(depth + 1):
            c = Int('c' + str(i))
            self.consts += [c]
        avail_regs = self.arg_regs
        possibilities = self.helper(depth, 0, 0, [], avail_regs)
        
        return possibilities

    def helper(self, iter: int, reg_iter: int, const_iter: int, temp_r: List[Instr], avail_regs: List[Reg]):
        if iter == 0:
            possibilities = []
            for op in self.arith_ops_imm:
                possibilities += [temp_r + [Instr(op, ReturnReg(), arg, self.consts[const_iter])] for arg in avail_regs]
            for op in self.arith_ops:
                possibilities += [temp_r + [Instr(op, ReturnReg(), arg1, arg2)] for arg1, arg2 in list(itertools.product(avail_regs, avail_regs))]
            for p in possibilities:
                yield p
                return

        new_regs = avail_regs.copy()
        new_r = temp_r.copy()
        if reg_iter < len(Reg.const_regs):
            new_regs.append(Reg(Reg.const_regs[reg_iter]))
        diff = [x for x in new_regs if x not in avail_regs]

        for op in self.arith_ops_imm:
            for dest in new_regs:
                for arg in avail_regs + [Zero()]:
                    last_instr = "invalid" if len(new_r) == 0 else new_r[-1].instr
                    # eliminate redundant programs: consecutive addition/subtraction of constants on same dest is unnecessary
                    if (op in ["addi", "subi"]) and len(new_r) > 0 and last_instr in ["addi", "subi"] and bool(new_r[-1].args[0] == dest):
                        continue
                    new_r += [Instr(op, dest, arg, self.consts[const_iter])]
                    if dest in diff:
                        yield from self.helper(iter - 1, reg_iter + 1, const_iter + 1, new_r, new_regs)
                    else:
                        yield from self.helper(iter - 1, reg_iter, const_iter + 1, new_r, avail_regs)
                    new_r.pop()

        for op in self.arith_ops:
            for dest in new_regs:
                for arg1 in avail_regs + [Zero()]:
                    for arg2 in avail_regs + [Zero()]:
                        # eliminate redundant programs here
                        if (op == "mul" or op == "add") and repr(arg1) > repr(arg2):
                            continue

                        new_r += [Instr(op, dest, arg1, arg2)]
                        if dest in diff:
                            yield from self.helper(iter - 1, reg_iter + 1, const_iter, new_r, new_regs)
                        else:
                            yield from self.helper(iter - 1, reg_iter, const_iter, new_r, avail_regs)
                        new_r.pop()

    # same as smart sketches, but with dynamic programming to reduce duplication
    def dynamic_sketches(self):
        pass


if __name__ == "__main__":
    gen = RiscvGen(['x', 'y'])  # NOTE: order of arguments always has to be the same in the lists
    r = gen.naive_gen([([3, 2], 0), ([6, 1], 1)])
    print(repr(r))

    print("Number of possible program sketches with length 3:", len(list(gen.smart_sketches(2))))  # 1.5mil possibilties...

    r = gen.smart_gen([([3, 2], 0), ([6, 1], 1)], 0)
    print(repr(r))