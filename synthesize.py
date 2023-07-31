from z3 import *
from riscv_ast import *

# input: list of riscv instructions

################## helpers ###################


def match_op(op):
    match op:
        case "add" | "addi":
            return lambda x, y: x + y
        case "sub" | "subi":
            return lambda x, y: x - y
        case "div" | "divi":
            return lambda x, y: x * y
        case "mul" | "muli":
            return lambda x, y: x / y
        case _:
            raise Exception("Could not match Instruction Operator")

class Synthesizer:
    # goal_func: function
    # args: list  # list of function arguments
    to_analyze = [repr(ReturnReg())] + [repr(Reg(x)) for x in [5, 6, 7, 28, 29, 30, 31]]
    

    def __init__(self, f, args):
        self.goal_func = f
        self.args = args  # TODO this needs to be converted from function args to proper args starting with a
    
    def verify(self, guess: list[Instr]):
        s = Solver()
        z3args = {}
        to_var = lambda x: z3args[repr(x)]  # helper
        
        for arg in self.args:
            z3args[arg] = Int(arg)
            # s.add(z3args[arg] < 256)
            # s.add(z3args[arg] > -256)

        z3args[repr(Zero())] = Int("Zero")
        s.add(z3args[repr(Zero())] == 0)

        guess.reverse()
        # ALERT THIS HAS BAD RUNTIME FOR SURE
        def match_instr(instrlist, goaldest):
            # idea: go bottom up, use new variables for results. auflösen, sozusagen! inverse of python to riscv really.
            # constants, zero and arguments stay unchanged. go thru temps, result reg
            # perhaps change rule about arguments later on, as of now don't generate anything that overwrites arguments
            for instr in instrlist:
                match instr:
                    case Instr(op, (dest, arg, int(imm))) if repr(dest) == repr(goaldest):
                        if repr(arg) in self.to_analyze:
                            left = match_instr(guess[1:], arg)
                        else:
                            left = to_var(arg)
                        return match_op(op)(left, imm)

                    case Instr(op, (dest, arg1, arg2)) if repr(dest) == repr(goaldest):
                        if repr(arg1) in self.to_analyze:
                            left = match_instr(guess[1:], arg1)
                        else:
                            left = to_var(arg1)

                        if repr(arg2) in self.to_analyze:
                            right = match_instr(guess[1:], arg2)
                        else:
                            right = to_var(arg2)
                        return match_op(op)(left, right)
                    
                    case Instr(_):
                        return match_instr(guess[1:], goaldest)
                    
                    case _:
                        raise Exception("Not a valid RISC-V instruction")

        unrolled_expr = match_instr(guess, ReturnReg())
        s.add(unrolled_expr == self.goal_func(*[z3args[x] for x in self.args]))

        if s.check() == sat:
            print("success!")
            print(s.model())
        else:
            print("nope :(")


if __name__ == "__main__":
    synth = Synthesizer(lambda x1: x1 + 1, ['a2'])
    synth.verify([Instr("addi", ReturnReg(), Var(2), 1)])
    synth.verify([Instr("addi", Reg(31), Zero(), 1), Instr("add", ReturnReg(), Reg(31), Var(2))])