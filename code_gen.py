from ast import *
from python_to_riscv import *


if __name__ == "__main__":
    in_expr = input("Please enter an arithmetic expression: ")
    in_expr_tree = parse(in_expr, mode='eval')
    c = Compiler()
    match in_expr_tree:
        case Expression(body=to_analyse):
            print(c.compile(to_analyse))
