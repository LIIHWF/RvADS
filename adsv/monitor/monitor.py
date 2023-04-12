from adsv.semantic_model.static_scene import StaticScene
from adsv.semantic_model.scenario import Scenario, DynamicScenario, VehicleState, TrafficLightState, TrafficLightColor, PhysicalState, Vector3
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration, VehicleConfiguration, Itinerary
from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from adsv.tm2cl.tactic import *
from .property import Property


class Result:
    def __init__(self, premise: bool, formula: bool, premise_core: Optional[Core], formula_core: Optional[Core]):
        self._premise = premise
        self._formula = formula
        self._premise_core = premise_core
        self._formula_core = formula_core

    @property
    def premise(self) -> bool:
        return self._premise

    @property
    def formula(self) -> bool:
        return self._formula

    @property
    def specification(self) -> bool:
        return None if self.premise is False else self.formula

    @property
    def premise_core(self) -> Optional[Tuple[Formula, ...]]:
        return self._premise_core.sub_formulas if self._premise is not None else None

    @property
    def formula_core(self) -> Optional[Tuple[Formula, ...]]:
        return self._formula_core.sub_formulas if self._formula is not None else None


def _value(node_value: AstNode) -> bool:
    if node_value is TrueValue:
        return True
    elif node_value is FalseValue:
        return False
    else:
        raise ValueError('input is not TrueValue or FalseValue')


class Monitor:
    def __init__(self, specification: Property, static_scene: StaticScene, vehicle_ids: Set[str], traffic_light_ids: Set[str]=None):
        self._specification = specification
        self._static_scene = static_scene
        self._vehicle_ids = vehicle_ids
        self._traffic_light_ids = frozenset() if traffic_light_ids is None else frozenset(traffic_light_ids)
        self._premise_monitor = self._build_premise_monitor()
        self._formula_monitor = self._build_formula_monitor()

    @cached_property
    def sample_scenario(self) -> Scenario:
        sample_scenario = Scenario(ScenarioConfiguration(
            '', 0, {vid: VehicleConfiguration(Itinerary(0, 0, []), 0) for vid in self._vehicle_ids},
            [], set(), False, 0, 0
        ), self._static_scene, DynamicScenario({vid: [
            VehicleState('', 0, 0, 0, 0, 0, 0, 0, 0, False, False, 0, 0, 0, 0, PhysicalState(Vector3(0,0,0), Vector3(0,0,0)))] for vid in self._vehicle_ids},
            {tid: [TrafficLightState(TrafficLightColor.GREEN)] for tid in self._traffic_light_ids}))
        return sample_scenario

    def _build_premise_monitor(self):
        self._premise_expanded_formula = expansion(self.specification.bounded_premise, self.sample_scenario)
        self._premise_evaluated_formula = static_scene_evaluation(self._premise_expanded_formula, self.sample_scenario.static_scene)
        self._premise_simplified_formula = tautology_elimination(self._premise_evaluated_formula)
        self._premise_automata_formula = convert_to_automata(self._premise_simplified_formula)
        self._premise_multi_operator_formula = add_multi_operator(self._premise_automata_formula)
        def monitor(scenario):
            return RecordEvaluator(scenario, self._premise_simplified_formula).evaluate(self._premise_multi_operator_formula)
        return monitor

    def _build_formula_monitor(self):
        self._formula_expanded_formula = expansion(self.specification.bounded_formula, self.sample_scenario)
        self._formula_evaluated_formula = static_scene_evaluation(self._formula_expanded_formula, self.sample_scenario.static_scene)
        self._formula_simplified_formula = tautology_elimination(self._formula_evaluated_formula)
        self._formula_automata_formula = convert_to_automata(self._formula_simplified_formula)
        self._formula_multi_operator_formula = add_multi_operator(self._formula_automata_formula)
        def monitor(scenario):
            return RecordEvaluator(scenario, self._formula_simplified_formula).evaluate(self._formula_multi_operator_formula)
        return monitor

    @property
    def specification(self) -> Property:
        return self._specification

    def check(self, scenario: Scenario) -> Result:
        formula_core = None
        premise_ret, premise_core = self._premise_monitor(scenario)
        if premise_ret is FalseValue:
            formula_ret = TrueValue
        else:
            formula_ret, formula_core = self._formula_monitor(scenario)
        return Result(_value(premise_ret), _value(formula_ret), premise_core, formula_core)
