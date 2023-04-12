from adsv.utils.types import *
from adsv.semantic_model.static_scene import StaticScene
from .element.dynamic_scenario import DynamicScenario, DynamicScene, VehicleState
from adsv.semantic_model.scenario.proto import scenario_pb2
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration


class Scene:
    def __init__(self, static_scene: StaticScene, dynamic_scene: DynamicScene, waiting_time: Optional[Mapping[str, Number]]):
        self._static_scene = static_scene
        self._dynamic_scene = dynamic_scene
        self._waiting_time = waiting_time

    @property
    def static_scene(self) -> StaticScene:
        return self._static_scene

    @property
    def dynamic_scene(self) -> DynamicScene:
        return self._dynamic_scene

    @property
    def metric_graph(self):
        return self.static_scene.metric_graph

    @property
    def vehicles_id(self):
        return self.dynamic_scene.vehicles_state.keys()

    @property
    def traffic_lights_id(self):
        return self.dynamic_scene.traffic_lights_state.keys()

    def waiting_time(self, vehicle_id):
        if self._waiting_time is None:
            raise AttributeError
        return self._waiting_time[vehicle_id]


class Scenario(ProtoClass):
    @singledispatchmethod
    def __init__(self, scenario_configuration: ScenarioConfiguration, static_scene: StaticScene,
                 dynamic_scenario: DynamicScenario):
        self._scenario_configuration = scenario_configuration
        self._static_scene = static_scene
        self._dynamic_scenario = dynamic_scenario
        self._waiting_time = None
        self._sample_scene = self.scene(0)
        self._init_waiting_time()

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.Scenario):
        self.__init__(ScenarioConfiguration(proto.scenario_configuration), StaticScene(proto.static_scene),
                      DynamicScenario(proto.dynamic_scenario))

    def _init_waiting_time(self):
        self._waiting_time = [{vid: 0 for vid in self.vehicles_id}]
        for i in range(1, self.ticks_num):
            cur_waiting_time = dict()
            cur_dynamic_scene = self.dynamic_scenario.dynamic_scene(i)
            for vid in self.vehicles_id:
                v_state = cur_dynamic_scene.vehicle_state(vid)
                if v_state.at_stop_target:
                    cur_waiting_time[vid] = self._waiting_time[-1][vid] + self.time_interval
                else:
                    cur_waiting_time[vid] = 0
            self._waiting_time.append(cur_waiting_time)

    def dump(self) -> scenario_pb2.Scenario:
        proto = scenario_pb2.Scenario()
        proto.static_scene.CopyFrom(self.static_scene.dump())
        proto.scenario_configuration.CopyFrom(self.scenario_configuration.dump())
        proto.dynamic_scenario.CopyFrom(self.dynamic_scenario.dump())
        return proto

    @property
    def scenario_configuration(self) -> ScenarioConfiguration:
        return self._scenario_configuration

    @property
    def time_interval(self) -> Number:
        return self.scenario_configuration.time_interval

    @property
    def static_scene(self):
        return self._static_scene

    @property
    def dynamic_scenario(self):
        return self._dynamic_scenario

    def scene(self, tick: int):
        return Scene(self.static_scene, self.dynamic_scenario.dynamic_scene(tick),
                     None if self._waiting_time is None else self._waiting_time[tick])

    @cached_property
    def vehicles_id(self):
        return frozenset(self._sample_scene.dynamic_scene.vehicles_state.keys())

    @cached_property
    def traffic_lights_id(self):
        return frozenset(self._sample_scene.dynamic_scene.traffic_lights_state.keys())

    @property
    def ticks_num(self):
        return self.dynamic_scenario.ticks_num

    def strict_eq(self, other: 'Scenario') -> bool:
        return self.static_scene.strict_eq(other.static_scene) and \
               self.dynamic_scenario.vehicles_state_sequence == \
               other.dynamic_scenario.vehicles_state_sequence and \
               self.dynamic_scenario.traffic_lights_state_sequence == \
               other.dynamic_scenario.traffic_lights_state_sequence

    def sub_scenario(self, edges_id: Iterable[str]):
        return Scenario(self.scenario_configuration, self.static_scene.sub_scene(edges_id), self.dynamic_scenario)
