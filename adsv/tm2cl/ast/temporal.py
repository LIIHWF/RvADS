from adsv.utils.types import *
from .common import Formula, Tm2clFormula


class TemporalNode(Tm2clFormula):
    ...


class Always(TemporalNode):
    def __init__(self, sub_formula: Formula):
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple[Formula]:
        return self.sub_formula,

    def apply_sub_nodes(self, sub_formula: Formula) -> 'Always':
        return Always(sub_formula)

    def __str__(self):
        return f'□[{str(self.sub_formula)}]'

    def __repr__(self):
        return f'Always({self.sub_formula})'


class Until(TemporalNode):
    def __init__(self, left_formula: Formula, right_formula: Formula):
        self.left_formula = left_formula
        self.right_formula = right_formula

    @property
    def sub_nodes(self) -> Tuple[Formula, Formula]:
        return self.left_formula, self.right_formula

    def apply_sub_nodes(self, left_formula: Formula, right_formula: Formula) -> 'Until':
        return Until(left_formula, right_formula)

    def __str__(self):
        return f'[{str(self.left_formula)} U {str(self.right_formula)}]'

    def __repr__(self):
        return f'Until({self.left_formula}, {self.right_formula})'


class Eventual(TemporalNode):
    def __init__(self, sub_formula: Formula):
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple[Formula]:
        return self.sub_formula,

    def apply_sub_nodes(self, sub_formula: Formula) -> 'Eventual':
        return Eventual(sub_formula)

    def __str__(self):
        return f'♢[{str(self.sub_formula)}]'

    def __repr__(self):
        return f'Eventual({self.sub_formula})'


class Next(TemporalNode):
    def __init__(self, sub_formula: Formula):
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple['Formula']:
        return self.sub_formula,

    def apply_sub_nodes(self, sub_formula: 'Formula') -> 'Next':
        return Next(sub_formula)

    def __str__(self):
        return f'[N {str(self.sub_formula)}]'

    def __repr__(self):
        return f'Next({self.sub_formula})'
