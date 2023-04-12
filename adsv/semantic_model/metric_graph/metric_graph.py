from adsv.utils.types import *
from .element.node import Node, NodeId
from .element.edge import Edge, EdgeId
from .element.road import Road, RoadId
from .element.junction import Junction, JunctionId
from adsv.semantic_model.metric_graph.proto import metric_graph_pb2


def get_enter_exit_edges(nodes, edges):
    enter_edges = {node_id: set() for node_id in nodes}
    exit_edges = {node_id: set() for node_id in nodes}
    for edge in edges.values():
        enter_edges[edge.target_id].add(edge)
        exit_edges[edge.source_id].add(edge)
    static_enter_edges = MappingProxyType({
        node_id: frozenset(edge_set) for node_id, edge_set in enter_edges.items()
    })
    static_exit_edges = MappingProxyType({
        node_id: frozenset(edge_set) for node_id, edge_set in exit_edges.items()
    })
    return static_enter_edges, static_exit_edges


class MetricGraph(ProtoClass):
    @singledispatchmethod
    def __init__(self, nodes: Iterable[Node], edges: Iterable[Edge],
                 roads: Iterable[Road], junctions: Iterable[Junction], opposite_edges: Iterable[Tuple[EdgeId, EdgeId]]):
        self._nodes: Mapping[NodeId, Node] = MappingProxyType({node.id: node for node in nodes})
        self._edges: Mapping[EdgeId, Edge] = MappingProxyType({edge.id: edge for edge in edges})
        self._roads: Mapping[RoadId, Road] = MappingProxyType({road.id: road for road in roads})
        self._junctions: Mapping[JunctionId, Junction] = MappingProxyType({
            junction.id: junction for junction in junctions})
        self._enter_edges, self._exit_edges = get_enter_exit_edges(self.nodes, self.edges)
        self._edges_road: Mapping[EdgeId, Road] = MappingProxyType({
            edge_id: road for road in self.roads.values() for edge_id in road.edge_id_sequence})
        self._edges_junction: Mapping[EdgeId, Junction] = MappingProxyType({
            edge_id: junction for junction in self.junctions.values() for edge_id in junction.edges_id})
        self._opposite_edge: Mapping[EdgeId, EdgeId] = MappingProxyType({
            edge1_id: edge2_id for edge1_id, edge2_id in opposite_edges
        })

    @__init__.register
    def __init__proto(self, proto: metric_graph_pb2.MetricGraph):
        self.__init__(
            [Node(node_proto) for node_proto in proto.nodes],
            [Edge(edge_proto) for edge_proto in proto.edges],
            [Road(road_proto) for road_proto in proto.roads],
            [Junction(junction_proto) for junction_proto in proto.junctions],
            [(opposite_proto.edge1_id, opposite_proto.edge2_id) for opposite_proto in proto.opposite_edges]
        )

    def dump(self) -> 'metric_graph_pb2.MetricGraph':
        proto = metric_graph_pb2.MetricGraph()
        for node in self.nodes.values():
            node_proto = proto.nodes.add()
            node_proto.CopyFrom(node.dump())
        for edge in self.edges.values():
            edge_proto = proto.edges.add()
            edge_proto.CopyFrom(edge.dump())
        for road in self.roads.values():
            road_proto = proto.roads.add()
            road_proto.CopyFrom(road.dump())
        for junction in self.junctions.values():
            junction_proto = proto.junctions.add()
            junction_proto.CopyFrom(junction.dump())
        for opposite_pair in self._opposite_edge.items():
            opposite_proto = proto.opposite_edges.add()
            opposite_proto.edge1_id = opposite_pair[0]
            opposite_proto.edge2_id = opposite_pair[1]
        return proto

    def opposite(self, edge_id: EdgeId) -> Optional[EdgeId]:
        return self._opposite_edge[edge_id] if edge_id in self._opposite_edge else None

    @property
    def nodes(self) -> Mapping[NodeId, Node]:
        return self._nodes

    @property
    def edges(self) -> Mapping[EdgeId, Edge]:
        return self._edges

    def node(self, node_id: NodeId) -> Node:
        return self.nodes[node_id]

    def edge(self, edge_id: EdgeId) -> Edge:
        return self.edges[edge_id]

    @property
    def roads(self) -> Mapping[RoadId, Road]:
        return self._roads

    @property
    def junctions(self) -> Mapping[JunctionId, Junction]:
        return self._junctions

    def road(self, road_id: RoadId) -> Road:
        return self.roads[road_id]

    def junction(self, junction_id: JunctionId) -> Junction:
        return  self.junctions[junction_id]

    @property
    def edges_road(self) -> Mapping[EdgeId, Road]:
        return self._edges_road

    def edge_road(self, edge_id: EdgeId) -> Optional[Road]:
        return self._edges_road[edge_id] if edge_id in self._edges_road else None

    @property
    def edges_junction(self) -> Mapping[EdgeId, Junction]:
        return self._edges_junction

    def edge_junction(self, edge_id) -> Optional[Junction]:
        return self._edges_junction[edge_id] if edge_id in self._edges_junction else None

    def enter_edges(self, node_id: NodeId) -> FrozenSet[Edge]:
        return self._enter_edges[node_id]

    def exit_edges(self, node_id: NodeId) -> FrozenSet[Edge]:
        return self._exit_edges[node_id]

    def node_edges(self, node_id: NodeId) -> FrozenSet[Edge]:
        return self.enter_edges(node_id) | self.exit_edges(node_id)

    def node_road(self, node_id: NodeId) -> Optional[Road]:
        for edge in self.node_edges(node_id):
            road = self.edge_road(edge.id)
            if road is not None:
                return road
        return None

    def node_junction(self, node_id: NodeId) -> Optional[Junction]:
        for edge in self.node_edges(node_id):
            junction = self.edge_junction(edge.id)
            if junction is not None:
                return junction
        return None

    def edge_source(self, edge_id: EdgeId) -> Node:
        return self.nodes[self.edges[edge_id].source_id]

    def edge_target(self, edge_id: EdgeId) -> Node:
        return self.nodes[self.edges[edge_id].target_id]

    def edge_length(self, edge_id: EdgeId) -> Number:
        return self.edges[edge_id].length

    def road_edge_sequence(self, road_id: RoadId) -> Tuple[Edge, ...]:
        return tuple(self.edges[edge_id] for edge_id in self.roads[road_id].edge_id_sequence)

    def road_entrance(self, road_id: RoadId) -> Node:
        return self.nodes[self.roads[road_id].entrance_id]

    def road_exit(self, road_id: RoadId) -> Node:
        return self.nodes[self.roads[road_id].exit_id]

    def junction_edges(self, junction_id: JunctionId) -> FrozenSet[Edge]:
        return frozenset(self.edges[edge_id] for edge_id in self.junctions[junction_id].edges_id)

    def junction_entrance_nodes(self, junction_id: JunctionId) -> Tuple[Node, ...]:
        return tuple(self.nodes[node_id] for node_id in self.junctions[junction_id].entrance_nodes_id)

    def junction_entrance_num(self, junction_id: JunctionId) -> int:
        return self.junctions[junction_id].entrance_num

    def junction_exit_nodes(self, junction_id: JunctionId) -> Tuple[Node, ...]:
        return tuple(self.nodes[node_id] for node_id in self.junctions[junction_id].exit_nodes_id)

    def junction_exit_num(self, junction_id: JunctionId) -> int:
        return self.junctions[junction_id].exit_num

    def strict_eq(self, other: 'MetricGraph'):
        if self.nodes.keys() != other.nodes.keys():
            return False
        elif not all(self.nodes[node_id].strict_eq(other.nodes[node_id]) for node_id in self.nodes):
            return False

        if self.edges.keys() != other.edges.keys():
            return False
        elif not all(self.edges[edge_id].strict_eq(other.edges[edge_id]) for edge_id in self.edges):
            return False

        if self.roads.keys() != other.roads.keys():
            return False
        elif not all(self.roads[road_id].strict_eq(other.roads[road_id]) for road_id in self.roads):
            return False

        if self.junctions.keys() != other.junctions.keys():
            return False
        elif not all(self.junctions[junction_id].strict_eq(other.junctions[junction_id])
                     for junction_id in self.junctions):
            return False

        return True

    def sub_graph(self, edges_id: Iterable[str]):
        edges = [self.edges[edge_id] for edge_id in edges_id]
        nodes_id = set(edge.target_id for edge in edges) | set(edge.source_id for edge in edges)
        nodes = [self.nodes[node_id] for node_id in nodes_id]
        n_roads = []
        n_junctions = []
        for road in self.roads.values():
            if all([(edge_id in edges_id) for edge_id in road.edge_id_sequence]):
                n_roads.append(road)
        for junction in self.junctions.values():
            if all([(edge_id in edges_id) for edge_id in junction.edges_id]):
                n_junctions.append(junction)
        n_opposite = []
        for oppo in self._opposite_edge.items():
            if oppo[0] in edges_id and oppo[1] in edges_id:
                n_opposite.append(oppo)
        return MetricGraph(nodes, edges, n_roads, n_junctions, n_opposite)
