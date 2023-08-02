from ast import *
from typing import Callable, Tuple, List


def expr_to_func(ast_in: Expression) -> Tuple[Callable[[List[int]], int], list[str]]:
    expr_vars = []
    expr_body = Constant(value=0)
    for node in walk(ast_in):
        match node:
            case Name(id, _) if id not in expr_vars:
                expr_vars.append(id)
            case Expression(body=b):  # for putting into lambda body later
                expr_body = b
            case _:
                continue

    expr_vars.sort()
    func = Expression(body=Lambda(args=arguments(posonlyargs=[],
                                                 args=[arg(arg=id) for id in expr_vars],
                                                 kwonlyargs=[],
                                                 kw_defaults=[],
                                                 defaults=[]),
                                  body=expr_body))
    return eval(unparse(func)), expr_vars
