from .edge import EdgeId
from .node import NodeId
from adsv.utils.types import *
from adsv.utils import And
from adsv.semantic_model.metric_graph.proto import metric_graph_pb2


RoadId = str


class Road(ProtoClass):
    Id = RoadId

    @singledispatchmethod
    def __init__(self, id_: RoadId, edge_id_sequence: Iterable['EdgeId'], entrance_id: NodeId, exit_id: NodeId):
        self._id = id_
        self._edge_id_sequence = tuple(edge_id_sequence)
        self._entrance_id: NodeId = entrance_id
        self._exit_id: NodeId = exit_id

    @__init__.register
    def __init__proto(self, proto: metric_graph_pb2.Road):
        self.__init__(proto.id, [edge_id for edge_id in proto.edge_id_sequence], proto.entrance_id, proto.exit_id)

    def dump(self) -> 'metric_graph_pb2.Road':
        proto = metric_graph_pb2.Road()
        proto.id = self.id
        for edge_id in self.edge_id_sequence:
            proto.edge_id_sequence.append(edge_id)
        proto.entrance_id = self.entrance_id
        proto.exit_id = self.exit_id
        return proto

    @property
    def id(self) -> RoadId:
        return self._id

    @property
    def edge_id_sequence(self) -> Tuple[EdgeId, ...]:
        return self._edge_id_sequence

    @property
    def entrance_id(self) -> NodeId:
        return self._entrance_id

    @property
    def exit_id(self) -> NodeId:
        return self._exit_id

    def strict_eq(self, other: 'Road'):
        return And(
            self.id == other.id,
            self.entrance_id == other.entrance_id,
            self.exit_id == other.exit_id,
            self.edge_id_sequence == other.edge_id_sequence
        )

    def __eq__(self, other: 'Road'):
        return self.id == other.id

    def __hash__(self):
        return hash(self.id)
