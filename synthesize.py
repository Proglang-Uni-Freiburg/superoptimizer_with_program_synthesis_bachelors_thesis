from z3 import *
from riscv_ast import *
from generate_riscv import *
from typing import Callable, List


class Synthesizer:
    goal_func: Callable[..., int]
    args: List[str]  # list of function arguments
    to_analyze: List[str] = [repr(ReturnReg())] + [repr(Reg(x)) for x in [5, 6, 7, 28, 29, 30, 31]]
    z3args: dict[str, BitVecRef] = {}

    def __init__(self, f: Callable[..., int], args: List[str]):
        self.goal_func = f
        self.args = args

    # we cannot easily convert a list of instructions directly to z3 because registers may have different values at different points in the program
    # instead we traverse the instruction list bottom-up, resolving registers to values when possible.
    # a expression is returned
    def match_instr(self, instrlist: List[Instr], goaldest: Reg):
        to_var = lambda x: self.z3args[py_name(x)]  # helper

        for instr in instrlist:
            match instr:
                case Instr(op, (dest, Reg() as arg, int(imm))) if repr(dest) == repr(goaldest):
                    if repr(arg) in self.to_analyze:
                        left = self.match_instr(instrlist[1:], arg)
                    else:
                        left = to_var(arg)
                    return match_op(op)(left, imm)

                case Instr(op, (dest, Reg() as arg1, Reg() as arg2)) if repr(dest) == repr(goaldest):
                    if repr(arg1) in self.to_analyze:
                        left = self.match_instr(instrlist[1:], arg1)
                    else:
                        left = to_var(arg1)

                    if repr(arg2) in self.to_analyze:
                        right = self.match_instr(instrlist[1:], arg2)
                    else:
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

        self.z3args[repr(Zero())] = BitVec("Zero", 64)
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

        self.z3args[repr(Zero())] = BitVec("Zero", 64)
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
            return [s.model().evaluate(x) for x in self.z3args.values()], False
        else:
            print("Found Solution!")
            return [], True

    # uses naive generator for guesses
    def cegis_0(self):
        gen = RiscvGen(self.args)
        example_args = [0 for x in self.args]
        examples = [(example_args, self.goal_func(*example_args))]
        while(True):
            guess = gen.naive_gen(examples)
            print(guess)
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
            print(guess)
            example_args, success = self.cegis_counter(guess)
            if success:
                return guess
            examples += [(example_args, self.goal_func(*example_args))]




if __name__ == "__main__":
    synth = Synthesizer(lambda x1: x1 + 1, ['x1'])
    synth.verify([Instr("addi", ReturnReg(), Regvar(2, 'x1'), 1)])
    synth.verify([Instr("addi", Reg(31), Zero(), 1), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))])
    print(synth.cegis_counter([Instr("addi", Reg(31), Zero(), 2), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))]))
    print("======================")
    print("x1 + 1")
    print("x1 = a2\n")  # TODO automate this
    print("\n" + "\n".join(repr(x) for x in synth.cegis_1()))

    synth2 = Synthesizer(lambda x1, x2: (x1 - x1) + (x2 - 3) * 2 - x2, ['x1', 'x2'])
    print("\n" + "\n".join(repr(x) for x in synth2.cegis_1()))