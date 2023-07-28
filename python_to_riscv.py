from ast import *
from riscv_ast import *
from typing import List


class Compiler:
    avail_reg = [Reg(x) for x in [5, 6, 7, 28, 29, 30, 31]]
    result: List[str] = [".global _start", "", "_start:"]

    def __init__(self):
        return
    
    def compile(self, e):
        last_reg = self.transform_expr(e)  # final result, equals exit code of program
        self.result += ["addi a7, zero, 93", f"addi a0, {last_reg}, 0", "ecall"]  # add exit to program at the end
        return "\n".join(self.result)

    def transform_const(self, val) -> Reg:
        if len(self.avail_reg) > 1:
            reg = self.avail_reg.pop()
            self.result.append(repr(Assign(reg, val)))
            return reg
        else:
            raise Exception("ran out of temporary registers!")  # TODO: free up operations in this case?

    def transform_expr(self, e):
        match e:
            case BinOp(left, Add(), right):
                reg1 = self.transform_expr(left)  # problem: expr of type (1 + (2 + (3 + (4 + ...))))
                reg2 = self.transform_expr(right)
                self.result.append(repr(Instr("add", reg1, reg1, reg2)))
                self.avail_reg.append(reg2)
                return reg1
            case BinOp(left, Sub(), right):
                reg1 = self.transform_expr(left)
                reg2 = self.transform_expr(right)
                self.result.append(repr(Instr("sub", reg1, reg1, reg2)))
                self.avail_reg.append(reg2)
                return reg1
            case UnaryOp(USub(), rest):
                reg = self.transform_expr(rest)
                self.result.append(repr(Instr("Sub", reg, Zero(), reg)))
                return reg
            case Constant(val):
                return self.transform_const(val)
            case _:
                raise Exception("could not parse " + repr(e))