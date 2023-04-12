from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from adsv.tm2cl.automata.automata import Symbol, Automata
from adsv.tm2cl.automata.parser import parse_ltl_formula
import itertools


class AutomataNode(Formula):
    def __init__(self, automata: Automata, symbol_formula_map: Mapping[Symbol, Formula], origin_formula: Formula):
        self._automata = automata
        self._symbol_formula_map = symbol_formula_map
        self._origin_formula = origin_formula

    @property
    def automata(self):
        return self._automata

    @property
    def origin_formula(self) -> Formula:
        return self._origin_formula

    @property
    def symbol_formula_map(self) -> Mapping[Symbol, Formula]:
        return self._symbol_formula_map

    @property
    def symbols(self) -> FrozenSet[Symbol]:
        return self.automata.symbols

    def formula(self, symbol: Symbol) -> Formula:
        return self._symbol_formula_map[symbol]

    @property
    def sub_nodes(self) -> Tuple['AstNode']:
        return tuple()

    def apply_sub_nodes(self) -> 'AutomataNode':
        return AutomataNode(self._automata, self._symbol_formula_map, self.origin_formula)

    def __str__(self):
        return str(self.origin_formula)

    def __repr__(self):
        return f'AutomataNode({self.origin_formula})'


def is_temporal_node(node: AstNode):
    if isinstance(node, TemporalNode):
        return True
    return False


def contains_temporal_node(node: AstNode):
    if is_temporal_node(node):
        return True
    for sub_node in node.sub_nodes:
        if contains_temporal_node(sub_node):
            return True
    return False


def handle_binary_operator(formula: Formula, counter):
    left_serial, left_map = temporal_formula_serialize(formula.left_formula, counter)
    right_serial, right_map = temporal_formula_serialize(formula.right_formula, counter)
    formula_map = dict()
    formula_map.update(left_map)
    formula_map.update(right_map)
    return left_serial, right_serial, formula_map


def temporal_formula_serialize(formula: Formula, counter: itertools.count) -> Tuple[str, Mapping[Symbol, Formula]]:
    if not contains_temporal_node(formula):
        new_symbol = Symbol(f'p{next(counter)}')
        return new_symbol.name, {new_symbol: formula}
    elif isinstance(formula, Always):
        sub_serial, sub_map = temporal_formula_serialize(formula.sub_formula, counter)
        return f'[] ({sub_serial})', sub_map
    elif isinstance(formula, Eventual):
        sub_serial, sub_map = temporal_formula_serialize(formula.sub_formula, counter)
        return f'<> ({sub_serial})', sub_map
    elif isinstance(formula, Until):
        left_serial, right_serial, formula_map = handle_binary_operator(formula, counter)
        return f'({left_serial} U {right_serial})',  formula_map
    elif isinstance(formula, Next):
        sub_serial, sub_map = temporal_formula_serialize(formula.sub_formula, counter)
        return f'X ({sub_serial})', sub_map
    elif isinstance(formula, Implies):
        left_serial, right_serial, formula_map = handle_binary_operator(formula, counter)
        return f'({left_serial} -> {right_serial})', formula_map
    elif isinstance(formula, And):
        left_serial, right_serial, formula_map = handle_binary_operator(formula, counter)
        return f'({left_serial} && {right_serial})', formula_map
    elif isinstance(formula, Or):
        left_serial, right_serial, formula_map = handle_binary_operator(formula, counter)
        return f'({left_serial} || {right_serial})', formula_map
    elif isinstance(formula, Not):
        sub_serial, sub_map = temporal_formula_serialize(formula.sub_formula, counter)
        return f'(! {sub_serial})', sub_map
    else:
        raise ValueError(f'Formula type {type(formula)} is not supported')


def generate_automata_node(formula: TemporalNode):
    counter = itertools.count()
    formula_serial, symbol_formula_map = temporal_formula_serialize(formula, counter)
    automata = parse_ltl_formula(formula_serial)
    node = AutomataNode(automata, symbol_formula_map, formula)
    return node


def convert_to_automata(formula: AstNode):
    if is_temporal_node(formula):
        return generate_automata_node(formula)
    sub_nodes = [sn for sn in formula.sub_nodes]
    for i in range(len(sub_nodes)):
        sub_nodes[i] = convert_to_automata(sub_nodes[i])
    formula = formula.apply_sub_nodes(*sub_nodes)
    return formula
