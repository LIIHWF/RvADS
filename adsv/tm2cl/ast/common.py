from adsv.utils.types import *
from abc import abstractmethod


class AstNode:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    @property
    def sub_nodes(self) -> Tuple['AstNode']:
        raise NotImplementedError

    def apply_sub_nodes(self, *sub_nodes: 'AstNode') -> 'AstNode':
        raise NotImplementedError

    # def __repr__(self):
    #     return str(self)


class Expression(AstNode):
    ...


class Variable(Expression):
    def _init_variable(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def char(self):
        return self.name


class StaticVariable(Expression):
    def _init_static_variable(self, id_: str):
        self._id = id_

    @property
    def id(self):
        return self._id

    @property
    def char(self):
        return self.id


class StaticValue(Expression):
    def _init_static_value(self, value):
        self.value = value


class Formula(AstNode):
    ...


class ConstFormula(Formula):
    @property
    def neg(self):
        raise NotImplementedError


class TrueValueClass(ConstFormula):
    def __init__(self):
        pass

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'AstNode':
        return TrueValue

    def __invert__(self):
        return FalseValue

    def __and__(self, other: ConstFormula):
        return other

    def __or__(self, other: ConstFormula):
        return TrueValue

    def __eq__(self, other):
        return other is TrueValue

    def __repr__(self):
        return 'TrueValue'


class FalseValueClass(ConstFormula):
    def __init__(self):
        pass

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'AstNode':
        return FalseValue

    def __invert__(self):
        return TrueValue

    def __and__(self, other):
        return FalseValue

    def __or__(self, other):
        return other

    def __eq__(self, other):
        return other is FalseValue

    def __repr__(self):
        return 'FalseValue'

TrueValue = TrueValueClass()
FalseValue = FalseValueClass()


class M2clFormula(Formula):
    ...


class AtomicProposition(M2clFormula):
    ...


class Tm2clFormula(Formula):
    ...
