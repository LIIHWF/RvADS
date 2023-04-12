from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from functools import singledispatch
from adsv.semantic_model.scenario import Scenario
from adsv.semantic_model.static_scene import SignalType


class Context:
    def __init__(self):
        self._symbols: Dict[str, List[StaticVariable]] = dict()

    def _check_symbol_name(self, symbol_name: str):
        if symbol_name not in self._symbols:
            raise ValueError(f'Symbol {symbol_name} is not in the symbol stack')

    def add_symbol(self, symbol_name: str, value: 'StaticVariable'):
        if symbol_name not in self._symbols:
            self._symbols[symbol_name] = [value]
        else:
            self._symbols[symbol_name].append(value)

    def pop_symbol(self, symbol_name: str):
        self._check_symbol_name(symbol_name)
        self._symbols[symbol_name].pop()
        if len(self._symbols[symbol_name]) == 0:
            self._symbols.pop(symbol_name)

    def get_static_variable(self, symbol_name: str) -> 'StaticVariable':
        self._check_symbol_name(symbol_name)
        return self._symbols[symbol_name][-1]


@singledispatch
def domain(variable, model: Scenario, ctx: Context) -> Iterable[StaticVariable]:
    raise NotImplementedError(f'Unsupported variable type {type(variable)}')


@domain.register(VehicleVariable)
def domain_vehicle(variable, model: Scenario, ctx: Context):
    return [VehicleValue(vehicle_id) for vehicle_id in model.vehicles_id]


@domain.register(RoadVariable)
def domain_road(variable, model: Scenario, ctx: Context):
    return [RoadValue(road_id) for road_id in model.static_scene.metric_graph.roads.keys()]


@domain.register(JunctionVariable)
def domain_junction(variable, model: Scenario, ctx: Context):
    return [JunctionValue(junction_id) for junction_id in model.static_scene.metric_graph.junctions.keys()]


@domain.register(JunctionEntranceVariable)
def domain_junction_entrance(variable: JunctionEntranceVariable, model: Scenario, ctx: Context):
    if isinstance(variable.junction_node, JunctionVariable):
        junction_node = ctx.get_static_variable(variable.junction_node.name)
    else:
        junction_node = variable.junction_node
    return [JunctionEntranceValue(junction_node, str(i))
            for i in range(model.static_scene.metric_graph.junction_entrance_num(junction_node.id))]


@domain.register(JunctionExitVariable)
def domain_junction_exit(variable: JunctionExitVariable, model: Scenario, ctx: Context):
    if isinstance(variable.junction_node, JunctionVariable):
        junction_node = ctx.get_static_variable(variable.junction_node.name)
    else:
        junction_node = variable.junction_node
    return [JunctionEntranceValue(junction_node, str(i))
            for i in range(model.static_scene.metric_graph.junction_exit_num(junction_node.id))]


@domain.register(StopSignVariable)
def domain_stop_sign(variable: StopSignVariable, model: Scenario, ctx: Context):
    return [StopSignValue(stop_sign.id)
            for stop_sign in model.static_scene.signals.values() if stop_sign.signal_type == SignalType.STOP_SIGN]


@domain.register(TrafficLightVariable)
def domain_traffic_light(variable: TrafficLightVariable, model: Scenario, ctx: Context):
    return [TrafficLightValue(traffic_light_id) for traffic_light_id in model.traffic_lights_id]


def expansion(formula: Formula, model: Scenario):
    return _expansion(formula, model, Context())


@singledispatch
def _expansion(formula, model: Scenario, ctx: Context):
    sub_nodes = tuple(_expansion(sub_node, model, ctx) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)


@_expansion.register(Forall)
def expansion_forall(formula: Forall, model: Scenario, ctx: Context):
    sub_formulas = TrueValue
    for static_variable in domain(formula.variable, model, ctx):
        ctx.add_symbol(formula.variable.name, static_variable)
        cur_formula = _expansion(formula.sub_formula, model, ctx)
        if sub_formulas is None:
            sub_formulas = cur_formula
        else:
            sub_formulas = And(sub_formulas, cur_formula)
        ctx.pop_symbol(formula.variable.name)
    return sub_formulas


@_expansion.register(Exist)
def expansion_exist(formula: Exist, model: Scenario, ctx: Context):
    sub_formulas = FalseValue
    for static_variable in domain(formula.variable, model, ctx):
        ctx.add_symbol(formula.variable.name, static_variable)
        cur_formula = _expansion(formula.sub_formula, model, ctx)
        if sub_formulas is None:
            sub_formulas = cur_formula
        else:
            sub_formulas = Or(sub_formulas, cur_formula)
        ctx.pop_symbol(formula.variable.name)
    return sub_formulas


@_expansion.register(Variable)
def expansion_variable(formula: Variable, model: Scenario, ctx: Context):
    return ctx.get_static_variable(formula.name)
