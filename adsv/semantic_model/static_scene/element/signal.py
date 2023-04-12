from adsv.utils.types import *
from adsv.utils import And
from adsv.semantic_model.metric_graph import NodeId
from adsv.semantic_model.static_scene.proto import static_scene_pb2
from enum import Enum


SignalId = str


class SignalState(ProtoClass):
    @singledispatchmethod
    def __init__(self, control_node_id: NodeId):
        self._control_node_id = control_node_id

    @__init__.register
    def __init__proto(self, proto: static_scene_pb2.SignalState):
        self.__init__(proto.control_node_id)

    def dump(self) -> 'static_scene_pb2.SignalState':
        proto = static_scene_pb2.SignalState()
        proto.control_node_id = self.control_node_id
        return proto

    @property
    def control_node_id(self):
        return self._control_node_id

    def __eq__(self, other: 'SignalState'):
        return self.control_node_id == other.control_node_id

    def __str__(self):
        return f'SignalState(control_node_id=\'{self.control_node_id}\')'


SignalType = Enum('SignalType', {name: id_ for name, id_ in static_scene_pb2.SignalType.items()})


class Signal(ProtoClass):
    @singledispatchmethod
    def __init__(self, id_: SignalId, signal_type: SignalType, state: SignalState):
        self._id = id_
        self._signal_type = signal_type
        self._state = state

    @__init__.register
    def __init__proto(self, proto: static_scene_pb2.Signal):
        self.__init__(proto.id, SignalType(proto.signal_type), SignalState(proto.state))

    def dump(self) -> 'static_scene_pb2.Signal':
        proto = static_scene_pb2.Signal()
        proto.id = self.id
        proto.signal_type = self.signal_type.value
        proto.state.CopyFrom(self.state.dump())
        return proto

    @property
    def id(self) -> SignalId:
        return self._id

    @property
    def signal_type(self) -> SignalType:
        return self._signal_type

    @property
    def state(self) -> SignalState:
        return self._state

    def __eq__(self, other: 'Signal'):
        return self.id == other.id

    def strict_eq(self, other: 'Signal', check_id: bool = False) -> bool:
        if check_id and self.id != other.id:
            return False
        return And(self.signal_type == other.signal_type, self.state == other.state)
