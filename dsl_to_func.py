from riscv_dsl import *


def match_instr(self, instrlist: List[Instr], goaldest: Reg):
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
