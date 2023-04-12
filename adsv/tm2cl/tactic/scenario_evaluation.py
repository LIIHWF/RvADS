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
from .convert_to_automata import AutomataNode
from adsv.tm2cl.automata.automata import AutomataResult
from .add_multi_operator import MultiOr, MultiAnd, MultiImplies, MultiNot


def road_length(scene: Scene, road_id: RoadId):
    return sum(scene.metric_graph.edge(edge_id).length for edge_id in scene.metric_graph.road(road_id).edge_id_sequence)


def road_offset_edge(scene: Scene, road_id: RoadId, edge_id: EdgeId, edge_offset: Number) -> Optional[Number]:
    pre_length = 0
    for cur_edge_id in scene.metric_graph.road(road_id).edge_id_sequence:
        if cur_edge_id == edge_id:
            return pre_length + edge_offset
        else:
            pre_length += scene.metric_graph.edge(cur_edge_id).length
    return pre_length


def road_offset_node(scene: Scene, road_id: RoadId, node_id: NodeId) -> Optional[Number]:
    road = scene.metric_graph.road(road_id)
    if node_id == road.entrance_id:
        return 0
    cum_length = 0
    for edge_id in road.edge_id_sequence:
        edge = scene.metric_graph.edge(edge_id)
        cum_length += edge.length
        if edge.target_id == node_id:
            return cum_length
    return None


def handle_formula(formula: AstNode):
    if isinstance(formula, ArithmeticConstraint):
        return arithmetic_calculation(formula)
    else:
        return tautology_elimination(formula)


def is_determined(formula: AstNode):
    return formula is TrueValue or formula is FalseValue or isinstance(formula, StaticValue) or isinstance(formula, StaticVariable)


@singledispatch
def scenario_evaluation(formula: AstNode, scene: Scenario, i_: int) -> AstNode:
    sub_nodes = [sub_node for sub_node in formula.sub_nodes]
    current_formula = handle_formula(formula)
    i = 0
    while not is_determined(current_formula):
        if is_determined(sub_nodes[i]):
            i += 1
        else:
            sub_nodes[i] = handle_formula(scenario_evaluation(sub_nodes[i], scene, i_))
            current_formula = handle_formula(formula.apply_sub_nodes(*sub_nodes))
    return current_formula


@scenario_evaluation.register
def scenario_evaluation_arithmetic(formula: ArithmeticConstraint, scene: Scenario, i_: int) -> AstNode:
    left_exp = formula.left_exp
    right_exp = formula.right_exp
    if not isinstance(left_exp, ArithmeticConstant):
        left_exp = scenario_evaluation(formula.left_exp, scene, i_)
    if not isinstance(right_exp, ArithmeticConstant):
        right_exp = scenario_evaluation(formula.right_exp, scene, i_)
    if not (isinstance(left_exp, ArithmeticConstant) and isinstance(right_exp, ArithmeticConstant)):
        raise ValueError

    if formula.operator == ArithmeticOperator.EQ:
        return TrueValue if left_exp.value == right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.NEQ:
        return TrueValue if left_exp.value != right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.LT:
        return TrueValue if left_exp.value < right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.LE:
        return TrueValue if left_exp.value <= right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.GT:
        return TrueValue if left_exp.value > right_exp.value else FalseValue
    elif formula.operator == ArithmeticOperator.GE:
        return TrueValue if left_exp.value >= right_exp.value else FalseValue


def eval_at_node(scene: Scene, vehicle_state: VehicleState, node_id: NodeId):
    edge = scene.metric_graph.edge(vehicle_state.edge_id)
    if edge.target_id == node_id and vehicle_state.at_stop_target and not vehicle_state.reached_destination and edge.length - vehicle_state.offset < 3:
        return TrueValue
    return FalseValue


@scenario_evaluation.register(MultiAnd)
def scenario_evaluation_multiand(formula: MultiAnd, scenario: Scenario, i_: int):
    for sub_formula in formula.sub_nodes:
        if scenario_evaluation(sub_formula, scenario, i_) is FalseValue:
            return FalseValue
    return TrueValue


@scenario_evaluation.register(MultiOr)
def scenario_evaluation_multior(formula: MultiOr, scenario: Scenario, i_: int):
    for sub_formula in formula.sub_nodes:
        if scenario_evaluation(sub_formula, scenario, i_) is TrueValue:
            return TrueValue
    return FalseValue


@scenario_evaluation.register(MultiImplies)
def scenario_evaluation_multiimplies(formula: MultiImplies, scenario: Scenario, i_: int):
    for sub_formula in formula.sub_nodes[:-1]:
        if scenario_evaluation(sub_formula, scenario, i_) is FalseValue:
            return TrueValue
    if scenario_evaluation(formula.sub_nodes[-1], scenario, i_) is FalseValue:
        return FalseValue
    return TrueValue


@scenario_evaluation.register(MultiNot)
def scenario_evaluation_multinot(formula: MultiNot, scenario: Scenario, i_: int):
    sub_eval = scenario_evaluation(formula.sub_formula, scenario, i_)
    if sub_eval is FalseValue:
        return TrueValue
    elif sub_eval is TrueValue:
        return FalseValue
    else:
        raise NotImplementedError


@scenario_evaluation.register(At)
def scenario_evaluation_at(formula: At, scenario: Scenario, i_: int):
    scene = scenario.scene(i_)
    obj = formula.object
    position_set = formula.position_set
    # obj = scenario_evaluation(formula.object, scene, i_)
    # position_set = scenario_evaluation(formula.position_set, scene, i_)
    if contains_variable(obj) or contains_variable(position_set):
        return At(obj, position_set)
    if not isinstance(obj, VehicleValue):
        return At(obj, position_set)

    vehicle_id = obj.id
    vehicle_state = scene.dynamic_scene.vehicle_state(vehicle_id)

    if isinstance(position_set, RoadValue):
        road = scene.metric_graph.edge_road(vehicle_state.edge_id)
        if road is None:
            return FalseValue
        return TrueValue if road.id == position_set.id else FalseValue

    if isinstance(position_set, JunctionValue):
        junction = scene.metric_graph.edge_junction(vehicle_state.edge_id)
        if junction is None:
            return FalseValue
        return TrueValue if junction.id == position_set.id else FalseValue

    if isinstance(position_set, RoadExit):
        node_id = scene.metric_graph.road(position_set.road_node.id).exit_id
        return eval_at_node(scene, vehicle_state, node_id)

    if isinstance(position_set, RoadEntrance):
        node_id = scene.metric_graph.road(position_set.road_node.id).entrance_id
        return eval_at_node(scene, vehicle_state, node_id)

    if isinstance(position_set, JunctionEntranceValue):
        node_id = scene.metric_graph.junction(position_set.junction_node.id).entrance_nodes_id[position_set.node_order]
        return eval_at_node(scene, vehicle_state, node_id)

    if isinstance(position_set, JunctionExitValue):
        node_id = scene.metric_graph.junction(position_set.junction_node.id).exit_nodes_id[position_set.node_order]
        return eval_at_node(scene, vehicle_state, node_id)

    if isinstance(position_set, JunctionEntranceSet):
        for node_id in scene.metric_graph.junction(position_set.junction_node.id).entrance_nodes_id:
            if eval_at_node(scene, vehicle_state, node_id) == TrueValue:
                return TrueValue
        return FalseValue

    if isinstance(position_set, JunctionExitSet):
        for node_id in scene.metric_graph.junction(position_set.junction_node.id).exit_nodes_id:
            if eval_at_node(scene, vehicle_state, node_id) == TrueValue:
                return TrueValue
        return FalseValue

    return At(obj, position_set)


def eval_node_node_meet(scene: Scene, node1_id: NodeId, node2_id: NodeId):
    edges = scene.metric_graph.exit_edges(node1_id) | scene.metric_graph.enter_edges(node2_id)
    min_dis = INF
    for edge in edges:
        if edge.source_id == node1_id and edge.target_id == node2_id:
            min_dis = min(edge.length, min_dis)
    if min_dis != INF:
        return min_dis

    node1_road = scene.metric_graph.node_road(node1_id)
    node2_road = scene.metric_graph.node_road(node2_id)
    if node1_road == node2_road and node1_road is not None:
        road_id = node1_road.id
        node1_offset = road_offset_node(scene, road_id, node1_id)
        node2_offset = road_offset_node(scene, road_id, node2_id)
        if node1_offset <= node2_offset:
            return node1_offset - node1_offset
    return INF


def eval_edge_node_meet(scene: Scene, edge1_id: EdgeId, offset1: Number, node2_id: NodeId):
    edge = scene.metric_graph.edge(edge1_id)
    if edge.target_id == node2_id:
        return edge.length - offset1

    road1 = scene.metric_graph.edge_road(edge1_id)
    road2 = scene.metric_graph.node_road(node2_id)
    if road1 is not None and road2 is not None and road1 == road2:
        road_id = road1.id
        road_offset1 = road_offset_edge(scene, road_id, edge1_id, offset1)
        road_offset2 = road_offset_node(scene, road_id, node2_id)
        if road_offset1 <= road_offset2:
            return road_offset2 - road_offset1
    return INF


def eval_node_edge_meet(scene: Scene, node1_id: NodeId, edge2_id: EdgeId, offset2: Number):
    edge = scene.metric_graph.edge(edge2_id)
    if edge.target_id == node1_id:
        return offset2

    road1 = scene.metric_graph.node_road(node1_id)
    road2 = scene.metric_graph.edge_road(edge2_id)
    if road1 is not None and road2 is not None and road1 == road2:
        road_id = road1.id
        road_offset1 = road_offset_node(scene, road_id, node1_id)
        road_offset2 = road_offset_edge(scene, road_id, edge2_id, offset2)
        if road_offset1 <= road_offset2:
            return road_offset2 - road_offset1
    return INF


def eval_edge_edge_meet(scene: Scene, edge1_id: EdgeId, offset1: Number, edge2_id: EdgeId, offset2: Number):
    if edge1_id == edge2_id:
        if offset1 <= offset2:
            return offset2 - offset1
        return INF

    road1 = scene.metric_graph.edge_road(edge1_id)
    road2 = scene.metric_graph.edge_road(edge2_id)

    if road1 is not None and road2 is not None and road1 == road2:
        road_id = road1.id
        road_offset1 = road_offset_edge(scene, road_id, edge1_id, offset1)
        road_offset2 = road_offset_edge(scene, road_id, edge2_id, offset2)
        if road_offset1 <= road_offset2:
            return road_offset2 - road_offset1
    return INF


@scenario_evaluation.register(Dist)
def scenario_evaluation_meet(formula: Dist, scenario: Scenario, i_: int):
    scene = scenario.scene(i_)
    from_obj = scenario_evaluation(formula.from_obj, scene, i_)
    to_obj = scenario_evaluation(formula.to_obj, scene, i_)
    if contains_variable(from_obj) or contains_variable(to_obj):
        return Dist(from_obj, to_obj)

    if isinstance(from_obj, SignalNode) and isinstance(to_obj, SignalNode):
        node1_id = scene.static_scene.signal(from_obj.id).state.control_node_id
        node2_id = scene.static_scene.signal(to_obj.id).state.control_node_id
        return ArithmeticConstant(eval_node_node_meet(scene, node1_id, node2_id))

    if isinstance(from_obj, VehicleValue) and isinstance(to_obj, SignalNode):
        vehicle_state = scene.dynamic_scene.vehicle_state(from_obj.id)
        edge_id, offset = vehicle_state.edge_id, vehicle_state.offset
        node2_id = scene.static_scene.signal(to_obj.id).state.control_node_id
        return ArithmeticConstant(eval_edge_node_meet(scene, edge_id, offset, node2_id))

    if isinstance(from_obj, VehicleValue) and isinstance(to_obj, VehicleValue):
        vehicle1_state = scene.dynamic_scene.vehicle_state(from_obj.id)
        vehicle2_state = scene.dynamic_scene.vehicle_state(to_obj.id)
        edge1_id, offset1 = vehicle1_state.edge_id, vehicle1_state.offset
        edge2_id, offset2 = vehicle2_state.edge_id, vehicle2_state.offset
        return ArithmeticConstant(eval_edge_edge_meet(scene, edge1_id, offset1, edge2_id, offset2))

    if isinstance(from_obj, SignalNode) and isinstance(to_obj, VehicleValue):
        node1_id = scene.static_scene.signal(from_obj.id).state.control_node_id
        vehicle_state = scene.dynamic_scene.vehicle_state(to_obj.id)
        edge2_id, offset2 = vehicle_state.edge_id, vehicle_state.offset
        return ArithmeticConstant(eval_node_edge_meet(scene, node1_id, edge2_id, offset2))

    return Dist(from_obj, to_obj)


@scenario_evaluation.register(WaitingTime)
def scenario_evaluation_waitingtime(formula: WaitingTime, scenario: Scenario, i_: int):
    if isinstance(formula.vehicle, VehicleValue):
        return ArithmeticConstant(scenario.scene(i_).waiting_time(formula.vehicle.id))
    return WaitingTime(formula.vehicle)


@scenario_evaluation.register(Speed)
def scenario_evaluation_speed(formula: Speed, scenario: Scenario, i_: int):
    if isinstance(formula.vehicle, VehicleValue):
        return ArithmeticConstant(scenario.scene(i_).dynamic_scene.vehicle_state(formula.vehicle.id).control_speed)


@scenario_evaluation.register(TrafficLightColorConstraint)
def scenario_evaluation_tflc(formula: TrafficLightColorConstraint, scenario: Scenario, i_: int):
    scene = scenario.scene(i_)
    traffic_light_value = scenario_evaluation(formula.traffic_light_node, scene, i_)
    color = scenario_evaluation(formula.color, scene, i_)
    if contains_variable(traffic_light_value) or contains_variable(color):
        return TrafficLightColorConstraint(traffic_light_value, color)
    return TrueValue if scene.dynamic_scene.traffic_light_state(traffic_light_value.id).color == color.value \
        else FalseValue


@scenario_evaluation.register(Always)
def scenario_evaluation_always(formula: Always, scenario: Scenario, i_: int):
    result_formula = TrueValue
    for i in range(i_, scenario.ticks_num):
        cur_tick_formula = handle_formula(scenario_evaluation(formula.sub_formula, scenario, i))
        if cur_tick_formula == FalseValue:
            return FalseValue
        if cur_tick_formula == TrueValue:
            pass
        else:
            raise NotImplemented  # TODO
    return result_formula


@scenario_evaluation.register(Eventual)
def scenario_evaluation_eventual(formula: Eventual, scenario: Scenario, i_: int):
    result_formula = FalseValue
    for i in range(i_, scenario.ticks_num):
        cur_tick_formula = handle_formula(scenario_evaluation(formula.sub_formula, scenario, i))
        if cur_tick_formula == TrueValue:
            return TrueValue
        if cur_tick_formula == FalseValue:
            pass
        else:
            raise NotImplemented
    return result_formula


@scenario_evaluation.register(TurnRight)
def scenario_evaluation_turnright(formula: TurnRight, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return TurnRight(formula.vehicle)
    edge_id = scenario.scene(i_).dynamic_scene.vehicle_state(formula.vehicle.id).edge_id
    edge = scenario.static_scene.metric_graph.edge(edge_id)
    if edge.turn_type == TurnType.RIGHT_TURN:
        return TrueValue
    else:
        return FalseValue


@scenario_evaluation.register(TurnLeft)
def scenario_evaluation_turnleft(formula: TurnLeft, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return TurnLeft(formula.vehicle)
    edge_id = scenario.scene(i_).dynamic_scene.vehicle_state(formula.vehicle.id).edge_id
    edge = scenario.static_scene.metric_graph.edge(edge_id)
    if edge.turn_type == TurnType.LEFT_TURN:
        return TrueValue
    else:
        return FalseValue


@scenario_evaluation.register(GoStraight)
def scenario_evaluation_gostraight(formula: GoStraight, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return GoStraight(formula.vehicle)
    edge_id = scenario.scene(i_).dynamic_scene.vehicle_state(formula.vehicle.id).edge_id
    edge = scenario.static_scene.metric_graph.edge(edge_id)
    if edge.turn_type == TurnType.NO_TURN:
        return TrueValue
    else:
        return FalseValue


@scenario_evaluation.register(Until)
def scenario_evaluation_until(formula: Until, scenario: Scenario, i_: int):
    left_formula_result = TrueValue
    right_formula_result = FalseValue
    for i in range(i_, scenario.ticks_num):
        cur_tick_right_result = handle_formula(scenario_evaluation(formula.right_formula, scenario, i))
        if cur_tick_right_result == TrueValue:
            return TrueValue
        if cur_tick_right_result == FalseValue:
            pass
        else:
            raise ValueError(f'cur_tick_right_result: {repr(cur_tick_right_result)}')  # TODO

        cur_tick_left_result = handle_formula(scenario_evaluation(formula.left_formula, scenario, i))
        if cur_tick_left_result == FalseValue:
            return FalseValue
        if cur_tick_left_result == TrueValue:
            pass
        else:
            raise NotImplemented  # TODO
    return FalseValue


@scenario_evaluation.register(Next)
def scenario_evaluation_next(formula: Next, scenario: Scenario, i_: int):
    if i_ + 1 >= scenario.ticks_num:
        return FalseValue
    return scenario_evaluation(formula.sub_formula, scenario, i_ + 1)


def eval_next(vid: str, scenario: Scenario, i_: int, turn_type: TurnType):
    itinerary = scenario.scenario_configuration.vehicles_configuration[vid].itinerary
    itinerary_index = scenario.dynamic_scenario.dynamic_scene(i_).vehicle_state(vid).itinerary_index
    if itinerary_index > len(itinerary.segment_id_seq) - 2:
        return FalseValue
    next_edge_id = itinerary.segment_id_seq[itinerary_index + 1]
    if scenario.static_scene.metric_graph.edge(next_edge_id).turn_type == turn_type:
        return TrueValue
    else:
        return FalseValue


@scenario_evaluation.register(NextTurnLeft)
def scenario_evaluation_nextturnleft(formula: NextTurnLeft, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return NextTurnLeft(formula.vehicle)
    return eval_next(formula.vehicle.id, scenario, i_, TurnType.LEFT_TURN)


@scenario_evaluation.register(NextTurnRight)
def scenario_evaluation_nextturnright(formula: NextTurnRight, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return NextTurnRight(formula.vehicle)
    return eval_next(formula.vehicle.id, scenario, i_, TurnType.RIGHT_TURN)


@scenario_evaluation.register(NextGoStraight)
def scenario_evaluation_nextgostraight(formula: NextGoStraight, scenario: Scenario, i_: int):
    if not isinstance(formula.vehicle, StaticVariable):
        return NextGoStraight(formula.vehicle)
    return eval_next(formula.vehicle.id, scenario, i_, TurnType.NO_TURN)


@scenario_evaluation.register(AutomataNode)
def scenario_evaluation_automata(formula: AutomataNode, scenario: Scenario, i_: int):
    def scenario_iterator():
        for i in range(i_, scenario.ticks_num):
            positive_symbols = set()
            for symbol in formula.symbols:
                sub_formula = formula.formula(symbol)
                evaluation = scenario_evaluation(sub_formula, scenario, i)
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
