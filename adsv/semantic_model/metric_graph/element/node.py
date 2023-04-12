from adsv.utils.types import *
from adsv.geometry import Vertex
from adsv.semantic_model.metric_graph.proto import metric_graph_pb2


NodeId = str


class Node(ProtoClass):
    @singledispatchmethod
    def __init__(self, id_: NodeId, display_position: Optional['Vertex'] = None):
        self._id = id_
        self._display_position = display_position

    @__init__.register
    def __init__proto(self, proto: metric_graph_pb2.Node):
        self.__init__(proto.id, Vertex(proto.display_position) if proto.HasField('display_position') else None)

    def dump(self) -> 'metric_graph_pb2.Node':
        proto = metric_graph_pb2.Node()
        proto.id = self.id
        if self.display_position is not None:
            proto.display_position.CopyFrom(self.display_position.dump())
        return proto

    @property
    def display_position(self):
        return self._display_position

    @property
    def id(self) -> NodeId:
        return self._id

    def strict_eq(self, other: 'Node', check_id: bool = False) -> bool:
        if check_id and self.id != other.id:
            return False
        return self.display_position == other.display_position

    def __eq__(self, other: 'Node'):
        return self.id == other.id

    def __repr__(self):
        return f'Node({self.id})'

    def __str__(self):
        return f'Node({self.id})'

    def __hash__(self):
        return hash(self.id)
