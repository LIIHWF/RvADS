from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from adsv.semantic_model.metric_graph import RoadId, JunctionId, EdgeId, NodeId, Road
from functools import singledispatch
from adsv.semantic_model.common.map_common import TurnType
from adsv.semantic_model.scenario import Scene, VehicleState, Scenario
from .common import contains_variable
from .tautology_elimination import tautology_elimination
from .arithmetic_calculation import arithmetic_calculation
from .convert_to_automata import AutomataNode #, NumbaAutomataNode
from adsv.tm2cl.automata.automata import AutomataResult, TranslateCondition
# from adsv.tm2cl.automata.numba_automata import RESULT_ACCEPT, RESULT_REJECT, RESULT_INCONCLUSIVE
from .add_multi_operator import MultiOr, MultiAnd, MultiNot, MultiImplies
from .scenario_evaluation import handle_formula, is_determined, scenario_evaluation


class Core:
    def __init__(self, result: bool, sub_formulas: Tuple[Formula, ...]):
        self._result = result
        self._sub_formulas = sub_formulas

    @property
    def result(self) -> bool:
        return self.result

    @property
    def sub_formulas(self) -> Tuple[Formula, ...]:
        return self._sub_formulas


def get_atomic_formula_map(formula: Formula) -> Mapping[str, AtomicProposition]:
    if isinstance(formula, AtomicProposition):
        return {str(formula): formula}
    ret_set = dict()
    for sub_node in formula.sub_nodes:
        if isinstance(sub_node, Formula):
            ret_set.update(get_atomic_formula_map(sub_node))
    return ret_set


def record_true_set(scenario: Scenario, formula: Formula) -> List[FrozenSet[str]]:
    result = []
    atomic_formula_map = get_atomic_formula_map(formula)
    for i in range(scenario.ticks_num):
        cur_result = set()
        for na, af in atomic_formula_map.items():
            if scenario_evaluation(af, scenario, i) is TrueValue:
                cur_result.add(na)
        result.append(frozenset(cur_result))
    return result


class RecordEvaluator:
    def __init__(self, scenario: Scenario, formula: Formula):
        self.scenario = scenario
        self.formula = formula
        self.record = record_true_set(scenario, formula)

    def evaluate(self, simplified_formula: Formula) -> Tuple[AstNode, Optional[Core]]:
        return self._evaluate(simplified_formula, 0)

    @singledispatchmethod
    def _evaluate(self, formula: AstNode, i_: int) -> Tuple[AstNode, Optional[Core]]:
        sub_nodes = [sub_node for sub_node in formula.sub_nodes]
        current_formula = handle_formula(formula)
        i = 0
        while not is_determined(current_formula):
            if is_determined(sub_nodes[i]):
                i += 1
            else:
                sub_nodes[i] = handle_formula(self._evaluate(sub_nodes[i], i_))
                current_formula = handle_formula(formula.apply_sub_nodes(*sub_nodes))
        return current_formula

    @_evaluate.register
    def _evaluate_atomic(self, formula: AtomicProposition, i_: int):
        if str(formula) in self.record[i_]:
            return TrueValue
        else:
            return FalseValue

    @_evaluate.register
    def _evaluate_multiand(self, formula: MultiAnd, i_: int):
        unsat_formulas = []
        is_top_level = False
        for sub_formula in formula.sub_nodes:
            if not is_top_level and isinstance(sub_formula, AutomataNode):
                is_top_level = True
            if self._evaluate(sub_formula, i_) is FalseValue:
                if is_top_level:
                    unsat_formulas.append(sub_formula)
                else:
                    return FalseValue
        if is_top_level:
            if len(unsat_formulas) > 0:
                return FalseValue, Core(False, tuple(unsat_formulas))
            else:
                return TrueValue, None
        else:
            return TrueValue

    @_evaluate.register
    def _evaluate_multior(self, formula: MultiOr, i_: int):
        sat_formulas = []
        is_top_level = False
        for sub_formula in formula.sub_nodes:
            if not is_top_level and isinstance(sub_formula, AutomataNode):
                is_top_level = True
            if self._evaluate(sub_formula, i_) is TrueValue:
                if is_top_level:
                    sat_formulas.append(sub_formula)
                else:
                    return TrueValue
        if is_top_level:
            if len(sat_formulas) > 0:
                return TrueValue, Core(True, tuple(sat_formulas))
            else:
                return FalseValue, None
        else:
            return FalseValue

    @_evaluate.register
    def _evaluate_multiimplies(self, formula: MultiImplies, i_: int):
        for sub_formula in formula.sub_nodes[:-1]:
            if self._evaluate(sub_formula, i_) is FalseValue:
                return TrueValue
        if self._evaluate(formula.sub_nodes[-1], i_) is FalseValue:
            return FalseValue
        return TrueValue

    @_evaluate.register
    def _evaluate_multinot(self, formula: MultiNot, i_: int):
        if self._evaluate(formula.sub_formula, i_) is FalseValue:
            return TrueValue
        else:
            return FalseValue

    @_evaluate.register
    def _evaluate_automata(self, formula: AutomataNode, i_: int):
        def scenario_iterator():
            for i in range(i_, self.scenario.ticks_num):
                positive_symbols = set()
                for symbol in formula.symbols:
                    sub_formula = formula.formula(symbol)
                    evaluation = self._evaluate(sub_formula, i)
                    if evaluation is TrueValue:
                        positive_symbols.add(symbol)
                    elif evaluation is not FalseValue:
                        raise NotImplementedError
                yield positive_symbols

        result = formula.automata.check_finite_sequence(scenario_iterator())
        if result == AutomataResult.ACCEPT:
            return TrueValue
        else:
            return FalseValue

    @_evaluate.register
    def _evaluate_always(self, formula: Always, i_: int):
        result_formula = TrueValue
        for i in range(i_, self.scenario.ticks_num):
            cur_tick_formula = handle_formula(self._evaluate(formula.sub_formula, i))
            if cur_tick_formula == FalseValue:
                return FalseValue
            if cur_tick_formula == TrueValue:
                pass
            else:
                raise NotImplemented  # TODO
        return result_formula

    @_evaluate.register
    def _evaluate_until(self, formula: Until, i_: int):
        for i in range(i_, self.scenario.ticks_num):
            cur_tick_right_result = handle_formula(self._evaluate(formula.right_formula, i))
            if cur_tick_right_result == TrueValue:
                return TrueValue
            if cur_tick_right_result == FalseValue:
                pass
            else:
                raise ValueError(f'cur_tick_right_result: {repr(cur_tick_right_result)}')  # TODO

            cur_tick_left_result = handle_formula(self._evaluate(formula.left_formula, i))
            if cur_tick_left_result == FalseValue:
                return FalseValue
            if cur_tick_left_result == TrueValue:
                pass
            else:
                raise NotImplemented  # TODO
        return FalseValue

    @_evaluate.register
    def _evaluate_eventual(self, formula: Eventual, i_: int):
        result_formula = FalseValue
        for i in range(i_, self.scenario.ticks_num):
            cur_tick_formula = handle_formula(self._evaluate(formula.sub_formula, i))
            if cur_tick_formula == TrueValue:
                return TrueValue
            if cur_tick_formula == FalseValue:
                pass
            else:
                raise NotImplemented
        return result_formula

    @_evaluate.register
    def _evaluate_next(self, formula: Next, i_: int):
        if i_ + 1 >= self.scenario.ticks_num:
            return FalseValue
        return self._evaluate(formula.sub_formula, i_ + 1)
