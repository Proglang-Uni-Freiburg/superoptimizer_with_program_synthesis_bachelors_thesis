from ast import *
from python_to_riscv import *
from ast_to_func import *


if __name__ == "__main__":
    in_expr = input("Please enter an arithmetic expression: ")
    in_expr_tree = parse(in_expr, mode='eval')
    in_func, in_args = expr_to_func(in_expr_tree)  # convert input to python lambda with variables as args
    example_dict = {in_args[x]: (x + 1) for x in range(len(in_args))}  # for testing purposes
    c = Compiler()
    match in_expr_tree:
        case Expression(body=to_analyse):
            res = c.compile(to_analyse)
            print('\n'.join([repr(i) for i in res]))
