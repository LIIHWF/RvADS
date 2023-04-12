from adsv.utils.types import *
from adsv.semantic_model.static_scene import SignalId
from .vehicle import VehicleState, VehicleId
from .traffic_light import TrafficLightState
from adsv.semantic_model.scenario.proto import scenario_pb2


class DynamicScene:
    def __init__(self, vehicles_state: Mapping[VehicleId, VehicleState],
                 traffic_lights_state: Mapping[SignalId, TrafficLightState]):
        self._vehicles_state = vehicles_state
        self._traffic_lights_state = traffic_lights_state

    @property
    def vehicles_state(self) -> Mapping[VehicleId, VehicleState]:
        return self._vehicles_state

    @property
    def traffic_lights_state(self) -> Mapping[SignalId, TrafficLightState]:
        return self._traffic_lights_state

    def vehicle_state(self, vehicle_id: VehicleId) -> VehicleState:
        return self.vehicles_state[vehicle_id]

    def traffic_light_state(self, traffic_light_id: SignalId) -> TrafficLightState:
        return self.traffic_lights_state[traffic_light_id]


class DynamicScenario(ProtoClass):
    @singledispatchmethod
    def __init__(self, vehicles_state_sequence: Mapping[VehicleId, Iterable[VehicleState]],
                 traffic_lights_state_sequence: Mapping[SignalId, Iterable[TrafficLightState]]):
        self._vehicles_state_sequence = MappingProxyType({
            vehicle_id: tuple(state_sequence) for vehicle_id, state_sequence in vehicles_state_sequence.items()
        })
        self._traffic_lights_state_sequence = MappingProxyType({
            traffic_light_id: tuple(state_sequence)
            for traffic_light_id, state_sequence in traffic_lights_state_sequence.items()
        })
        self._ticks_num = self._get_ticks_num()

    def _get_ticks_num(self) -> int:
        ticks_num = None
        for state_sequence in chain(self.vehicles_state_sequence.values(), self.traffic_lights_state_sequence.values()):
            if ticks_num is None:
                ticks_num = len(state_sequence)
            elif ticks_num != len(state_sequence):
                raise ValueError('The length of state sequences is not equal')
        return ticks_num

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.DynamicScenario):
        self.__init__(
            {vehicle_id: [VehicleState(state_proto) for state_proto in proto.vehicles_state_sequence[vehicle_id].states]
             for vehicle_id in proto.vehicles_state_sequence},
            {traffic_light_id: [TrafficLightState(state_proto)
                                for state_proto in proto.traffic_lights_state_sequence[traffic_light_id].states]
             for traffic_light_id in proto.traffic_lights_state_sequence}
        )

    def dump(self) -> 'scenario_pb2.DynamicScenario':
        proto = scenario_pb2.DynamicScenario()
        for traffic_light_id, traffic_light_state_sequence in self.traffic_lights_state_sequence.items():
            state_sequence_proto = scenario_pb2.TrafficLightStateSequence()
            for state in traffic_light_state_sequence:
                state_proto = state_sequence_proto.states.add()
                state_proto.CopyFrom(state.dump())
            proto.traffic_lights_state_sequence[traffic_light_id].CopyFrom(state_sequence_proto)
        for vehicle_id, vehicle_state_sequence in self.vehicles_state_sequence.items():
            state_sequence_proto = scenario_pb2.VehicleStateSequence()
            for state in vehicle_state_sequence:
                state_proto = state_sequence_proto.states.add()
                state_proto.CopyFrom(state.dump())
            proto.vehicles_state_sequence[vehicle_id].CopyFrom(state_sequence_proto)
        return proto

    @property
    def ticks_num(self) -> int:
        return self._ticks_num

    @property
    def vehicles_state_sequence(self) -> Mapping[VehicleId, Tuple[VehicleState, ...]]:
        return self._vehicles_state_sequence

    @property
    def traffic_lights_state_sequence(self) -> Mapping[SignalId, Tuple[TrafficLightState, ...]]:
        return self._traffic_lights_state_sequence

    def dynamic_scene(self, tick: int) -> DynamicScene:
        return DynamicScene(
            MappingProxyType({vehicle_id: state_sequence[tick]
                              for vehicle_id, state_sequence in self.vehicles_state_sequence.items()}),
            MappingProxyType({traffic_light_id: state_sequence[tick]
                              for traffic_light_id, state_sequence in self.traffic_lights_state_sequence.items()})
        )


