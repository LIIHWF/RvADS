from .common import Expression, AtomicProposition, AstNode, StaticValue
from adsv.utils.types import *
from enum import Enum, auto
from abc import abstractmethod


class ArithmeticOperator(Enum):
    EQ = auto()
    NEQ = auto()
    LT = auto()
    LE = auto()
    GT = auto()
    GE = auto()


class ArithmeticExpression(Expression):
    ...


class ArithmeticConstant(StaticValue, ArithmeticExpression):
    def __init__(self, value: Number):
        self._init_static_value(value)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'ArithmeticConstant':
        return ArithmeticConstant(self.value)

    def __str__(self):
        return f'{self.value}'


class ArithmeticConstraint(AtomicProposition):
    def __init__(self, left_exp: ArithmeticExpression, operator: 'ArithmeticOperator',
                 right_exp: 'ArithmeticExpression'):
        self.left_exp = left_exp
        self.operator = operator
        self.right_exp = right_exp

    @property
    def sub_nodes(self) -> Iterable['ArithmeticExpression']:
        return self.left_exp, self.right_exp

    def apply_sub_nodes(self, left_exp: 'ArithmeticExpression',
                        right_exp: 'ArithmeticExpression') -> 'ArithmeticConstraint':
        return ArithmeticConstraint(left_exp, self.operator, right_exp)

    def __str__(self):
        if self.operator == ArithmeticOperator.EQ:
            op_str = '='
        elif self.operator == ArithmeticOperator.NEQ:
            op_str = '≠'
        elif self.operator == ArithmeticOperator.GE:
            op_str = '≥'
        elif self.operator == ArithmeticOperator.GT:
            op_str = '>'
        elif self.operator == ArithmeticOperator.LE:
            op_str = '≤'
        elif self.operator == ArithmeticOperator.LT:
            op_str = '<'
        else:
            op_str = '?'
        return f'[{str(self.left_exp)} {op_str} {self.right_exp}]'

    def __repr__(self):
        return f'ArithmeticConstraint({self.left_exp}, {self.operator.name}, {self.right_exp})'
