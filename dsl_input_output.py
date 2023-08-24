from riscv_dsl import *
import sys

__all__ = ["ast_to_output", "input_to_ast"]


def full_program(instrs: List[Instr], args: dict[Regvar, int]) -> List[Instr]:
    r = []
    for reg, v in args.items():
        r += [Regassign(reg, v)]
    r += instrs
    return prog_start + r + prog_end


# prints to stdout by default. optionally takes assignments to function arguments used in program and adds them to finished code
def ast_to_output(input: List[Instr], args={}, f_name=None):
    p = full_program(input, args)
    if f_name is not None:
        f_out = open(f_name, 'w')
    else:
        f_out = open(sys.stdout.fileno(), 'w', closefd=False)

    with f_out as f:
        for line in p:
            f.write(repr(line) + '\n')


def identify_reg(s: str) -> Reg:
    if s[0] == 'a':
        if s[1] == '0':
            return ReturnReg()
        return Regvar(int(s[1:]), s[1:])
    if s[0] == 'x':
        if s[1] == '0':
            return Zero()
        return Reg(int(s[1:]))
    raise Exception("invalid instruction argument in input file")


# takes textfile with full riscv programm and converts it back to list of riscv ast instructions
def input_to_ast(f_name: str) -> List[Instr]:
    r = []
    with open(f_name, 'r') as f:
        for line in f:
            words = line.split()
            if len(words) >= 1 and words[0] in Instr.arith_ops:
                try:
                    dest = words[1][:-1]  # erase comma
                    arg1 = words[2][:-1]
                    arg2 = words[3]
                    if words[0][-1] == 'i':  # immediate op
                        r += [Instr(words[0], identify_reg(dest), identify_reg(arg1), int(arg2))]
                    else:
                        r += [Instr(words[0], identify_reg(dest), identify_reg(arg1), identify_reg(arg2))]
                
                except Exception as e:
                    raise Exception("invalid instruction in input file")
    return r[:-1]


if __name__ == "__main__":
    ex = [Instr("srai", Reg(31), Regvar(2, 'x'), 2), Instr('add', ReturnReg(), Zero(), Reg(31))]
    ast_to_output(ex)
    ast_to_output(ex, f_name="test_in.txt")
    converted_back = input_to_ast("test_in.txt")
    print(all(repr(x) == repr(y) for x, y in zip(ex, converted_back)))
    ast_to_output(ex, {Regvar(2, 'x'): 3}, "out.s")
    

