from z3 import *
from riscv_ast import *
from typing import Callable, List

# TODO: cleanup!


class Synthesizer:
    goal_func: Callable[..., int]
    args: List[str]  # list of function arguments
    to_analyze: List[str] = [repr(ReturnReg())] + [repr(Reg(x)) for x in [5, 6, 7, 28, 29, 30, 31]]
    z3args: dict[str, ArithRef] = {}

    def __init__(self, f: Callable[..., int], args: List[str]):
        self.goal_func = f
        self.args = args

    # ALERT THIS HAS BAD RUNTIME FOR SURE
    def match_instr(self, instrlist: List[Instr], goaldest: Reg):
        # idea: go bottom up, use new variables for results. auflösen, sozusagen! inverse of python to riscv really.
        # constants, zero and arguments stay unchanged. go thru temps, result reg
        # perhaps change rule about arguments later on, as of now don't generate anything that overwrites arguments
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

    def verify(self, guess: list[Instr]):
        s = Solver()

        for arg in self.args:
            self.z3args[arg] = Int(arg)
            # s.add(self.z3args[arg] < 256)
            # s.add(self.z3args[arg] > -256)

        self.z3args[repr(Zero())] = Int("Zero")
        s.add(self.z3args[repr(Zero())] == 0)

        guess.reverse()

        unrolled_expr = self.match_instr(guess, ReturnReg())
        s.add(unrolled_expr == self.goal_func(*[self.z3args[x] for x in self.args]))

        if s.check() == sat:
            print("success!")
            print(s.model())
        else:
            print("nope :(")


if __name__ == "__main__":
    synth = Synthesizer(lambda x1: x1 + 1, ['x1'])
    synth.verify([Instr("addi", ReturnReg(), Regvar(2, 'x1'), 1)])
    synth.verify([Instr("addi", Reg(31), Zero(), 1), Instr("add", ReturnReg(), Reg(31), Regvar(2, 'x1'))])