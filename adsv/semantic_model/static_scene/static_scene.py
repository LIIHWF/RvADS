from adsv.utils.types import *
from adsv.semantic_model.metric_graph import MetricGraph
from .element.signal import Signal, SignalId
from adsv.semantic_model.static_scene.proto import static_scene_pb2


class StaticScene(ProtoClass):
    @singledispatchmethod
    def __init__(self, metric_graph: MetricGraph, signals: Iterable[Signal]):
        self._metric_graph = metric_graph
        self._signals: Mapping[SignalId, Signal] = MappingProxyType({
            signal.id: signal for signal in signals
        })
        self._node_signal_id_map = self._build_node_signal_id_map()

    def _build_node_signal_id_map(self) -> Mapping[str, str]:
        nid_sid_map = dict()
        for sid, signals in self.signals.items():
            nid_sid_map[signals.state.control_node_id] = sid
        return nid_sid_map

    @__init__.register
    def __init__proto(self, proto: static_scene_pb2.StaticScene):
        self.__init__(MetricGraph(proto.metric_graph),
                      [Signal(signal_proto) for signal_proto in proto.signals])

    def dump(self) -> 'static_scene_pb2.StaticScene':
        proto = static_scene_pb2.StaticScene()
        proto.metric_graph.CopyFrom(self.metric_graph.dump())
        for signal in self.signals.values():
            signal_proto = proto.signals.add()
            signal_proto.CopyFrom(signal.dump())
        return proto
    
    @property
    def metric_graph(self) -> MetricGraph:
        return self._metric_graph

    @property
    def signals(self) -> Mapping[SignalId, Signal]:
        return self._signals

    def signal(self, signal_id: SignalId) -> Signal:
        return self._signals[signal_id]

    def signal_on_node(self, node_id: str) -> Optional[Signal]:
        if node_id in self._node_signal_id_map:
            return self.signal(self._node_signal_id_map[node_id])
        return None

    def strict_eq(self, other: 'StaticScene') -> bool:
        if not self.metric_graph.strict_eq(other.metric_graph):
            return False
        if self.signals.keys() != other.signals.keys():
            return False
        for signal_id in self.signals:
            if not self.signal(signal_id).strict_eq(other.signal(signal_id)):
                return False
        return True

    def sub_scene(self, edges_id: Iterable[str]):
        n_metric_graph = self.metric_graph.sub_graph(edges_id)
        n_signals = []
        for signal in self.signals.values():
            if signal.state.control_node_id in n_metric_graph.nodes and \
                    len(n_metric_graph.exit_edges(signal.state.control_node_id)) > 0:
                n_signals.append(signal)
        return StaticScene(n_metric_graph, n_signals)
