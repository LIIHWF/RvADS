from adsv.utils.types import *
from adsv.semantic_model.scenario.proto import scenario_pb2
from enum import Enum


TrafficLightColor = Enum('TrafficLightColor', {name: id_ for name, id_ in scenario_pb2.TrafficLightState.Color.items()})


class TrafficLightState(ProtoClass):
    @singledispatchmethod
    def __init__(self, color: TrafficLightColor):
        self._color = color

    @__init__.register
    def __init__proto(self, proto: scenario_pb2.TrafficLightState):
        self.__init__(TrafficLightColor(proto.color))

    def dump(self) -> 'scenario_pb2.TrafficLightState':
        proto = scenario_pb2.TrafficLightState()
        proto.color = self.color.value
        return proto

    @property
    def color(self) -> TrafficLightColor:
        return self._color

    def __eq__(self, other: 'TrafficLightState'):
        return self.color == other.color

    def __str__(self):
        return f'TrafficLightState({self.color})'

    def __repr__(self):
        return str(self)
