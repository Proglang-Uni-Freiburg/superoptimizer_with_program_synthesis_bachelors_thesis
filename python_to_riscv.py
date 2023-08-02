from ast import *
from riscv_ast import *
from typing import List


class Compiler:
    temp_res: Reg = ReturnReg()
    avail_const: List[Reg] = [Reg(x) for x in [5, 6, 7, 28, 29, 30, 31]]
    avail_var: List[int] = list(range(7, 1, -1))
    used_var: dict[str, Reg] = {}
    result: List[Instr] = prog_start

    def __init__(self):
        return

    def compile(self, e: AST):
        self.transform_expr(e)  # final result, equals exit code of program
        self.result += prog_end
        return self.result

    def transform_const(self, val: int) -> Reg:
        if len(self.avail_const) > 1:
            reg = self.avail_const.pop()
            self.result.append(Regassign(reg, val))
            return reg
        else:
            raise Exception("ran out of temporary registers!")  # TODO: free up operations in this case?

    def transform_var(self, val: str) -> Reg:
        if val in self.used_var.keys():
            return self.used_var[val]
        if len(self.avail_var) > 1:
            free_num = self.avail_var.pop()
            self.used_var[val] = Regvar(free_num, val)
            return self.used_var[val]
        else:
            raise Exception("ran out of argument registers!")

    def check_free(self, reg: Reg):  # frees reg for reuse if it was a constant
        if type(reg) == Regvar:
            return
        self.avail_const.append(reg)

    def transform_expr(self, e: AST):
        match e:
            case BinOp(left, Add(), right):
                reg1 = self.transform_expr(left)  # problem: expr of type (1 + (2 + (3 + (4 + ...))))
                reg2 = self.transform_expr(right)
                self.result.append((Instr("add", self.temp_res, reg1, reg2)))
                self.check_free(reg2)
                return self.temp_res
            case BinOp(left, Sub(), right):
                reg1 = self.transform_expr(left)
                reg2 = self.transform_expr(right)
                self.result.append((Instr("sub", self.temp_res, reg1, reg2)))
                self.check_free(reg2)
                return self.temp_res
            case BinOp(left, Mult(), right):
                reg1 = self.transform_expr(left)
                reg2 = self.transform_expr(right)
                self.result.append((Instr("mul", self.temp_res, reg1, reg2)))
                self.check_free(reg2)
                return self.temp_res
            case BinOp(left, Div(), right):
                reg1 = self.transform_expr(left)
                reg2 = self.transform_expr(right)
                self.result.append((Instr("div", self.temp_res, reg1, reg2)))
                self.check_free(reg2)
                return self.temp_res
            case UnaryOp(USub(), rest):
                reg = self.transform_expr(rest)
                self.result.append((Instr("Sub", reg, Zero(), reg)))
                return reg
            case Name(id=val):
                return self.transform_var(val)
            case Constant(val):
                return self.transform_const(val)
            case _:
                raise Exception("could not parse " + dump(e))