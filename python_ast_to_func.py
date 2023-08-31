from ast import *
from typing import Callable, Tuple, List


class TransformDiv(NodeTransformer):

    def visit_BinOp(self, node):
        match node:
            case BinOp(left=leftval, op=Div() | FloorDiv(), right=rightval):
                replacement = Call(func=Name(id='pydiv', ctx=Load()), args=[leftval, rightval], keywords=[])
                return replacement
            case BinOp(left=leftval, op=opval, right=rightval):
                new_left = self.visit(leftval)
                new_right = self.visit(rightval)
                return BinOp(left=new_left, op=opval, right=new_right)
        return node


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


if __name__ == "__main__":
    ast_in = parse("x / 2 + 1", mode='eval')
    print(dump(fix_missing_locations(TransformDiv().visit(ast_in))))
