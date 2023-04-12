from adsv.semantic_model.lane_map import LaneMap, Section, SectionId
from adsv.geometry import Vertex, average_vertex, Polyline
from adsv.utils.types import *
from adsv.utils import Counter
from adsv.semantic_model.metric_graph import Edge, Node, NodeId, EdgeId
from .node_edge_adapter import NodeEdgeAdapter
import itertools


class LaneMapAdapter:
    def __init__(self, lane_map: 'LaneMap', node_id_prefix: NodeId = 'v', edge_id_prefix: EdgeId = 'e'):
        self._lane_map = lane_map
        self._node_id_prefix = node_id_prefix
        self._edge_id_prefix = edge_id_prefix
        _nodes, _edges, self.section_edge_pairs = self._generate_nodes_and_edges_by_section()
        self._nodes: Mapping[NodeId, Node] = MappingProxyType({node.id: node for node in _nodes})
        self._edges: Mapping[EdgeId, Edge] = MappingProxyType({edge.id: edge for edge in _edges})
        opposite_edge_pairs = self._get_opposite_edge_pairs()
        self.metric_graph = NodeEdgeAdapter(_nodes, _edges, opposite_edge_pairs).metric_graph

    def _get_opposite_edge_pairs(self) -> Iterable[Tuple[EdgeId, EdgeId]]:
        edge_section_map: Mapping[EdgeId, Section] = \
            MappingProxyType({edge_id: self._lane_map.sections[section_id] for section_id, edge_id in self.section_edge_pairs})
        section_edge_map: Mapping[SectionId, Edge] = \
            MappingProxyType({section_id: self._edges[edge_id] for section_id, edge_id in self.section_edge_pairs})
        node_source_edge: Mapping[NodeId, List[Edge]] = {node_id: list() for node_id in self._nodes}
        node_target_edge: Mapping[NodeId, List[Edge]] = {node_id: list() for node_id in self._nodes}
        opposite_map: Dict[EdgeId, EdgeId] = dict()
        for edge in self._edges.values():
            node_source_edge[edge.source_id].append(edge)
            node_target_edge[edge.target_id].append(edge)
            section = edge_section_map[edge.id]
            if section.left_section_id is not None:
                opposite_map[edge.id] = section_edge_map[section.left_section_id].id
        flag = True
        while flag:
            flag = False
            for edge1, edge2 in itertools.product(self._edges.values(), self._edges.values()):
                if edge1.id != edge2.id and edge1.id not in opposite_map and edge2.id not in opposite_map:
                    tmp_list = node_source_edge[edge1.target_id]
                    edge1_succ_edge = None if len(tmp_list) != 1 else tmp_list[0]
                    tmp_list = node_target_edge[edge1.source_id]
                    edge1_prev_edge = None if len(tmp_list) != 1 else tmp_list[0]
                    tmp_list = node_source_edge[edge2.target_id]
                    edge2_succ_edge = None if len(tmp_list) != 1 else tmp_list[0]
                    tmp_list = node_target_edge[edge2.source_id]
                    edge2_prev_edge = None if len(tmp_list) != 1 else tmp_list[0]
                    if edge1_succ_edge is None or edge1_prev_edge is None or \
                            edge2_succ_edge is None or edge2_prev_edge is None:
                        continue
                    if edge2_prev_edge.id in opposite_map and edge2_succ_edge.id in opposite_map and \
                            edge1_succ_edge.id == opposite_map[edge2_prev_edge.id] and \
                            edge1_prev_edge.id == opposite_map[edge2_succ_edge.id]:
                        opposite_map[edge1.id] = edge2.id
                        opposite_map[edge2.id] = edge1.id
                        flag = True
        return [(edge1_id, edge2_id) for edge1_id, edge2_id in opposite_map.items()]

    def _get_section_direct_vertex(self, section_id: SectionId) -> Tuple[Vertex, Vertex]:
        return self._lane_map.sections[section_id].reference_line.vertices[0], \
               self._lane_map.sections[section_id].reference_line.vertices[-1]

    def _get_section_predecessors_id(self, section_id: SectionId) -> FrozenSet[SectionId]:
        ret = set()
        for lane in self._lane_map.sections[section_id].ordered_lanes:
            for pred_lane_id in lane.predecessors_id:
                pred_section = self._lane_map.get_lane_section(pred_lane_id)
                ret.add(pred_section.id)
        return frozenset(ret)

    def _get_section_successors_id(self, section_id: SectionId) -> FrozenSet[SectionId]:
        ret = set()
        for lane in self._lane_map.sections[section_id].ordered_lanes:
            for suc_lane_id in lane.successors_id:
                suc_section = self._lane_map.get_lane_section(suc_lane_id)
                ret.add(suc_section.id)
        return frozenset(ret)

    def _get_section_start_connection(self, section_id: SectionId) -> Tuple[
        FrozenSet[SectionId], FrozenSet[SectionId]]:
        predecessors_id = self._get_section_predecessors_id(section_id)
        end_sections = set()
        start_sections = {section_id}
        for predecessor_id in predecessors_id:
            end_sections.add(predecessor_id)
            for successor_id in self._get_section_successors_id(predecessor_id):
                start_sections.add(successor_id)
        return frozenset(start_sections), frozenset(end_sections)

    def _get_section_end_connection(self, section_id: SectionId) -> Tuple[
        FrozenSet[SectionId], FrozenSet[SectionId]]:
        successors_id = self._get_section_successors_id(section_id)
        start_sections = set()
        end_sections = {section_id}
        for successor_id in successors_id:
            start_sections.add(successor_id)
            for predecessor_id in self._get_section_predecessors_id(successor_id):
                end_sections.add(predecessor_id)
        return frozenset(start_sections), frozenset(end_sections)

    def _get_section_vertex(self, section_id: SectionId) -> Tuple[Vertex, Vertex]:
        predecessors_id = self._get_section_predecessors_id(section_id)
        successors_id = self._get_section_successors_id(section_id)
        start_vertex, end_vertex = self._get_section_direct_vertex(section_id)
        start_vertices = {start_vertex}
        end_vertices = {end_vertex}
        for successor_id in successors_id:
            start_vertex, end_vertex = self._get_section_direct_vertex(successor_id)
            end_vertices.add(start_vertex)
            for predecessor_id in self._get_section_predecessors_id(successor_id):
                start_vertex, end_vertex = self._get_section_direct_vertex(predecessor_id)
                end_vertices.add(end_vertex)

        for predecessor_id in predecessors_id:
            start_vertex, end_vertex = self._get_section_direct_vertex(predecessor_id)
            start_vertices.add(end_vertex)
            for successor_id in self._get_section_successors_id(predecessor_id):
                start_vertex, end_vertex = self._get_section_direct_vertex(successor_id)
                start_vertices.add(start_vertex)
        return average_vertex(*start_vertices), average_vertex(*end_vertices)

    def _generate_nodes_and_edges_by_section(self) -> Tuple[List[Node], List[Edge], List[Tuple[SectionId, EdgeId]]]:
        section_source_node_map: Dict[SectionId, Node] = dict()
        section_target_node_map: Dict[SectionId, Node] = dict()
        nodes: List[Node] = []
        node_counter = Counter()

        def generate_node(display_position: Vertex) -> Node:
            node_id = f'{self._node_id_prefix}{node_counter.get()}'
            node_ = Node(node_id, display_position)
            nodes.append(node_)
            return node_

        for section_id, section in self._lane_map.sections.items():
            if section_id not in section_source_node_map or section_id not in section_target_node_map:
                source_vertex, target_vertex = self._get_section_vertex(section_id)
                if section_id not in section_source_node_map:
                    node = generate_node(source_vertex)
                    s, e = self._get_section_start_connection(section_id)
                    for sid in s:
                        section_source_node_map[sid] = node
                    for sid in e:
                        section_target_node_map[sid] = node

                if section_id not in section_target_node_map:
                    node = generate_node(target_vertex)
                    s, e = self._get_section_end_connection(section_id)
                    for sid in s:
                        section_source_node_map[sid] = node
                    for sid in e:
                        section_target_node_map[sid] = node

        edges: List[Edge] = []
        edge_counter = Counter()
        section_edge_pair: List[Tuple[SectionId, EdgeId]] = []
        for section_id, section in self._lane_map.sections.items():
            edge_id = f'{self._edge_id_prefix}{edge_counter.get()}'
            section_edge_pair.append((section_id, edge_id))
            edges.append(Edge(
                edge_id,
                section_source_node_map[section_id].id,
                section_target_node_map[section_id].id,
                section.length,
                section.rj_type,
                section.turn_type,
                Polyline(section_source_node_map[section_id].display_position,
                         *section.reference_line.vertices[1:-1],
                         section_target_node_map[section_id].display_position)
            ))
        return nodes, edges, section_edge_pair
