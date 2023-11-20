from z3 import *
from riscv_dsl import *
from synthesis import *
from typing import Callable, List
from python_ast_to_func import user_to_func
from dsl_to_func import to_func
from memory_profiler import profile
from python_ast_to_dsl import Compiler
import ast as ast


class Verifier:
    goal_func: Callable[..., int]
    args: List[str]  # list of function arguments
    to_analyze: List[str]
    z3args: dict[str, BitVecRef]

    def __init__(self, f: Callable[..., int], args: List[str]):
        self.goal_func = f
        self.args = args
        self.z3args = {repr(Zero()): BitVec("Zero", 64)}
        self.to_analyze = [repr(ReturnReg())] + [repr(Reg(x)) for x in [5, 6, 7, 28, 29, 30, 31]]
        # hack to force usage of remainder instead of python modulo in Z3
        BitVecRef.__mod__ = lambda self, other: SRem(self, other)
        BitVecRef.__rmod__ = lambda self, other: SRem(self, other)

    @classmethod
    def fromStr(cls, s: str) -> "Verifier":
        f, args = user_to_func(s)
        return cls(f, args)
    
    @classmethod
    def fromRiscv(cls, instrs: List[Instr]) -> "Verifier":
        f, args = to_func(instrs)
        return cls(f, args)


    # we cannot easily convert a list of instructions directly to z3 because registers may have different values at different points in the program
    # instead we traverse the instruction list bottom-up, resolving registers to values when possible.
    # a expression is returned
    def match_instr(self, instrlist: List[Instr], goaldest: Reg, s):
        to_var = lambda x: self.z3args[py_name(x)]  # helper

        for instr in instrlist:
            match instr:
                case Instr(op, (dest, Reg() as arg, int(imm))) if repr(dest) == repr(goaldest):
                    left = self.match_instr(instrlist[1:], arg, s)
                    if left is None:
                        left = to_var(arg)
                    return match_op(op)(left, imm)

                case Instr(op, (dest, Reg() as arg1, Reg() as arg2)) if repr(dest) == repr(goaldest):
                    left = self.match_instr(instrlist[1:], arg1, s)
                    if left is None:
                        left = to_var(arg1)

                    right = self.match_instr(instrlist[1:], arg2, s)
                    if right is None:
                        right = to_var(arg2)
                    if op == 'div' or op == 'rem':
                        s.add(right != 0)
                    return match_op(op)(left, right)

                case Instr(_):
                    return self.match_instr(instrlist[1:], goaldest, s)

                case _:
                    raise Exception("Not a valid RISC-V instruction")

    # verifies if guess matches goal function or not. Prints result
    def verify(self, guess: list[Instr]):
        s = Solver()

        for arg in self.args:
            self.z3args[arg] = BitVec(arg, 64)
            # s.add(self.z3args[arg] < 256)
            # s.add(self.z3args[arg] > -256)

        s.add(self.z3args[repr(Zero())] == 0)

        guess.reverse()

        try:
            unrolled_expr = self.match_instr(guess, ReturnReg(), s)
            s.add(unrolled_expr == self.goal_func(*[self.z3args[x] for x in self.args]))
        except Exception as e:
            print("Tried to verify a program that was not valid")
            return False

        if s.check() == sat:
            print("Instrction sequence matches goal function")
            print(s.model())
            return True
        else:
            print("Instruction sequence did not match goal function")
            return False

    def avoid_overflow(self, s, expr):
        if expr.num_args() < 2:
            return
        if expr.decl().name() == 'if':
            expr = expr.arg(0).arg(0).arg(0)  # if -> and -> (< 0) -> extracted = x * y
        x = expr.arg(0)
        y = expr.arg(1)
        self.avoid_overflow(s, x)
        self.avoid_overflow(s, y)
        match expr.decl().name():
            case 'bvadd':
                s.add(And(BVAddNoOverflow(x, y, True), BVAddNoUnderflow(x, y)))
            case 'bvsub':
                s.add(And(BVSubNoOverflow(x, y), BVSubNoUnderflow(x, y, True)))
            case 'bvmul':
                s.add(And(BVMulNoOverflow(x, y, True), BVMulNoUnderflow(x, y)))
            case 'bvshl':
                s.add(Implies(And(x > 0, y > 0), (x << y) > 0))
                s.add(Implies(And(x < 0, y < 0), (x << y) < 0))


    def _avoid_zero_div(self, s, expr):
        if type(expr) is int or expr.num_args() < 2:
            return
        if expr.decl().name() == 'bvsdiv' or expr.decl().name() == 'bvsrem':
            s.add(expr.arg(1) != 0)
            return
        for i in range(expr.num_args()):
            self._avoid_zero_div(s, expr.arg(i))



    # provides a counter example if the guess wasn't correct, or just returns true if the guess matched the specification
    def cegis_counter(self, guess:list[Instr], s: Solver) -> Tuple[List[Instr], bool]:

        guess.reverse()

        unrolled_expr = self.match_instr(guess, ReturnReg(), s)
        goal_f_result = self.goal_func(*[self.z3args[x] for x in self.args])
        self._avoid_zero_div(s, goal_f_result)
        s.add(unrolled_expr != goal_f_result)

        if s.check() == sat:
            del self.z3args[repr(Zero())]
            new_args = [int(s.model().eval(x).as_signed_long()) for x in self.z3args.values()]
            self.z3args[repr(Zero())] = BitVec("Zero", 64)
            return new_args, False
        else:
            guess.reverse()
            return [], True

    def cegis_general(self, generator_used: Callable):
        s = Solver()

        s.add(self.z3args[repr(Zero())] == 0)

        for arg in self.args:
            self.z3args[arg] = BitVec(arg, 64)
            s.add(self.z3args[arg] < 256)
            s.add(self.z3args[arg] >= -256)

        example_args = [0 for x in self.args]
        min_len = 0
        try:
            examples = [(example_args, self.goal_func(*example_args))]
        except:
            example_args = [1 for x in self.args]
            examples = [(example_args, self.goal_func(*example_args))]

        while(True):
            if generator_used.__func__ == RiscvGen.naive_gen:
                guess = generator_used(examples)
            else:
                guess, min_len = generator_used(examples, min_len)

            example_args, success = self.cegis_counter(guess, s)
            if success:
                return guess
            examples += [(example_args, self.goal_func(*example_args))]


    # uses naive generator for guesses
    def cegis_0(self):
        gen = RiscvGen(self.args)
        return self.cegis_general(gen.naive_gen)

    # uses generator with pruned search space
    def cegis_1(self):
        gen = RiscvGen(self.args)
        return self.cegis_general(gen.smart_gen)

    # uses generator and dynamic programming
    def cegis_2(self):
        gen = RiscvGen(self.args)
        return self.cegis_general(gen.dp_gen)

    # does not use cegis but just bottom up enumeration
    def bottom_up(self):
        gen = RiscvGen(self.args)
        s = Solver()

        max_depth = 5
        sym_args = {}

        s.add(self.z3args[repr(Zero())] == 0)
        for arg in self.args:
            sym_args[arg] = BitVec(arg, 64)
            self.z3args[arg] = sym_args[arg]
            s.add(self.z3args[arg] < 256)
            s.add(self.z3args[arg] >= -256)

        for i in range(max_depth):
            if len(self.args) == 2:
                x = self.goal_func(2, 3)
            for candidate in gen.dp_sketches_yield(i):
                s = gen.s
                s.push()
                cand_res = run_riscv(candidate, sym_args, s)
                func_res = self.goal_func(*[self.z3args[x] for x in self.args])
                self._avoid_zero_div(s, func_res)
                forall_args = [val for key, val in self.z3args.items() if key != repr(Zero())]
                if forall_args != []:
                    s.add(ForAll(forall_args, cand_res == func_res))
                else:
                    s.add(cand_res == func_res)
                if s.check() == sat:
                    new_cand = gen.replace_consts(candidate)
                    return new_cand
                s.pop()
                gen.s = s



if __name__ == "__main__":
    synth = Verifier(lambda x1: x1 + 1, ['x1'])
    synth.verify([Instr("addi", ReturnReg(), Regvar(2, 'x1'), 1)])
    synth.verify([Instr("addi", Reg(31), Zero(), 1), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))])
    print("======================\n")
    print("x1 + 1")
    print("x1 = a2\n")  # TODO automate this
    print("\n".join(repr(x) for x in synth.cegis_1()))
    
    print("\n(x1 - x1) + (x2 - 3) * 2 - x2")

    synth2 = Verifier(lambda x1, x2: (x1 - x1) + (x2 - 3) * 2 - x2, ['x1', 'x2'])
    print("\n".join(repr(x) for x in synth2.cegis_2()))

    print("\n(x + 2) * 4")
    # testing with using direct riscv input
    c = Compiler()
    synth3 = Verifier.fromRiscv(c.compile_input('(x + 2) * 4'))
    print("\n".join(repr(x) for x in synth3.cegis_2()))

    # testing overflow check
    x = BitVec('x', 64)
    s = Solver()
    s.add(x + 2 >> 2 != (x + 2) / 4)
    synth.avoid_overflow(s, (x + 2) >> 4)
    synth.avoid_overflow(s, (x + 2) / 4)
    s.check()

    
    # testing bottom up
    print("\n ~~~~~~~~~~~~~\n")
    synth4 = Verifier.fromRiscv(instrs=c.compile_input('(x % 2) '))
    print("\n".join(repr(x) for x in synth4.bottom_up()))