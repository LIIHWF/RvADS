from adsv.utils.types import *
from adsv.utils import And
from adsv.semantic_model.metric_graph.proto import metric_graph_pb2
from .node import NodeId
from .edge import EdgeId


JunctionId = str


class Junction(ProtoClass):
    @singledispatchmethod
    def __init__(self, id_: JunctionId, edges_id: Iterable['EdgeId'],
                 entrance_nodes_id: Iterable[NodeId], exit_nodes_id: Iterable[NodeId]):
        self._id = id_
        self._edges_id = frozenset(edges_id)
        self._entrance_nodes_id = tuple(entrance_nodes_id)
        self._exit_nodes_id = tuple(exit_nodes_id)

    @__init__.register
    def __init__proto(self, proto: metric_graph_pb2.Junction):
        self.__init__(proto.id, [edge_id for edge_id in proto.edges_id],
                      [node_id for node_id in proto.entrance_nodes_id],
                      [node_id for node_id in proto.exit_nodes_id])

    def dump(self) -> 'metric_graph_pb2.Junction':
        proto = metric_graph_pb2.Junction()
        proto.id = self.id
        for edge_id in self.edges_id:
            proto.edges_id.append(edge_id)
        for node_id in self.entrance_nodes_id:
            proto.entrance_nodes_id.append(node_id)
        for node_id in self.exit_nodes_id:
            proto.exit_nodes_id.append(node_id)
        return proto

    @property
    def id(self):
        return self._id

    @property
    def edges_id(self) -> FrozenSet[EdgeId]:
        return self._edges_id

    @property
    def entrance_nodes_id(self) -> Tuple[NodeId, ...]:
        return self._entrance_nodes_id

    @property
    def entrance_num(self) -> int:
        return len(self.entrance_nodes_id)

    @property
    def exit_nodes_id(self) -> Tuple[NodeId, ...]:
        return self._exit_nodes_id

    @property
    def exit_num(self) -> int:
        return len(self.exit_nodes_id)

    def strict_eq(self, other: 'Junction'):
        return And(
            self.id == other.id,
            self.edges_id == other.edges_id,
            self.entrance_nodes_id == other.entrance_nodes_id,
            self.exit_nodes_id == other.exit_nodes_id
        )
