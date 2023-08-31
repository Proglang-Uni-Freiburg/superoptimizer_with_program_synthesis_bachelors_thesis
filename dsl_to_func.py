from riscv_dsl import *
from ast import *
from typing import Callable, Tuple, List

def add_return(instrs: List[Instr]) -> List[Instr]:
    last_dest = instrs[-1].args[0]
    return instrs + [Instr('addi', ReturnReg(), last_dest, 0)]

def _to_ast(operator: str, arg1: str | BinOp | Call, arg2: str | int | BinOp | Call) -> BinOp | Call:
    match arg1:
        case 'x0':
            leftval = Constant(value=0)
        case str() as s:
            leftval = Name(id=s, ctx=Load())
        case _ as x:
            leftval = x
    
    match arg2:
        case 'x0':
            rightval = Constant(value=0)
        case str() as s:
            rightval = Name(id=s, ctx=Load())
        case int(i):
            rightval = Constant(value=i)
        case _ as x:
            rightval = x
    
    match operator:
        case "add" | "addi":
            opval = Add()
        case "sub" | "subi":
            opval = Sub()
        case "mul":
            opval = Mult()
        case "div":
            return Call(func=Name(id='pydiv', ctx=Load()), args=[leftval, rightval], keywords=[])
        case "slli":
            opval = LShift()
        case "srai":
            opval = RShift()

    return BinOp(left=leftval, op=opval, right=rightval)

# converts a instruction sequence into a function. 
# variables occuring in the function are returned in the list (in order of appearance)
def to_func(instrlist: List[Instr]) -> Tuple[Callable[[List[int]], int], list[str]]:
    assigned: dict[str, BinOp | Call] = {}
    vars: list[str] = []
    instrlist = add_return(instrlist)  # added as safety and for if instrlist is only a snippet
    for instr in instrlist:
        match instr:
            case Instr(op, (dest, Reg() as arg1, int(imm))):
                if repr(arg1) in assigned.keys():
                    assigned[repr(dest)] = (_to_ast(op, assigned[repr(arg1)], imm))
                else:
                    vars += [] if py_name(arg1) in vars or arg1 == Zero() else [py_name(arg1)]
                    assigned[repr(dest)] = (_to_ast(op, py_name(arg1), imm))
                continue

            case Instr(op, (dest, Reg() as arg1, Reg() as arg2)):
                left, right = 0, 0
                if repr(arg1) not in assigned.keys():
                    vars += [] if py_name(arg1) in vars or arg1 == Zero() else [py_name(arg1)]
                    left = py_name(arg1)
                else:
                    left = assigned[repr(arg1)]
                if repr(arg2) not in assigned.keys():
                    vars += [] if py_name(arg2) in vars or arg2 == Zero() else [py_name(arg2)]
                    right = py_name(arg2)
                else:
                    right = assigned[repr(arg2)]
                assigned[repr(dest)] = _to_ast(op, left, right)
                continue

            case _:
                continue

    expr_body = assigned[repr(ReturnReg())]
    func = Expression(body=Lambda(args=arguments(posonlyargs=[],
                                                 args=[arg(arg=id) for id in vars],
                                                 kwonlyargs=[],
                                                 kw_defaults=[],
                                                 defaults=[]),
                                  body=expr_body))
    return eval(unparse(func)), vars


if __name__ == "__main__":
    func, vars = to_func([Instr('slli', Regvar(3, 'x'), Regvar(3, 'x'), 1),
                              Instr('add', ReturnReg(), Regvar(3, 'x'), Regvar(4, 'y'))])
    print(func(2, 4))

