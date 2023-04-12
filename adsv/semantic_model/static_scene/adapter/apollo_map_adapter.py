from adsv.utils.types import *
from adsv.utils import Counter
from adsv.ads_libs.apollo.map.proto import map_pb2
from adsv.ads_libs.apollo.map.parser import ApolloMapParser
from adsv.semantic_model.lane_map.adapter import ApolloMapAdapter as ApolloLaneMapAdapter
from adsv.semantic_model.lane_map import SectionId
from adsv.semantic_model.metric_graph import MetricGraph, EdgeId, NodeId
from adsv.semantic_model.metric_graph.adapter import LaneMapAdapter
from adsv.semantic_model.static_scene import StaticScene, SignalType, Signal, SignalId, SignalState


class ApolloMapAdapter(metaclass=multimeta):
    @overload
    def __init__(self, apollo_proto: map_pb2.Map, node_id_prefix: NodeId = 'v', edge_id_prefix: EdgeId = 'e',
                 traffic_light_id_prefix: SignalId = 'traffic_light_', stop_sign_id_prefix: SignalId = 'stop_sign_'):
        self._apollo_proto = apollo_proto
        self._node_id_prefix = node_id_prefix
        self._edge_id_prefix = edge_id_prefix
        self._traffic_light_id_prefix = traffic_light_id_prefix
        self._stop_sign_id_prefix = stop_sign_id_prefix
        self._init_lane_map()
        self._init_metric_graph()
        self._init_overlap()
        signals, self.proto_id_signal_id_pairs = self._get_signals()
        self.static_scene = StaticScene(self._metric_graph, signals)

    @overload
    def __init__(self, apollo_proto: bytes, node_id_prefix: NodeId = 'v', edge_id_prefix: EdgeId = 'e',
                 traffic_light_id_prefix: SignalId = 'traffic_light_', stop_sign_id_prefix: SignalId = 'stop_sign_'):
        self.__init__(ApolloMapParser(apollo_proto).proto, node_id_prefix, edge_id_prefix,
                      traffic_light_id_prefix, stop_sign_id_prefix)

    def _init_lane_map(self):
        apollo_lane_map_adapter = ApolloLaneMapAdapter(self._apollo_proto)
        self.apollo_lane_map_adapter = apollo_lane_map_adapter
        self.lane_map = apollo_lane_map_adapter.lane_map
        self._proto_id_lane_id_map = {
            proto_id: lane_id for proto_id, lane_id in apollo_lane_map_adapter.proto_id_lane_id_pairs
        }

    def _init_metric_graph(self):
        lane_map_adapter = LaneMapAdapter(self.lane_map, self._node_id_prefix, self._edge_id_prefix)
        self.lane_map_metric_graph_adapter = lane_map_adapter
        self._metric_graph = lane_map_adapter.metric_graph
        self.section_edge_id_pairs = lane_map_adapter.section_edge_pairs
        self._section_edge_id_map: Dict[SectionId, EdgeId] = {
            section_id: edge_id for section_id, edge_id in lane_map_adapter.section_edge_pairs
        }

    def _init_overlap(self):
        self._overlaps = dict()
        for overlap in self._apollo_proto.overlap:
            self._overlaps[overlap.id.id] = overlap

    def _get_signal(self, signal_proto, id_: SignalId, signal_type: SignalType) -> Signal:
        control_nodes = set()
        for overlap_id in signal_proto.overlap_id:
            overlap = self._overlaps[overlap_id.id]
            for obj_proto in overlap.object:
                if obj_proto.id.id in self._proto_id_lane_id_map:
                    lane_id = self._proto_id_lane_id_map[obj_proto.id.id]
                    edge_id = self._section_edge_id_map[self.lane_map.get_lane_section(lane_id).id]
                    if obj_proto.lane_overlap_info.start_s < self.lane_map.lanes[lane_id].length / 2:
                        control_nodes.add(self._metric_graph.edge(
                            edge_id
                        ).source_id)
                    else:
                        control_nodes.add(self._metric_graph.edge(
                            edge_id
                        ).target_id)
                    edge = self._metric_graph.edge(edge_id)
        if len(control_nodes) != 1:
            raise ValueError(f'found multiple or no control nodes. {control_nodes}')
        control_node = list(control_nodes)[0]
        return Signal(id_, signal_type, SignalState(control_node))

    def _get_signals(self) -> Tuple[List[Signal], List[Tuple[str, SignalId]]]:
        proto_id_signal_id_pairs: List[Tuple[str, SignalId]] = []
        signals = []
        traffic_light_counter = Counter()
        for traffic_light_proto in self._apollo_proto.signal:
            traffic_light_id = f'{self._traffic_light_id_prefix}{traffic_light_counter.get()}'
            signals.append(self._get_signal(traffic_light_proto, traffic_light_id, SignalType.TRAFFIC_LIGHT))
            proto_id_signal_id_pairs.append((traffic_light_proto.id.id, signals[-1].id))

        stop_sign_counter = Counter()
        for stop_sign_proto in self._apollo_proto.stop_sign:
            stop_sign_id = f'{self._stop_sign_id_prefix}{stop_sign_counter.get()}'
            signals.append(self._get_signal(stop_sign_proto, stop_sign_id, SignalType.STOP_SIGN))
            proto_id_signal_id_pairs.append((stop_sign_proto.id.id, signals[-1].id))

        return signals, proto_id_signal_id_pairs
