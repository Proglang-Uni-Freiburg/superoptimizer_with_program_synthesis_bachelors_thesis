from ast import *
from python_ast_to_dsl import *
from python_ast_to_func import *
from run_riscv import *
from cegis_verify import *
from synthesis import *



def input_to_naive_riscv():
    in_expr = input("Please enter an arithmetic expression: ")
    in_expr_tree = parse(in_expr, mode='eval')
    in_func, in_args = expr_to_func(in_expr_tree)  # convert input to python lambda with variables as args
    example_dict = {in_args[x]: (x + 1) for x in range(len(in_args))}  # for testing purposes
    c = Compiler()
    match in_expr_tree:
        case Expression(body=to_analyse):
            res = c.compile(to_analyse)
            print('\n'.join([repr(i) for i in res]))
            print("output with all arguments set to 1, 2, ... , n:", run_riscv(res, example_dict))




if __name__ == "__main__":
    print("Available functions:")
    choice = int(input("User Input to Naive RISC-V (1) \n" \
                       "User Input to Synthesized RISC-V (2)\n"))
    if choice == 1:
        input_to_naive_riscv()
    else:
        print("Invalid choice")