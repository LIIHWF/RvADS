from adsv.utils.types import *
from adsv.utils import Counter
from adsv.semantic_model.metric_graph import Node, Edge, Junction, Road, MetricGraph, NodeId, EdgeId, JunctionId, RoadId
from adsv.semantic_model.common.map_common import RJType
from queue import Queue


def make_edge_sequence(edges: Iterable[Edge]) -> List[Edge]:
    remain_edges = list(edges)
    ordered_edges = [remain_edges[-1]]
    remain_edges.pop()
    while len(remain_edges) > 0:
        pre_len = len(remain_edges)
        for i in range(len(remain_edges)):
            edge = remain_edges[i]
            if edge.target_id == ordered_edges[0].source_id:
                ordered_edges.insert(0, edge)
                remain_edges.pop(i)
                break
            if edge.source_id == ordered_edges[-1].target_id:
                ordered_edges.insert(len(ordered_edges), edge)
                remain_edges.pop(i)
                break
        if pre_len == len(remain_edges):
            raise ValueError(f'Edges cannot connected into a chain, {edges}')
    return ordered_edges


class NodeEdgeAdapter:
    def __init__(self, nodes: Iterable[Node], edges: Iterable[Edge], opposite_edge_pairs: Iterable[Tuple[EdgeId, EdgeId]],
                 road_id_prefix: RoadId = 'R', junction_id_prefix: JunctionId = 'J'):
        self._nodes: Dict[NodeId, Node] = {node.id: node for node in nodes}
        self._edges: Dict[EdgeId, Edge] = {edge.id: edge for edge in edges}
        self._repair_rj_type()

        self._road_id_prefix = road_id_prefix
        self._junction_id_prefix = junction_id_prefix

        self._enter_edges: Dict[NodeId, List[Edge]] = {node_id: [] for node_id in self._nodes}
        self._exit_edges: Dict[NodeId, List[Edge]] = {node_id: [] for node_id in self._nodes}
        for edge in self._edges.values():
            self._enter_edges[edge.target_id].append(edge)
            self._exit_edges[edge.source_id].append(edge)

        self._junctions: Dict[JunctionId, Junction] = dict()
        self._roads: Dict[RoadId, Road] = dict()
        self._init_junctions()
        self._init_roads()

        self.metric_graph = MetricGraph(list(self._nodes.values()), list(self._edges.values()),
                                        list(self._roads.values()), list(self._junctions.values()), opposite_edge_pairs)

    def _repair_rj_type(self):
        for edge1 in self._edges.values():
            for edge2 in self._edges.values():
                if edge1 != edge2 and edge1.rj_type == RJType.ROAD and \
                        edge2.rj_type == RJType.ROAD and \
                        (edge1.source_id == edge2.source_id or edge1.target_id == edge2.target_id):
                    edge1.set_rj_type(RJType.JUNCTION)
                    edge2.set_rj_type(RJType.JUNCTION)

    def weakly_connected_component(self, condition: Callable) -> List[Tuple[FrozenSet[NodeId], FrozenSet[EdgeId]]]:
        visited_edge = set()
        components: List[Tuple[FrozenSet[EdgeId], FrozenSet[EdgeId]]] = []
        for edge in self._edges.values():
            if condition(edge) and edge.id not in visited_edge:
                component_edges_id: Set[EdgeId] = {edge.id}
                component_nodes_id: Set[NodeId] = set()
                visited_edge.add(edge.id)
                q = Queue()
                q.put(edge.source_id)
                q.put(edge.target_id)
                cnt = 0
                while not q.empty():
                    node_id = q.get()
                    component_nodes_id.add(node_id)
                    for n_edge in self._enter_edges[node_id] + self._exit_edges[node_id]:
                        if condition(n_edge) and n_edge.id not in visited_edge:
                            visited_edge.add(n_edge.id)
                            q.put(n_edge.source_id)
                            q.put(n_edge.target_id)
                            component_edges_id.add(n_edge.id)
                components.append((frozenset(component_nodes_id), frozenset(component_edges_id)))
        return components

    def _init_junctions(self):
        junction_counter = Counter()
        for nodes_id, edges_id in self.weakly_connected_component(lambda edge: edge.rj_type == RJType.JUNCTION):
            junction_id = f'{self._junction_id_prefix}{junction_counter.get()}'
            junction_entrances_id = set()
            junction_exits_id = set()
            for node_id in nodes_id:
                for enter_edge in self._enter_edges[node_id]:
                    if enter_edge.rj_type == RJType.ROAD:
                        junction_entrances_id.add(node_id)
                        break
                else:
                    for exit_edge in self._exit_edges[node_id]:
                        if exit_edge.rj_type == RJType.ROAD:
                            junction_exits_id.add(node_id)
                            break
            self._junctions[junction_id] = Junction(
                junction_id,
                edges_id,
                junction_entrances_id,
                junction_exits_id
            )

    def _init_roads(self):
        road_counter = Counter()
        for nodes_id, edges_id in self.weakly_connected_component(lambda edge: edge.rj_type == RJType.ROAD):
            road_id = f'{self._road_id_prefix}{road_counter.get()}'
            edge_sequence = make_edge_sequence([self._edges[edge_id] for edge_id in edges_id])
            self._roads[road_id] = Road(road_id,
                                        [edge.id for edge in edge_sequence],
                                        edge_sequence[0].source_id,
                                        edge_sequence[-1].target_id
                                        )
