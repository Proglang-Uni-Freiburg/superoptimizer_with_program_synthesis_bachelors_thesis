from riscv_ast import *
import sys

def full_program(l: List[Instr], args: dict[Regvar, int]) -> List[Instr]:
    r = []
    for reg, v in args.items():
        r += [Regassign(reg, v)]
    r += l
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


if __name__ == "__main__":
    ex = [Instr("srai", Reg(31), Regvar(2, 'x'), 2), Instr('add', ReturnReg(), Zero(), Reg(31))]
    ast_to_output(ex)
    ast_to_output(ex, {Regvar(2, 'x'): 3}, "out.s")

