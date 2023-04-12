from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from .convert_to_automata import AutomataNode


class MultiAnd(Formula):
    def __init__(self, *sub_nodes: 'Formula'):
        self._sub_nodes = sub_nodes

    @property
    def sub_nodes(self) -> Tuple['Formula']:
        return self._sub_nodes

    def apply_sub_nodes(self, *sub_nodes: 'AstNode') -> 'MultiAnd':
        return MultiAnd(*sub_nodes)

    def __str__(self):
        return f'MultiAnd{self.sub_nodes}'

    def __repr__(self):
        return f'MultiAnd{self.sub_nodes}'


class MultiOr(Formula):
    def __init__(self, *sub_nodes: 'Formula'):
        self._sub_nodes = sub_nodes

    @property
    def sub_nodes(self) -> Tuple['Formula']:
        return self._sub_nodes

    def apply_sub_nodes(self, *sub_nodes: 'AstNode') -> 'MultiOr':
        return MultiOr(*sub_nodes)

    def __str__(self):
        return f'MultiOr{self.sub_nodes}'

    def __repr__(self):
        return f'MultiOr{self.sub_nodes}'

class MultiNot(Formula):
    def __init__(self, sub_formula: 'Formula'):
        self.sub_formula = sub_formula

    @property
    def sub_nodes(self) -> Tuple['Formula']:
        return self.sub_formula,

    def apply_sub_nodes(self, sub_formula: 'Formula') -> 'MultiNot':
        return MultiNot(sub_formula)

    def __str__(self):
        return f'MultiNot{self.sub_nodes}'

    def __repr__(self):
        return f'MultiNot{self.sub_nodes}'

class MultiImplies(Formula):
    def __init__(self, *sub_nodes: 'Formula'):
        self._sub_nodes = sub_nodes

    @property
    def sub_nodes(self) -> Tuple['Formula']:
        return self._sub_nodes

    def apply_sub_nodes(self, *sub_nodes: 'AstNode') -> 'MultiImplies':
        return MultiImplies(*sub_nodes)

    def __str__(self):
        return f'MultiImplies{self.sub_nodes}'

    def __repr__(self):
        return f'MultiImplies{self.sub_nodes}'


def add_multi_operator(formula: AstNode):
    if isinstance(formula, And):
        return MultiAnd(*[add_multi_operator(sn) for sn in formula.and_nodes()])
    elif isinstance(formula, Or):
        return MultiOr(*[add_multi_operator(sn) for sn in formula.or_nodes()])
    elif isinstance(formula, Implies):
        return MultiImplies(*[add_multi_operator(sn) for sn in formula.implies_nodes()])
    elif isinstance(formula, Not):
        reduced_formula = formula.reduced()
        if isinstance(reduced_formula, Not):
            return MultiNot(reduced_formula.sub_formula)
        else:
            return reduced_formula
    elif isinstance(formula, AutomataNode):
        automata_node = formula.apply_sub_nodes()
        for sym, sub_formula in automata_node.symbol_formula_map.items():
            automata_node.symbol_formula_map[sym] = add_multi_operator(sub_formula)
        return automata_node
    else:
        sub_nodes = tuple(add_multi_operator(sn) for sn in formula.sub_nodes)
        return formula.apply_sub_nodes(*sub_nodes)
