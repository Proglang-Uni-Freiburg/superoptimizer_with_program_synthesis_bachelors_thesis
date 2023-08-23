from z3 import *
from riscv_ast import *
from run_riscv import *
from typing import Tuple
import itertools
import threading


class RiscvGen():
    c_min = -10
    c_max = 10
    max_depth = 10
    consts: List[BitVecRef]
    all_regs: List[Reg]
    arith_ops_imm: List[str] = ["addi", "subi", "slli", "srai"]
    arith_ops: List[str] = ["add", "sub", "mul", "div", "rem"]  # prefer easier operations, first
    arg_regs: List[Reg]
    cache: dict[Tuple[int, int], List[List[Instr]]]
    cache_p: dict[int, List[Tuple[Instr, bool]]]

    def __init__(self, args: List[str]):
        self.args = args
        self.arg_regs = [Regvar(i, x) for i, x in zip(ReturnReg().var_regs, args)]
        self.s = Solver()
        self.all_regs = [Reg(x) for x in Reg.const_regs] + [Zero(), ReturnReg()]
        self.consts = []
        self.cache = {}
        self.cache_p = {}


    def replace_consts(self, instrs: List[Instr]):
        result = []
        for instr in instrs:
            match instr:
                case Instr(op, [dest, arg1, BitVecRef() as c]):
                    c_eval = self.s.model().eval(c)
                    result += [Instr(op, dest, arg1, int(c_eval.as_signed_long()))]
                case i:
                    result += [i]
        return result


    # NOTE: 2-line solutions are the limit
    def naive_gen(self, examples: List[Tuple[List[int], int]]) -> List[Instr]:
        count = 0
        possibilities = self.code_sketches()
        for p in possibilities:
            self.s.push()
            for (inputs, output) in examples:  # note that there needs to always be at least one example
                success = True
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

    def code_sketches(self) -> List[List[Instr]]:
        possibilities = []
        c = BitVec('c', 64)
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
        c2 = BitVec('c2', 64)
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
    

    def smart_gen(self, examples: List[Tuple[List[int], int]], min_prog_length: int) -> Tuple[List[Instr], int]:
        count = 0
        possibilities = self.smart_sketches(min_prog_length)
        for p in possibilities:
            self.s.push()
            for (inputs, output) in examples:  # note that there needs to always be at least one example
                success = True
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


    # smart meaning: only try valid code. also don't generate duplicates
    def smart_sketches(self, depth: int) -> Iterable:
        
        def helper(iter: int, reg_iter: int, temp_r: List[Instr], avail_regs: List[Reg]):
            if iter == 0:
                possibilities = []
                for op in self.arith_ops_imm:
                    possibilities += [temp_r + [Instr(op, ReturnReg(), arg, self.consts[iter])] for arg in avail_regs]
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
                        new_r += [Instr(op, dest, arg, self.consts[iter])]
                        if dest in diff:
                            yield from helper(iter - 1, reg_iter + 1, new_r, new_regs)
                        else:
                            yield from helper(iter - 1, reg_iter, new_r, avail_regs)
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
                                yield from helper(iter - 1, reg_iter + 1, new_r, new_regs)
                            else:
                                yield from helper(iter - 1, reg_iter, new_r, avail_regs)
                            new_r.pop()

        possibilities = []
        for i in range(depth + 1):
            c = BitVec('c' + str(i), 64)
            self.consts += [c]
        avail_regs = self.arg_regs
        possibilities = helper(depth, 0, [], avail_regs)
        
        return possibilities

    # the same as smart_sketches, except with DP
    def dp_sketches(self, depth: int):

        def helper(iter: int, reg_iter: int, temp_r: List[Instr], avail_regs: List[Reg]):
            result = []
            if (iter, reg_iter) in self.cache.keys():
                return self.cache[iter, reg_iter]
            if iter == 0:
                possibilities = []
                for op in self.arith_ops_imm:
                    possibilities += [[Instr(op, ReturnReg(), arg, self.consts[iter])] for arg in avail_regs]
                for op in self.arith_ops:
                    if op in ['div', 'sub', 'rem']:
                        possibilities += [[Instr(op, ReturnReg(), arg1, arg2)] for arg1, arg2 in list(itertools.product(avail_regs, avail_regs)) if repr(arg1) != repr(arg2)]
                    else:
                        possibilities += [[Instr(op, ReturnReg(), arg1, arg2)] for arg1, arg2 in list(itertools.product(avail_regs, avail_regs))]
                return possibilities

            new_regs = avail_regs.copy()
            new_r = temp_r.copy()
            if reg_iter < len(Reg.const_regs):
                new_regs.append(Reg(Reg.const_regs[reg_iter]))
            diff = [x for x in new_regs if x not in avail_regs]

            for op in self.arith_ops_imm:
                for dest in new_regs:
                    for arg in avail_regs + [Zero()]:
                        new_instr = [Instr(op, dest, arg, self.consts[iter])]
                        new_r += new_instr
                        if dest in diff:
                            res = helper(iter - 1, reg_iter + 1, new_r, new_regs)
                            self.cache[iter - 1, reg_iter + 1] = res
                            result += [new_instr + x for x in res]
                        else:
                            res = helper(iter - 1, reg_iter, new_r, avail_regs)
                            self.cache[iter - 1, reg_iter] = res
                            result += [new_instr + x for x in res]
                        new_r.pop()

            for op in self.arith_ops:
                for dest in new_regs:
                    for arg1 in avail_regs + [Zero()]:
                        for arg2 in avail_regs + [Zero()]:
                            # eliminate redundant programs here
                            if (op == "mul" or op == "add") and repr(arg1) > repr(arg2):
                                continue
                            if (op in ['div', 'rem', 'sub']) and repr(arg1) == repr(arg2):
                                continue
                            
                            new_instr = [Instr(op, dest, arg1, arg2)]
                            new_r += new_instr
                            if dest in diff:
                                res = helper(iter - 1, reg_iter + 1, new_r, new_regs)
                                self.cache[iter - 1, reg_iter + 1] = res
                                result += [new_instr + x for x in res]
                            else:
                                res = helper(iter - 1, reg_iter, new_r, avail_regs)
                                self.cache[iter - 1, reg_iter] = res
                                result += [new_instr + x for x in res]
                            new_r.pop()
            return result

        possibilities = []
        for i in range(depth + 1):
            c = BitVec('c' + str(i), 64)
            self.consts += [c]
        avail_regs = self.arg_regs
        possibilities = helper(depth, 0, [], avail_regs)
        
        return possibilities
    
    # iterative memoization itself was not an improvement to the recursive dp version. However, this version was adapted to use utilize
    # multithreading as well as yield
    def dp_sketches_parallel(self, depth: int):

        def helper(iter: int, avail_regs: List[Reg]):

            def compute_iteration(reg_iter: int):
                if (reg_iter) in self.cache_p.keys():  # might occur if cache was already filled by a previous function call for sketch generation
                    return
                new_regs = avail_regs.copy()
                for i in range(min(reg_iter + 1, len(Reg.const_regs))):
                    new_regs.append(Reg(Reg.const_regs[i]))
                for op in self.arith_ops_imm:
                    for dest in new_regs:
                        for arg in new_regs[:-1] + [Zero()]:
                            instr = Instr(op, dest, arg, self.consts[reg_iter])
                            if dest == new_regs[-1]:
                                res = [(instr, True)]
                            else:
                                res = [(instr, False)]

                            self.cache_p[reg_iter] = self.cache_p.get((reg_iter), []) + res

                for op in self.arith_ops:
                    for dest in new_regs:
                        for arg1 in new_regs[:-1] + [Zero()]:
                            for arg2 in new_regs[:-1] + [Zero()]:
                                # eliminate redundant programs here
                                if (op == "mul" or op == "add") and repr(arg1) > repr(arg2):
                                    continue
                                if (op in ['div', 'rem', 'sub']) and repr(arg1) == repr(arg2):
                                    continue
                                instr = Instr(op, dest, arg1, arg2)
                                if dest == new_regs[-1]:
                                    res = [(instr, True)]
                                else:
                                    res = [(instr, False)]
                                self.cache_p[reg_iter] += res

            # inital setup: add all possibilities for instrs of length 1 because they don't follow the same pattern
            end_list = {}
            for reg_iter in range(0, iter + 1):
                new_regs = avail_regs.copy()
                for i in range(min(reg_iter, len(Reg.const_regs))):
                    new_regs.append(Reg(Reg.const_regs[i]))

                end_list[reg_iter] = []
                for op in self.arith_ops_imm:
                    end_list[reg_iter] += [Instr(op, ReturnReg(), arg, self.consts[0]) for arg in new_regs]
                for op in self.arith_ops:
                    if op in ['div', 'sub', 'rem']:
                        end_list[reg_iter] += [Instr(op, ReturnReg(), arg1, arg2) for arg1, arg2 in list(itertools.product(new_regs, new_regs)) if repr(arg1) != repr(arg2)]
                    else:
                        end_list[reg_iter] += [Instr(op, ReturnReg(), arg1, arg2) for arg1, arg2 in list(itertools.product(new_regs, new_regs))]

            threadlist = []
            for reg_iter in range(0, iter):
                compute_iteration(reg_iter)
                # threadlist.append(threading.Thread(target=compute_iteration, args=(reg_iter)))
                # for th in threadlist:
                #     th.start()
                # for th in threadlist:
                #     th.join()
            
            def build_res(iter: int, reg_iter: int, maxi: int, rest):
                if iter == maxi:
                    for instr in end_list[reg_iter]:
                        yield rest + [instr]
                    return
                for instr, b in self.cache_p[reg_iter]:
                    if b:
                        yield from build_res(iter + 1, reg_iter + 1, maxi, rest + [instr])
                    else:   
                        yield from build_res(iter + 1, reg_iter, maxi, rest + [instr])

            result = build_res(0, 0, iter, [])
            return result

        possibilities = []
        for i in range(depth + 1):
            c = BitVec('c' + str(i), 64)
            self.consts += [c]
        avail_regs = self.arg_regs
        possibilities = helper(depth, avail_regs)
        
        return possibilities


if __name__ == "__main__":
    gen = RiscvGen(['x', 'y'])  # NOTE: order of arguments always has to be the same in the lists
    r = gen.naive_gen([([3, 2], 0), ([6, 1], 1)])
    print(repr(r))

    # print("Number of possible program sketches with length 3:", len(list(gen.smart_sketches(2))), sep='\n')  # 1.5mil possibilties...
    # print("Number of possible program sketches with length 3:", len((gen.dp_sketches(2))), sep='\n')  # 1.5mil possibilties...
    print("Number of possible program sketches with length 3:", len(list(gen.dp_sketches_parallel(2))), sep='\n')  # 1.5mil possibilties...

    r = gen.smart_gen([([3, 2], 0), ([6, 1], 1)], 0)
    print(repr(r))