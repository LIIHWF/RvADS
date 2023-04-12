from adsv.utils.types import *
from adsv.tm2cl.ast import *
from adsv.tm2cl.ast.internal_node import *
from .common import contains_variable
from adsv.semantic_model.static_scene import StaticScene
from adsv.semantic_model.common.map_common import TurnType


@singledispatch
def static_scene_evaluation(formula: AstNode, static_scene: StaticScene) -> AstNode:
    sub_nodes = tuple(static_scene_evaluation(sub_node, static_scene) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)


def eval_at(obj,
            position_set, static_scene: StaticScene):
    if not isinstance(obj, SignalNode) or contains_variable(obj) or contains_variable(position_set):
        return At(obj, position_set)
    control_node_id = static_scene.signal(obj.id).state.control_node_id
    if isinstance(position_set, RoadEntrance):
        return TrueValue if control_node_id == \
                            static_scene.metric_graph.road(position_set.road_node.id).entrance_id else FalseValue

    if isinstance(position_set, RoadExit):
        return TrueValue if control_node_id == \
                            static_scene.metric_graph.road(position_set.road_node.id).exit_id else FalseValue

    if isinstance(position_set, RoadValue):
        return eval_at(obj, RoadExit(position_set), static_scene) | \
               eval_at(obj, RoadEntrance(position_set), static_scene)

    if isinstance(position_set, JunctionEntranceValue):
        return TrueValue \
            if control_node_id == \
               static_scene.metric_graph.junction(position_set.junction_node.id).entrance_nodes_id[position_set.node_order] \
            else FalseValue

    if isinstance(position_set, JunctionExitValue):
        return TrueValue \
            if control_node_id == \
               static_scene.metric_graph.junction(position_set.junction_node.id).exit_nodes_id[position_set.node_order] \
            else FalseValue

    if isinstance(position_set, JunctionEntranceSet):
        return TrueValue \
            if control_node_id in static_scene.metric_graph.junction(position_set.id).entrance_nodes_id \
            else FalseValue

    if isinstance(position_set, JunctionExitSet):
        return TrueValue \
            if control_node_id in static_scene.metric_graph.junction(position_set.id).exit_nodes_id \
            else FalseValue

    if isinstance(position_set, JunctionValue):
        return eval_at(obj, JunctionEntranceSet(position_set), static_scene) | \
               eval_at(obj, JunctionExitSet(position_set), static_scene)

    return At(obj, position_set)


@static_scene_evaluation.register(At)
def static_scene_evaluation_at(formula: At, static_scene: StaticScene) -> AstNode:
    if isinstance(formula.object, SignalNode) and isinstance(formula.object, StaticVariable) \
            and isinstance(formula.position_set, StaticVariable):
        return eval_at(formula.object, formula.position_set, static_scene)
    else:
        sub_nodes = tuple(static_scene_evaluation(sub_node, static_scene) for sub_node in formula.sub_nodes)
        return formula.apply_sub_nodes(*sub_nodes)


def get_junction_entrance_value_node_id(value: Union[JunctionEntranceValue], static_scene: StaticScene):
    metric_graph = static_scene.metric_graph
    junction_id = value.junction_node.id
    junction = metric_graph.junction(junction_id)
    return junction.entrance_nodes_id[value.node_order]


def get_junction_exit_value_node_id(value: JunctionExitValue, static_scene: StaticScene):
    metric_graph = static_scene.metric_graph
    junction_id = value.junction_node.id
    junction = metric_graph.junction(junction_id)
    return junction.exit_nodes_id[value.node_order]


@static_scene_evaluation.register(Opposite)
def static_scene_evaluation_opposite(formula: Opposite, static_scene: StaticScene) -> AstNode:
    if (isinstance(formula.position1, JunctionEntranceValue) or isinstance(formula.position1, JunctionExitValue)) and \
            (isinstance(formula.position2, JunctionEntranceValue) or isinstance(formula.position1, JunctionExitValue)):
        if isinstance(formula.position1.junction_node, StaticVariable) and isinstance(formula.position2.junction_node,
                                                                                      StaticVariable):
            if formula.position1.junction_node.id != formula.position2.junction_node.id:
                return FalseValue
            elif (isinstance(formula.position1, JunctionEntranceValue) and isinstance(formula.position2,
                                                                                      JunctionExitValue)) or \
                    (isinstance(formula.position2, JunctionExitValue) and isinstance(formula.position2,
                                                                                     JunctionEntranceValue)):
                return FalseValue
            else:
                if isinstance(formula.position1, JunctionEntranceValue):
                    for edge1 in static_scene.metric_graph.exit_edges(
                            get_junction_entrance_value_node_id(formula.position1, static_scene)):
                        for edge2 in static_scene.metric_graph.exit_edges(
                                get_junction_entrance_value_node_id(formula.position2, static_scene)):
                            opposite_edge_id = static_scene.metric_graph.opposite(edge1.id)
                            if opposite_edge_id is not None and opposite_edge_id == edge2.id and \
                                    edge2.turn_type == TurnType.NO_TURN:
                                return TrueValue
                    return FalseValue
                if isinstance(formula.position1, JunctionExitValue):
                    for edge1 in static_scene.metric_graph.enter_edges(
                            get_junction_exit_value_node_id(formula.position2, static_scene)):
                        for edge2 in static_scene.metric_graph.enter_edges(
                                get_junction_exit_value_node_id(formula.position1, static_scene)):
                            opposite_edge_id = static_scene.metric_graph.opposite(edge1.id)
                            if opposite_edge_id is not None and opposite_edge_id == edge2.id and \
                                    edge2.turn_type == TurnType.NO_TURN:
                                return TrueValue
                    return FalseValue
    sub_nodes = tuple(static_scene_evaluation(sub_node, static_scene) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)


@static_scene_evaluation.register(RightOf)
def static_scene_evaluation_rightof(formula: Opposite, static_scene: StaticScene) -> AstNode:
    if (isinstance(formula.position1, JunctionEntranceValue) or
        isinstance(formula.position1, JunctionExitValue)) and \
            (isinstance(formula.position2, JunctionEntranceValue) or
             isinstance(formula.position1, JunctionExitValue)):
        if isinstance(formula.position1.junction_node, StaticVariable) and \
                isinstance(formula.position2.junction_node, StaticVariable):
            if formula.position1.junction_node.id != formula.position2.junction_node.id:
                return FalseValue
            elif isinstance(formula.position1, JunctionEntranceValue) and \
                    isinstance(formula.position2, JunctionEntranceValue):
                for edge1 in static_scene.metric_graph.exit_edges(
                        get_junction_entrance_value_node_id(formula.position1, static_scene)):
                    for edge2 in static_scene.metric_graph.exit_edges(
                            get_junction_entrance_value_node_id(formula.position2, static_scene)):
                        if (
                                (edge1.turn_type == TurnType.RIGHT_TURN and edge2.turn_type == TurnType.NO_TURN) or
                                (edge1.turn_type == TurnType.NO_TURN and edge2.turn_type == TurnType.LEFT_TURN)
                           ) and edge1.target_id == edge2.target_id:
                            return TrueValue
                return FalseValue
            else:
                return FalseValue
    sub_nodes = tuple(static_scene_evaluation(sub_node, static_scene) for sub_node in formula.sub_nodes)
    return formula.apply_sub_nodes(*sub_nodes)
