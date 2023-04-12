from adsv.utils.types import *
from adsv.utils import And
from adsv.semantic_model.common.map_common import RJType, TurnType
from adsv.semantic_model.metric_graph.proto import metric_graph_pb2
from adsv.geometry import Polyline
from .node import NodeId


EdgeId = str


class Edge(ProtoClass):
    Id = str

    @singledispatchmethod
    def __init__(self, id_: EdgeId, source_id: NodeId, target_id: NodeId, length: Number,
                 rj_type: RJType, turn_type: TurnType, display_line: Optional[Polyline] = None):
        self._id = id_
        self._source_id = source_id
        self._target_id = target_id
        self._length = length
        self._rj_type = rj_type
        self._turn_type = turn_type
        self._display_line = display_line

    @__init__.register
    def __init__proto(self, proto: metric_graph_pb2.Edge):
        self.__init__(proto.id, proto.source_id, proto.target_id, proto.length,
                      RJType(proto.rj_type), TurnType(proto.turn_type),
                      Polyline(proto.display_line) if proto.HasField('display_line') else None)

    def dump(self) -> 'metric_graph_pb2.Edge':
        proto = metric_graph_pb2.Edge()
        proto.id = self.id
        proto.source_id = self.source_id
        proto.target_id = self.target_id
        proto.length = self.length
        proto.rj_type = self.rj_type.value
        proto.turn_type = self.turn_type.value
        if self.display_line is not None:
            proto.display_line.CopyFrom(self.display_line.dump())
        return proto

    @property
    def id(self) -> EdgeId:
        return self._id

    @property
    def source_id(self) -> NodeId:
        return self._source_id

    @property
    def target_id(self) -> NodeId:
        return self._target_id

    @property
    def length(self) -> Number:
        return self._length

    @property
    def rj_type(self) -> RJType:
        return self._rj_type

    def set_rj_type(self, rj_type: RJType):
        self._rj_type = rj_type

    @property
    def turn_type(self) -> TurnType:
        return self._turn_type

    @property
    def display_line(self) -> Optional[Polyline]:
        return self._display_line

    def strict_eq(self, other: 'Edge'):
        return And(
            self.id == other.id,
            self.source_id == other.source_id,
            self.target_id == other.target_id,
            self.length == other.length,
            self.turn_type == other.turn_type,
            self.rj_type == other.rj_type,
            self.display_line == other.display_line
        )

    def __eq__(self, other: 'Edge'):
        return self.id == other.id

    def __str__(self):
        return f'Edge({self.id}, {self.source_id}, {self.target_id}, {round(self.length, 3)})'

    def __hash__(self):
        return hash(self.id)

    def __repr__(self):
        return str(self)
