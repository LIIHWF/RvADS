from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from functools import singledispatch
from adsv.semantic_model.scenario import Scenario
from adsv.semantic_model.static_scene import SignalType


def is_determined(formula: Formula) -> bool:
    return formula is TrueValue or formula is FalseValue


@singledispatch
def tautology_elimination(formula: AstNode):
    sub_nodes = tuple(tautology_elimination(sub_node) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)


@tautology_elimination.register(ObjectEqual)
def tautology_elimination_object_equal(formula: ObjectEqual):
    object1 = tautology_elimination(formula.object1)
    object2 = tautology_elimination(formula.object2)
    if type(object1) == type(object2):
        if isinstance(object1, StaticVariable):
            return TrueValue if object1.id == object2.id else FalseValue
        elif isinstance(object1, Variable) and object1.name == object2.name:
            return TrueValue
    return ObjectEqual(object1, object2)


@tautology_elimination.register(And)
def tautology_elimination_and(formula: And):
    left_formula = tautology_elimination(formula.left_formula)
    right_formula = tautology_elimination(formula.right_formula)
    if left_formula is TrueValue and right_formula is TrueValue:
        return TrueValue
    elif left_formula is FalseValue or right_formula is FalseValue:
        return FalseValue
    elif left_formula is TrueValue:
        return right_formula
    elif right_formula is TrueValue:
        return left_formula
    else:
        return And(left_formula, right_formula)


@tautology_elimination.register(Or)
def tautology_elimination_or(formula: Or):
    left_formula = tautology_elimination(formula.left_formula)
    right_formula = tautology_elimination(formula.right_formula)
    if left_formula is TrueValue or right_formula is TrueValue:
        return TrueValue
    elif left_formula is FalseValue:
        return right_formula
    elif right_formula is FalseValue:
        return left_formula
    else:
        return Or(left_formula, right_formula)


@tautology_elimination.register(Implies)
def tautology_elimination_implies(formula: Or):
    left_formula = tautology_elimination(formula.left_formula)
    right_formula = tautology_elimination(formula.right_formula)
    if left_formula is FalseValue or right_formula is TrueValue:
        return TrueValue
    elif left_formula is TrueValue:
        return right_formula
    elif right_formula is FalseValue:
        return Not(left_formula)
    else:
        return Implies(left_formula, right_formula)


@tautology_elimination.register(Not)
def tautology_elimination_not(formula: Not):
    sub_formula = tautology_elimination(formula.sub_formula)
    if sub_formula is TrueValue:
        return FalseValue
    elif sub_formula is FalseValue:
        return TrueValue
    else:
        return Not(sub_formula)


@tautology_elimination.register(Always)
def tautology_elimination_always(formula: Always):
    sub_formula = tautology_elimination(formula.sub_formula)
    if sub_formula is TrueValue:
        return TrueValue
    elif sub_formula is FalseValue:
        return FalseValue
    else:
        return Always(sub_formula)


@tautology_elimination.register(Eventual)
def tautology_elimination_eventual(formula: Eventual):
    sub_formula = tautology_elimination(formula.sub_formula)
    if sub_formula is TrueValue:
        return TrueValue
    elif sub_formula is FalseValue:
        return FalseValue
    else:
        return Eventual(sub_formula)


@tautology_elimination.register(Next)
def tautology_elimination_next(formula: Eventual):
    sub_formula = tautology_elimination(formula.sub_formula)
    if sub_formula is TrueValue:
        return TrueValue
    elif sub_formula is FalseValue:
        return FalseValue
    else:
        return Next(sub_formula)


@tautology_elimination.register(Until)
def tautology_elimination_until(formula: Until):
    left_formula = tautology_elimination(formula.left_formula)
    right_formula = tautology_elimination(formula.right_formula)
    if right_formula is FalseValue:
        return FalseValue
    return Until(left_formula, right_formula)
