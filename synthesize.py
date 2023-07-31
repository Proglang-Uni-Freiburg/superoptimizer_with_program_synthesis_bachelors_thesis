from z3 import *
from riscv_ast import *

# input: list of riscv instructions


class Synthesizer:
    # goal_func: function
    # args: list  # list of function arguments

    def __init__(self, f, args):
        self.goal_func = f
        self.args = args
    
    def verify(self, guess: list[Instr]):
        s = Solver()
        z3args = {}
        to_var = lambda x: z3args[repr(x)]
        
        for arg in self.args:
            z3args[arg] = Int(arg)
            # s.add(z3args[arg] < 256)
            # s.add(z3args[arg] > -256)

        z3args["a0"] = Int("a0")
        Zero = Int("Zero")
        s.add(Zero == 0)
            
        for instr in guess:
            match instr:
                case Instr("add", (dest, reg1, reg2)):
                    s.add(to_var(dest) == to_var(reg1) + to_var(reg2))
                case Instr("addi", (dest, reg, imm)):
                    s.add(to_var(dest) == to_var(reg) + imm)
                case _:
                    raise Exception("Not a valid RISC-V instruction")

        if s.check() == sat:
            print("success!")
            print(s.model())
        else:
            print("nope :(")


if __name__ == "__main__":
    synth = Synthesizer(lambda x1: x1 + 1, ['x1'])
    synth.verify([Instr("addi", Var(0), Reg(1), 1)])