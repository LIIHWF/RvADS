from adsv.utils.types import *
from adsv.semantic_model.metric_graph import EdgeId
from adsv.semantic_model.scenario.proto import scenario_pb2


VehicleId = str


class Vector3(ProtoClass):
    @singledispatchmethod
    def __init__(self, x: Number, y: Number, z: Number):
        self._x = x
        self._y = y
        self._z = z

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.Vector3):
        self._x = proto.x
        self._y = proto.y
        self._z = proto.z

    def dump(self) -> scenario_pb2.Vector3:
        proto = scenario_pb2.Vector3()
        proto.x = self.x
        proto.y = self.y
        proto.z = self.z
        return proto

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def z(self):
        return self._z


class PhysicalState(ProtoClass):
    @singledispatchmethod
    def __init__(self, position: Vector3, speed: Vector3):
        self._position = position
        self._speed = speed

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.PhysicalState):
        self.__init__(Vector3(proto.position), Vector3(proto.speed))

    def dump(self) -> scenario_pb2.PhysicalState:
        proto = scenario_pb2.PhysicalState()
        proto.position.CopyFrom(self.position.dump())
        proto.speed.CopyFrom(self.speed.dump())
        return proto

    @property
    def position(self) -> Vector3:
        return self._position

    @property
    def speed(self) -> Vector3:
        return self._speed


class VehicleState(ProtoClass):
    @singledispatchmethod
    def __init__(self,
                 edge_id: EdgeId,
                 lane_order: int,
                 offset: Number,
                 longitudinal_speed: Number,
                 control_speed: Number,
                 longitudinal_acceleration: Number,
                 control_acceleration: Number,
                 target_speed: Number,
                 itinerary_index: int,
                 at_stop_target: bool,
                 reached_destination: bool,
                 turn: Number,
                 target_turn: Number,
                 lane_begin_offset: Number,
                 lane_end_offset: Number,
                 physical_state: PhysicalState):
        self._edge_id = edge_id
        self._offset = offset
        self._longitudinal_speed = longitudinal_speed
        self._control_speed = control_speed
        self._longitudinal_acceleration = longitudinal_acceleration
        self._control_acceleration = control_acceleration
        self._target_speed = target_speed
        self._itinerary_index = itinerary_index
        self._lane_order = lane_order
        self._at_stop_target = at_stop_target
        self._reached_destination = reached_destination
        self._turn = turn
        self._target_turn = target_turn
        self._lane_begin_offset = lane_begin_offset
        self._lane_end_offset = lane_end_offset
        self._physical_state = physical_state

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.VehicleState):
        self.__init__(proto.edge_id, proto.lane_order, proto.offset, proto.longitudinal_speed, proto.control_speed,
                      proto.longitudinal_acceleration, proto.control_acceleration, proto.target_speed, proto.itinerary_index,
                      proto.at_stop_target, proto.reached_destination, proto.turn, proto.target_turn, proto.lane_begin_offset, proto.lane_end_offset,
                      PhysicalState(proto.physical_state))

    def dump(self) -> 'scenario_pb2.VehicleState':
        proto = scenario_pb2.VehicleState()
        proto.edge_id = self.edge_id
        proto.offset = self.offset
        proto.longitudinal_speed = self.longitudinal_speed
        proto.longitudinal_acceleration = self.longitudinal_acceleration
        proto.control_speed = self.control_speed
        proto.control_acceleration = self.control_acceleration
        proto.target_speed = self.target_speed
        proto.itinerary_index = self._itinerary_index
        proto.lane_order = self.lane_order
        proto.at_stop_target = self.at_stop_target
        proto.reached_destination = self.reached_destination
        proto.turn = self.turn
        proto.target_turn = self.target_turn
        proto.lane_begin_offset = self.lane_begin_offset
        proto.lane_end_offset = self.lane_end_offset
        proto.physical_state.CopyFrom(self.physical_state.dump())
        return proto

    @property
    def physical_state(self) -> PhysicalState:
        return self._physical_state

    @property
    def lane_begin_offset(self) -> Number:
        return self._lane_begin_offset

    @property
    def lane_end_offset(self) -> Number:
        return self._lane_end_offset

    @property
    def turn(self) -> Number:
        return self._turn

    @property
    def target_turn(self) -> Number:
        return self._target_turn

    @property
    def target_speed(self) -> Number:
        return self._target_speed

    @property
    def itinerary_index(self) -> int:
        return self._itinerary_index

    @property
    def longitudinal_speed(self) -> Number:
        return self._longitudinal_speed

    @property
    def longitudinal_acceleration(self) -> Number:
        return self._longitudinal_acceleration

    @property
    def control_speed(self) -> Number:
        return self._control_speed

    @property
    def control_acceleration(self) -> Number:
        return self._control_acceleration

    @property
    def edge_id(self) -> EdgeId:
        return self._edge_id

    @property
    def offset(self) -> Number:
        return self._offset

    @property
    def at_stop_target(self) -> bool:
        return self._at_stop_target

    @property
    def reached_destination(self) -> bool:
        return self._reached_destination

    @property
    def lane_order(self) -> int:
        return self._lane_order

    def __eq__(self, other: 'VehicleState'):
        return self.edge_id == other.edge_id and abs(self.offset - other.offset) < 1e-2 and self.lane_order == other.lane_order

    def __str__(self):
        return f'VehicleState({self.edge_id}, {self.offset}, {self.lane_order})'
    
    def __repr__(self):
        return str(self)
