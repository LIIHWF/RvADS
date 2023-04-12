from adsv.utils.types import *
from .common import Formula, Variable


class QuantifierNode(Formula):
    ...


class Exist(QuantifierNode):
    def __init__(self, variable: Variable, sub_formula: Formula):
        self.variable = variable
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple[Variable, Formula]:
        return self.variable, self.sub_formula

    def apply_sub_nodes(self, variable: Variable, sub_formula: Formula) -> 'Exist':
        return Exist(variable, sub_formula)

    def __repr__(self):
        return f'Exist({self.variable}, {self.sub_formula})'


class Forall(QuantifierNode):
    def __init__(self, variable: Variable, sub_formula: Formula):
        self.variable = variable
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple[Variable, Formula]:
        return self.variable, self.sub_formula

    def apply_sub_nodes(self, variable: Variable, sub_formula: Formula) -> 'Forall':
        return Forall(variable, sub_formula)

    def __repr__(self):
        return f'Forall({self.variable}, {self.sub_formula})'
