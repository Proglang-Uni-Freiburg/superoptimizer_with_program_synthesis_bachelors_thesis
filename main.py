from ast import *
from python_ast_to_dsl import *
from python_ast_to_func import *
from run_riscv import *
from cegis_verify import *
from synthesis import *
from dsl_input_output import *
from dsl_to_func import to_func


def input_to_naive_riscv():
    choice_for_input_type = input("Do you wish to enter an arithmetic expression (1) or use a RISC-V assembly file as input (2)? ")
    if int(choice_for_input_type) == 2:
        in_file = input("Please enter the name of the input file: ")
        in_func, in_args = to_func(input_to_ast(in_file))
    else:
        in_expr = input("Please enter an arithmetic expression: ")
        in_expr_tree = parse(in_expr, mode='eval')
        in_func, in_args = expr_to_func(in_expr_tree)  # convert input to python lambda with variables as args
    example_dict = {in_args[x]: (x + 1) for x in range(len(in_args))}  # for testing purposes
    print("\n======================================\n")
    c = Compiler()
    res = c.compile_input(in_expr)
    ast_to_output(res, f_name="out.s")
    ast_to_output(res)
    print("\n======================================\n")
    print("output with all arguments set to 1, 2, ... , n:", run_riscv(res, example_dict))


def input_to_synthesized_riscv():
    choice_for_input_type = input("Do you wish to enter an arithmetic expression (1) or use a RISC-V assembly file as input (2)? ")
    if int(choice_for_input_type) == 2:
        in_file = input("Please enter the name of the input file: ")
        in_func, in_args = to_func(input_to_ast(in_file))
        synth = Verifier.fromRiscv(input_to_ast(in_file))
    else:
        in_expr = input("Please enter an arithmetic expression: ")
        in_expr_tree = parse(in_expr, mode='eval')
        in_func, in_args = expr_to_func(in_expr_tree)  # convert input to python lambda with variables as args
        synth = Verifier.fromStr(in_expr)
    example_dict = {in_args[x]: (x + 1) for x in range(len(in_args))}  # for testing purposes
    print("\n======================================\n")
    res = synth.cegis_2()
    ast_to_output(res, f_name="out.s")
    print(res, "\n")
    ast_to_output(res)
    print("\n======================================\n")
    print("output with all arguments set to 1, 2, ... , n:", run_riscv(res, example_dict))

def output_example_riscv_file():
    print("RISC-V Assembly code for the function x + x + 3")
    print("\n======================================\n")
    print("1: .global _start\n2:\n"\
"3: _start: \n" \
"4: addi x5, a1, 3\n" \
"5: add a0, a1, x5\n" \
"6: addi a7, x0, 93\n" \
"7: ecall")
    print("\n======================================\n")
    print("Lines 4 and 5 compute the actual result. The output is stored in the return register a0, afterwards exit is called.")


def output_help_text():
    print("This is a tool for synthesizing RISC-V assembly code from an arithmetic expression.\n" \
    "Supported operators are +, -, <<, >>, *, /, %. You may use variables of any name.\n" \
    "In Option (1) or (2) you will be prompted to either input a supported arithmetic expression directly,\n" \
    "or enter the name of a RISC-V assembly file that describes a supported arithmetic expression.\n" \
    "A solution will be computed and shown in the terminal and saved in out.s.\n"\
    "Using make run in the terminal you may run the out.s.\n"\
    "Option (1) uses a naive compilation method, while Option (2) uses synthesis with the CEGIS method.\n" \
    "To see an example of a valid RISC-V input or output file, you can select Option (4).")


if __name__ == "__main__":
    print("Available functions:")
    choice = int(input("User Input to Naive RISC-V (1)\n" \
                       "User Input to Synthesized RISC-V (2)\n" \
                        "Output help text (3)\n" \
                        "Output example RISC-V assembly file (4)\n"))
    print("\n======================================\n")
    match choice:
        case 1:
            input_to_naive_riscv()
        case 2:
            input_to_synthesized_riscv()
        case 3:
            output_help_text()
        case 4:
            output_example_riscv_file()
        case _:
            print("Invalid choice. Please enter one of the option numbers.")