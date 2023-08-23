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
        last = self._transform_expr(e)  # final result, equals exit code of program
        self.result += [Instr("addi", ReturnReg(), last, 0)]
        return self.result

    def _transform_const(self, val: int) -> Reg:
        if len(self.avail_const) > 1:
            reg = self.avail_const.pop()
            self.result.append(Regassign(reg, val))
            return reg
        else:
            raise Exception("ran out of temporary registers!")  # TODO: free up operations in this case?

    def _transform_var(self, val: str) -> Reg:
        if val in self.used_var.keys():
            return self.used_var[val]
        if len(self.avail_var) > 1:
            free_num = self.avail_var.pop()
            self.used_var[val] = Regvar(free_num, val)
            return self.used_var[val]
        else:
            raise Exception("ran out of argument registers!")

    def _check_free(self, reg: Reg):  # frees reg for reuse if it was a constant
        if type(reg) == Regvar:
            return
        self.avail_const.append(reg)

    def _transform_expr(self, e: AST) -> Reg:
        match e:
            case BinOp(left, Add(), right):
                reg1 = self._transform_expr(left)  # problem: expr of type (1 + (2 + (3 + (4 + ...))))
                reg2 = self._transform_expr(right)
                self.result.append((Instr("add", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, Sub(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("sub", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, Mult(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("mul", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, Div(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("div", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, Mod(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("rem", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, LShift(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("sll", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case BinOp(left, RShift(), right):
                reg1 = self._transform_expr(left)
                reg2 = self._transform_expr(right)
                self.result.append((Instr("sra", self.temp_res, reg1, reg2)))
                self._check_free(reg2)
                return self.temp_res
            case UnaryOp(USub(), rest):
                reg = self._transform_expr(rest)
                self.result.append((Instr("Sub", reg, Zero(), reg)))
                return reg
            case Name(id=val):
                return self._transform_var(val)
            case Constant(val):
                return self._transform_const(val)
            case _:
                raise Exception("could not parse " + dump(e))