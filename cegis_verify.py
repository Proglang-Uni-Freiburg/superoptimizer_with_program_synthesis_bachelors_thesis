from z3 import *
from riscv_dsl import *
from synthesis import *
from typing import Callable, List
from dsl_to_func import to_func
from python_ast_to_dsl import Compiler


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

        # floordiv is not implemented for z3 arguments. Regular div converts to ints automatically, though
        BitVecRef.__floordiv__ = lambda self, other: BitVecRef.__div__(self, other)

    # we cannot easily convert a list of instructions directly to z3 because registers may have different values at different points in the program
    # instead we traverse the instruction list bottom-up, resolving registers to values when possible.
    # a expression is returned
    # TODO: This needs to be rewritten! It does not currently work correctly.
    # instead do this: don't go bottom up. Just save results.
    def match_instr(self, instrlist: List[Instr], goaldest: Reg):
        to_var = lambda x: self.z3args[py_name(x)]  # helper

        for instr in instrlist:
            match instr:
                case Instr(op, (dest, Reg() as arg, int(imm))) if repr(dest) == repr(goaldest):
                    left = self.match_instr(instrlist[1:], arg)
                    if left is None:
                        left = to_var(arg)
                    return match_op(op)(left, imm)

                case Instr(op, (dest, Reg() as arg1, Reg() as arg2)) if repr(dest) == repr(goaldest):
                    left = self.match_instr(instrlist[1:], arg1)
                    if left is None:
                        left = to_var(arg1)

                    right = self.match_instr(instrlist[1:], arg2)
                    if right is None:
                        right = to_var(arg2)
                    return match_op(op)(left, right)

                case Instr(_):
                    return self.match_instr(instrlist[1:], goaldest)

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
            unrolled_expr = self.match_instr(guess, ReturnReg())
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

    # provides a counter example if the guess wasn't correct, or just returns true if the guess matched the specification
    def cegis_counter(self, guess:list[Instr]) -> Tuple[List[Instr], bool]:
        s = Solver()

        s.add(self.z3args[repr(Zero())] == 0)

        for arg in self.args:
            self.z3args[arg] = BitVec(arg, 64)
            s.add(self.z3args[arg] < 256)
            s.add(self.z3args[arg] > -256)

        guess.reverse()

        unrolled_expr = self.match_instr(guess, ReturnReg())
        s.add(unrolled_expr != self.goal_func(*[self.z3args[x] for x in self.args]))

        if s.check() == sat:
            del self.z3args[repr(Zero())]
            new_args = [int(s.model().eval(x).as_signed_long()) for x in self.z3args.values()]
            self.z3args[repr(Zero())] = BitVec("Zero", 64)
            return new_args, False
        else:
            guess.reverse()
            print("Found Solution!")
            return [], True

    # uses naive generator for guesses
    def cegis_0(self):
        gen = RiscvGen(self.args)
        example_args = [0 for x in self.args]
        examples = [(example_args, self.goal_func(*example_args))]
        while(True):
            guess = gen.naive_gen(examples)
            # print(guess)
            example_args, success = self.cegis_counter(guess)
            if success:
                return guess
            examples += [(example_args, self.goal_func(*example_args))]

    # uses generator with pruned search space
    def cegis_1(self):
        gen = RiscvGen(self.args)
        example_args = [0 for x in self.args]
        min_len = 0
        examples = [(example_args, self.goal_func(*example_args))]
        while(True):
            guess, min_len = gen.smart_gen(examples, min_len)
            # print(guess)
            example_args, success = self.cegis_counter(guess)
            if success:
                return guess
            examples += [(example_args, self.goal_func(*example_args))]

    def cegis_2(self):
        gen = RiscvGen(self.args)
        example_args = [0 for x in self.args]
        min_len = 0
        examples = [(example_args, self.goal_func(*example_args))]
        while(True):
            guess, min_len = gen.dp_gen(examples, min_len)
            print(guess)
            example_args, success = self.cegis_counter(guess)
            if success:
                return guess
            examples += [(example_args, self.goal_func(*example_args))]


class DirectCegis(Verifier):
    starting_impl: List[Instr]
    def __init__(self, instrs: List[Instr]):
        self.starting_impl = instrs
        f, args = to_func(instrs)
        super().__init__(f, args)

    def cegis_3(self):
        gen = RiscvGen(self.args)
        example_args = [0 for x in self.args]
        min_len = 0
        examples = [(example_args, self.goal_func(*example_args))]




if __name__ == "__main__":
    synth = Verifier(lambda x1: x1 + 1, ['x1'])
    synth.verify([Instr("addi", ReturnReg(), Regvar(2, 'x1'), 1)])
    synth.verify([Instr("addi", Reg(31), Zero(), 1), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))])
    print(synth.cegis_counter([Instr("addi", Reg(31), Zero(), 2), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))]))
    print("======================")
    print("x1 + 1")
    print("x1 = a2\n")  # TODO automate this
    print("\n".join(repr(x) for x in synth.cegis_1()))
    
    print("\n(x1 - x1) + (x2 - 3) * 2 - x2")

    synth2 = Verifier(lambda x1, x2: (x1 - x1) + (x2 - 3) * 2 - x2, ['x1', 'x2'])
    print("\n".join(repr(x) for x in synth2.cegis_2()))

    # testing with using direct riscv input
    c = Compiler()
    synth3 = DirectCegis(c.compile_input('(x + 2) / 4'))
    print("\n".join(repr(x) for x in synth3.cegis_2()))
