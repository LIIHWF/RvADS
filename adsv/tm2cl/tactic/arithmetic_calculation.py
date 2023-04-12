from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from functools import singledispatch
from adsv.semantic_model.scenario import Scenario
from adsv.semantic_model.static_scene import SignalType


@singledispatch
def arithmetic_calculation(formula: AstNode) -> AstNode:
    sub_nodes = tuple(arithmetic_calculation(sub_node) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)


@arithmetic_calculation.register(ArithmeticConstraint)
def arithmetic_calculation_ac(formula: ArithmeticConstraint):
    left_exp = arithmetic_calculation(formula.left_exp)
    right_exp = arithmetic_calculation(formula.right_exp)

    if not isinstance(left_exp, ArithmeticConstant) or not isinstance(right_exp, ArithmeticConstant):
        return ArithmeticConstraint(left_exp, formula.operator, right_exp)

    if formula.operator == ArithmeticOperator.EQ:
        return TrueValue if left_exp.value == right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.NEQ:
        return TrueValue if left_exp.value != right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.LT:
        return TrueValue if left_exp.value < right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.LE:
        return TrueValue if left_exp.value <= right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.GT:
        return TrueValue if left_exp.value > right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.GE:
        return TrueValue if left_exp.value >= right_exp.value else FalseValue
    else:
        return ArithmeticConstraint(left_exp, formula.operator, right_exp)
