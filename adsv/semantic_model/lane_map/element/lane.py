from adsv.utils.types import *
from adsv.utils import And
from adsv.geometry import RegionPolyline, Polyline
from adsv.semantic_model.common.map_common import RJType, TurnType
from adsv.semantic_model.lane_map.proto import lane_map_pb2
from enum import Enum


# LaneId = NewType('LaneId', str)
LaneId = str
LaneBoundType = Enum('LaneBoundType', {name: id_ for name, id_ in lane_map_pb2.Lane.BoundType.items()})


class Lane(RegionPolyline):
    Id = LaneId
    BoundType = LaneBoundType

    @singledispatchmethod
    def __init__(self, id_: LaneId, predecessors_id: Iterable[LaneId], successors_id: Iterable[LaneId],
                 left_forward_neighbor_id: Optional[LaneId], right_forward_neighbor_id: Optional[LaneId],
                 left_reverse_neighbor_id: Optional[LaneId], right_reverse_neighbor_id: Optional[LaneId],
                 left_boundary_type: LaneBoundType, right_boundary_type: LaneBoundType,
                 rj_type_: RJType, turn_type: TurnType,
                 reference_line: Polyline, left_boundary_line: Polyline, right_boundary_line: Polyline,
                 extend_length: Number = 0
                 ):
        self._id = id_
        self._left_forward_neighbor_id, self._right_forward_neighbor_id = \
            left_forward_neighbor_id, right_forward_neighbor_id
        self._left_reverse_neighbor_id, self._right_reverse_neighbor_id = \
            left_reverse_neighbor_id, right_reverse_neighbor_id
        self._left_boundary_type, self._right_boundary_type = \
            left_boundary_type, right_boundary_type
        self._predecessors_id = frozenset(predecessors_id)
        self._successors_id = frozenset(successors_id)
        self._rj_type = rj_type_
        self._turn_type = turn_type
        super().__init__(reference_line.extend(extend_length),
                         left_boundary_line.extend(extend_length), right_boundary_line.extend(extend_length))

    @__init__.register
    def __init__proto(self, proto: lane_map_pb2.Lane):
        self.__init__(
            proto.id, [pid for pid in proto.predecessors_id], [sid for sid in proto.successors_id],
            proto.left_forward_neighbor_id if proto.HasField('left_forward_neighbor_id') else None,
            proto.right_forward_neighbor_id if proto.HasField('right_forward_neighbor_id') else None,
            proto.left_reverse_neighbor_id if proto.HasField('left_reverse_neighbor_id') else None,
            proto.right_reverse_neighbor_id if proto.HasField('right_reverse_neighbor_id') else None,
            LaneBoundType(proto.left_boundary_type), LaneBoundType(proto.right_boundary_type),
            RJType(proto.rj_type), TurnType(proto.turn_type), Polyline(proto.region_polyline.reference_line),
            Polyline(proto.region_polyline.left_boundary_line), Polyline(proto.region_polyline.right_boundary_line)
        )

    def dump(self) -> 'lane_map_pb2.Lane':
        proto = lane_map_pb2.Lane()
        proto.id = self.id
        proto.rj_type = self.rj_type.value
        for predecessor_id in self.predecessors_id:
            proto.predecessors_id.append(predecessor_id)
        for successor_id in self.successors_id:
            proto.successors_id.append(successor_id)
        if self.left_forward_neighbor_id is not None:
            proto.left_forward_neighbor_id = self.left_forward_neighbor_id
        if self.right_forward_neighbor_id is not None:
            proto.right_forward_neighbor_id = self.right_forward_neighbor_id
        if self.left_reverse_neighbor_id is not None:
            proto.left_reverse_neighbor_id = self.left_reverse_neighbor_id
        if self.right_reverse_neighbor_id is not None:
            proto.right_reverse_neighbor_id = self.right_reverse_neighbor_id
        proto.left_boundary_type = self.left_boundary_type.value
        proto.right_boundary_type = self.right_boundary_type.value
        proto.turn_type = self.turn_type.value
        proto.region_polyline.CopyFrom(super().dump())
        return proto

    @property
    def length(self):
        return self.reference_line.length

    @property
    def id(self) -> LaneId:
        return self._id

    @property
    def rj_type(self) -> RJType:
        return self._rj_type

    @property
    def turn_type(self) -> TurnType:
        return self._turn_type

    @property
    def predecessors_id(self) -> FrozenSet[LaneId]:
        return self._predecessors_id

    @property
    def successors_id(self) -> FrozenSet[LaneId]:
        return self._successors_id

    @property
    def left_forward_neighbor_id(self) -> Optional[LaneId]:
        return self._left_forward_neighbor_id

    @property
    def right_forward_neighbor_id(self) -> Optional[LaneId]:
        return self._right_forward_neighbor_id

    @property
    def left_reverse_neighbor_id(self) -> Optional[LaneId]:
        return self._left_reverse_neighbor_id

    @property
    def right_reverse_neighbor_id(self) -> Optional[LaneId]:
        return self._right_reverse_neighbor_id

    @property
    def left_boundary_type(self) -> LaneBoundType:
        return self._left_boundary_type

    @property
    def right_boundary_type(self) -> LaneBoundType:
        return self._right_boundary_type

    def __eq__(self, other: 'Lane') -> bool:
        return self.id == other.id

    def strict_eq(self, other: 'Lane', check_id: bool = False):
        return And(not check_id or self.id == other.id,
                   self.rj_type == other.rj_type,
                   self.predecessors_id == other.predecessors_id,
                   self.successors_id == other.successors_id,
                   self.left_forward_neighbor_id == other.left_forward_neighbor_id,
                   self.right_forward_neighbor_id == other.right_forward_neighbor_id,
                   self.left_reverse_neighbor_id == other.left_reverse_neighbor_id,
                   self.right_reverse_neighbor_id == other.right_reverse_neighbor_id,
                   self.left_boundary_type == other.left_boundary_type,
                   self.right_boundary_type == other.right_boundary_type,
                   self.turn_type == other.turn_type,
                   self.reference_line == other.reference_line,
                   self.left_boundary_line == other.left_boundary_line,
                   self.right_boundary_line == other.right_boundary_line)

    def __repr__(self):
        return f'Lane({self.id})'

    def __str__(self):
        return f'Lane({self.id})'

    def __hash__(self):
        return hash(self.id)
