from adsv.scenario_generator.scenario_pattern.proto import scenario_pattern_pb2
from adsv.semantic_model.metric_graph import Junction, MetricGraph, Node, Edge
from adsv.semantic_model.static_scene import Signal
from adsv.geometry import Vector
from adsv.map_manager import MapInfoLoader
from adsv.utils.types import *
import math


def counterclockwise_angle(vec1: Vector, vec2: Vector):
    dot_ret = vec1.x * vec2.x + vec1.y * vec2.y
    cross_ret = vec1.x * vec2.y - vec1.y * vec2.x
    angle = math.atan2(cross_ret, dot_ret)
    while angle < 0:
        angle += 2 * math.pi
    return angle


def get_entrance_index_map(metric_graph: MetricGraph, junction: Junction) -> List[Node]:
    zero_node = min([metric_graph.node(nid) for nid in junction.entrance_nodes_id],
                    key=lambda node: (node.display_position.y, node.display_position.x))
    max_node = max([metric_graph.node(nid) for nid in junction.entrance_nodes_id],
                    key=lambda node: (node.display_position.y, node.display_position.x))

    mid_position = zero_node.display_position + (max_node.display_position - zero_node.display_position) / 2

    def node_angle(node1: Node, node2: Node):
        if node1 == node2:
            return 0
        vec1 = node1.display_position - mid_position
        vec2 = node2.display_position - mid_position
        return counterclockwise_angle(vec1, vec2)

    return sorted([metric_graph.node(nid) for nid in junction.entrance_nodes_id],
                  key=lambda node: node_angle(zero_node, node))


def get_ordered_directions(metric_graph: MetricGraph, node_id: str) -> List[Edge]:
    enter_edge = next(iter(metric_graph.enter_edges(node_id)))
    last_segment = enter_edge.display_line.line_segments[-1]
    enter_vec = last_segment.v1 - last_segment.v2
    exit_edges = list(metric_graph.exit_edges(node_id))
    def direction_angle(edge: Edge):
        source_node = metric_graph.node(edge.source_id)
        target_node = metric_graph.node(edge.target_id)
        vec = target_node.display_position - source_node.display_position
        return -counterclockwise_angle(vec, enter_vec)
    exit_edges.sort(key=direction_angle)
    return exit_edges


class JunctionPattern(ProtoClass):
    @singledispatchmethod
    def __init__(self, map_data: MapInfoLoader, junction_id: str):
        self._map_name = map_data.map_name
        self._map_data = map_data
        self._metric_graph = self._map_data.metric_graph
        self._junction = self._map_data.metric_graph.junction(junction_id)
        self._entrance_node_map = get_entrance_index_map(self.metric_graph, self.junction)
        self._entrance_directions = \
            [get_ordered_directions(self._map_data.metric_graph, self.entrance_node(i).id) for i in range(self.entrance_num)]

    @__init__.register
    def __init__proto(self, proto: scenario_pattern_pb2.JunctionPattern):
        self.__init__(MapInfoLoader(proto.map_name), proto.junction_id)

    @property
    def map_name(self) -> str:
        return self._map_name

    @property
    def map_data(self) -> MapInfoLoader:
        return self._map_data

    @property
    def metric_graph(self) -> MetricGraph:
        return self._metric_graph

    @property
    def junction(self) -> Junction:
        return self._junction

    def entrance_node(self, index) -> Node:
        return self._entrance_node_map[index]

    def entrance_signal(self, index) -> Optional[Signal]:
        return self._map_data.static_scene.signal_on_node(self.entrance_node(index).id)

    @property
    def entrance_num(self) -> int:
        return len(self._entrance_node_map)

    def directions(self, entrance_index: int) -> List[Edge]:
        return list(self._entrance_directions[entrance_index])

    def direction_num(self, entrance_index: int) -> int:
        return len(self._entrance_directions[entrance_index])

    def direction(self, entrance_index: int, direction_index: int) -> Edge:
        return self._entrance_directions[entrance_index][direction_index]

    def focus_edges(self) -> Set[str]:
        focus_edges_id = set(self.junction.edges_id)
        for node_id in self.junction.entrance_nodes_id:
            focus_edges_id |= set(edge.id for edge in self.metric_graph.enter_edges(node_id))
        for node_id in self.junction.exit_nodes_id:
            focus_edges_id |= set(edge.id for edge in self.metric_graph.exit_edges(node_id))
        return focus_edges_id

    def dump(self) -> scenario_pattern_pb2.JunctionPattern:
        proto = scenario_pattern_pb2.JunctionPattern()
        proto.map_name = self.map_name
        proto.junction_id = self.junction.id

