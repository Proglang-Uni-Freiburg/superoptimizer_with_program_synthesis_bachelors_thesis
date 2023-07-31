from z3 import *
from riscv_ast import *

# input: list of riscv instructions


class Synthesizer:
    # goal_func: function
    # args: list  # list of function arguments
    to_analyze = [ReturnReg()] + [Reg(x) for x in [5, 6, 7, 28, 29, 30, 31]]
    def __init__(self, f, args):
        self.goal_func = f
        self.args = args  # TODO this needs to be converted from function args to proper args starting with a
    
    def verify(self, guess: list[Instr]):
        s = Solver()
        z3args = {}
        to_var = lambda x: z3args[repr(x)]
        
        for arg in self.args:
            z3args[arg] = Int(arg)
            # s.add(z3args[arg] < 256)
            # s.add(z3args[arg] > -256)

        Zero = Int("Zero")
        s.add(Zero == 0)
        z3args["a0"] = Int("a0")
        s.add(z3args["a0"] == self.goal_func(*[z3args[x] for x in self.args]))

        guess.reverse()
        def match_instr(instrlist, goaldest):
            # idea: go bottom up, use new variables for results. auflösen, sozusagen! inverse of python to riscv really.
            # constants, zero and arguments stay unchanged. go thru temps, result reg
            # perhaps change rule about arguments later on, as of now don't generate anything that overwrites arguments
            for instr in instrlist:
                match instr:
                    case Instr("add" | "addi", (goaldest, arg1, arg2)):
                        if arg1 in self.to_analyze:
                            left = match_instr(guess[1:], arg1)
                        else:
                            left = to_var(arg1)
                        if arg2 in self.to_analyze:
                            right = match_instr(guess[1:],arg2)
                        else:
                            right = to_var(arg2)
                        return left + right
                    case _:
                        raise Exception("Not a valid RISC-V instruction")

        match_instr(guess, ReturnReg)
        if s.check() == sat:
            print("success!")
            print(s.model())
        else:
            print("nope :(")


if __name__ == "__main__":
    synth = Synthesizer(lambda x1: x1 + 1, ['a2'])
    synth.verify([Instr("addi", ReturnReg(), Var(2), 1)])