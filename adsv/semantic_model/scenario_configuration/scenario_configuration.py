from adsv.utils.types import *
from adsv.semantic_model.scenario_configuration.proto import scenario_configuration_pb2


class Itinerary(ProtoClass):
    @singledispatchmethod
    def __init__(self, start_offset: Number, end_offset: Number, segment_id_seq):
        self._start_offset = start_offset
        self._end_offset = end_offset
        self._segment_id_seq = tuple(segment_id_seq)

    @__init__.register
    def __init__proto(self, proto: scenario_configuration_pb2.Itinerary):
        self.__init__(proto.start_offset, proto.end_offset, proto.segment_ids)

    def dump(self) -> scenario_configuration_pb2.Itinerary:
        proto = scenario_configuration_pb2.Itinerary()
        proto.start_offset = self.start_offset
        proto.end_offset = self.end_offset
        for segment_id in self.segment_id_seq:
            proto.segment_ids.append(
                segment_id
            )
        return proto

    @property
    def start_offset(self) -> float:
        return self._start_offset

    @property
    def end_offset(self) -> float:
        return self._end_offset

    @property
    def segment_id_seq(self) -> Tuple[str, ...]:
        return self._segment_id_seq


class VehicleConfiguration(ProtoClass):
    @singledispatchmethod
    def __init__(self, itinerary: Itinerary, init_speed: Number):
        self._itinerary = itinerary
        self._init_speed = init_speed

    @__init__.register
    def __init__proto(self, proto: scenario_configuration_pb2.VehicleConfiguration):
        self.__init__(Itinerary(proto.itinerary), proto.init_speed)

    def dump(self) -> scenario_configuration_pb2.VehicleConfiguration:
        proto = scenario_configuration_pb2.VehicleConfiguration()
        proto.itinerary.CopyFrom(self.itinerary.dump())
        proto.init_speed = self.init_speed
        return proto

    @property
    def itinerary(self) -> Itinerary:
        return self._itinerary

    @property
    def init_speed(self) -> float:
        return self._init_speed


class ScenarioConfiguration(ProtoClass):
    @singledispatchmethod
    def __init__(self, map_name: str, seed: int, vehicles_configuration: Mapping[str, VehicleConfiguration],
                 initialization_order: List[str], traffic_lights: Set[str], reverse_traffic_lights: bool, time_limit: Number, time_interval: Number):
        self._map_name = map_name
        self._seed = seed
        self._vehicles_configuration = vehicles_configuration
        self._initialization_order = tuple(initialization_order)
        self._traffic_lights = frozenset(traffic_lights)
        self._reverse_traffic_lights = reverse_traffic_lights
        self._time_limit = time_limit
        self._time_interval = time_interval

    @__init__.register
    def __init__proto(self, proto: scenario_configuration_pb2.ScenarioConfiguration):
        self.__init__(proto.map_name, proto.seed,
                      {vehicle_id: VehicleConfiguration(proto.vehicles_configuration[vehicle_id]) for vehicle_id in proto.vehicles_configuration},
                      [vehicle_id for vehicle_id in proto.initialization_order],
                      {tid for tid in proto.traffic_lights},
                      proto.reverse_traffic_lights,
                      proto.time_limit, proto.time_interval)

    @property
    def map_name(self) -> str:
        return self._map_name

    @property
    def vehicles_configuration(self) -> Mapping[str, VehicleConfiguration]:
        return self._vehicles_configuration

    @property
    def time_limit(self) -> float:
        return self._time_limit

    @property
    def seed(self) -> int:
        return self._seed

    @property
    def traffic_lights(self) -> FrozenSet[str]:
        return self._traffic_lights

    @property
    def reverse_traffic_lights(self) -> bool:
        return self._reverse_traffic_lights

    @property
    def initialization_order(self) -> Tuple[str, ...]:
        return self._initialization_order

    def set_time_interval(self, time_interval: Number):
        self._time_interval = time_interval

    @property
    def time_interval(self) -> float:
        return self._time_interval

    def dump(self) -> scenario_configuration_pb2.ScenarioConfiguration:
        proto = scenario_configuration_pb2.ScenarioConfiguration()
        proto.map_name = self.map_name
        proto.seed = self.seed
        proto.time_limit = self.time_limit
        proto.time_interval = self.time_interval
        for vehicle_id, config in self.vehicles_configuration.items():
            proto.vehicles_configuration[vehicle_id].CopyFrom(config.dump())
        for vehicle_id in self.initialization_order:
            proto.initialization_order.append(vehicle_id)
        for tid in self.traffic_lights:
            proto.traffic_lights.append(tid)
        proto.reverse_traffic_lights = self.reverse_traffic_lights
        return proto
