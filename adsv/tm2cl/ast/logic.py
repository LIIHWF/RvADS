from adsv.utils.types import *
from .common import Formula


class LogicNode(Formula):
    ...


class And(LogicNode):
    def __init__(self, left_formula: Formula, right_formula: Formula):
        self.left_formula = left_formula
        self.right_formula = right_formula

    @property
    def sub_nodes(self) -> Tuple[Formula, Formula]:
        return self.left_formula, self.right_formula

    def apply_sub_nodes(self, left_formula: Formula, right_formula: Formula) -> 'And':
        return And(left_formula, right_formula)

    def and_nodes(self) -> Tuple['Formula', ...]:
        if isinstance(self.left_formula, And):
            left_nodes = self.left_formula.and_nodes()
        else:
            left_nodes = self.left_formula,
        if isinstance(self.right_formula, And):
            right_nodes = self.right_formula.and_nodes()
        else:
            right_nodes = self.right_formula,
        return left_nodes + right_nodes

    def __str__(self):
        return f'[{" ∧ ".join(str(n) for n in self.and_nodes())}]'

    def __repr__(self):
        return f'And{self.and_nodes()}'


class Or(LogicNode):
    def __init__(self, left_formula: Formula, right_formula: Formula):
        self.left_formula = left_formula
        self.right_formula = right_formula

    @property
    def sub_nodes(self) -> Tuple[Formula, Formula]:
        return self.left_formula, self.right_formula

    def apply_sub_nodes(self, left_formula: Formula, right_formula: Formula) -> 'Or':
        return Or(left_formula, right_formula)

    def or_nodes(self) -> Tuple['Formula', ...]:
        if isinstance(self.left_formula, Or):
            left_nodes = self.left_formula.or_nodes()
        else:
            left_nodes = self.left_formula,
        if isinstance(self.right_formula, Or):
            right_nodes = self.right_formula.or_nodes()
        else:
            right_nodes = self.right_formula,
        return left_nodes + right_nodes

    def __str__(self):
        return f'[{" ∨ ".join(str(n) for n in self.or_nodes())}]'

    def __repr__(self):
        return f'Or{self.or_nodes()}'


class Not(LogicNode):
    def __init__(self, sub_formula: Formula):
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple[Formula]:
        return self.sub_formula,

    def apply_sub_nodes(self, sub_formula: Formula) -> 'Not':
        return Not(sub_formula)

    def __str__(self):
        return f'¬{str(self.sub_formula)}'

    def __repr__(self):
        return f'Not({self.sub_formula})'

    def reduced(self) -> 'Formula':
        if isinstance(self.sub_formula, Not):
            reduced_sub_formula = self.sub_formula.reduced()
            if isinstance(reduced_sub_formula, Not):
                return reduced_sub_formula.sub_formula
            else:
                return Not(reduced_sub_formula)
        else:
            return Not(self.sub_formula)


class Implies(LogicNode):
    def __init__(self, left_formula: Formula, right_formula: Formula):
        self.left_formula = left_formula
        self.right_formula = right_formula

    @property
    def sub_nodes(self) -> Tuple[Formula, Formula]:
        return self.left_formula, self.right_formula

    def apply_sub_nodes(self, left_formula: Formula, right_formula: Formula) -> 'Implies':
        return Implies(left_formula, right_formula)

    def __repr__(self):
        return f'Implies{self.implies_nodes()}'

    def __str__(self):
        return f'[{" → ".join(str(n) for n in self.implies_nodes())}]'

    def implies_nodes(self) -> Tuple['Formula', ...]:
        if isinstance(self.left_formula, Implies):
            left_nodes = self.left_formula.implies_nodes()
        else:
            left_nodes = self.left_formula,
        if isinstance(self.right_formula, Implies):
            right_nodes = self.right_formula.implies_nodes()
        else:
            right_nodes = self.right_formula,
        return left_nodes + right_nodes
