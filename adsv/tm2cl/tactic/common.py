from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *


@singledispatch
def contains_variable(ast_node: AstNode):
    for sub_node in ast_node.sub_nodes:
        if contains_variable(sub_node):
            return True
    return False


@contains_variable.register(Variable)
def contains_variable_v(variable: Variable):
    return True
