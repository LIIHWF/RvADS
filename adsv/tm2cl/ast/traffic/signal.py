from adsv.utils.types import *
from adsv.tm2cl.ast.common import Variable, StaticVariable, M2clFormula, Expression, StaticValue, AstNode, AtomicProposition
from adsv.semantic_model.scenario import TrafficLightColor
from .object import Object
from abc import abstractmethod


class SignalNode(Object):
    ...


class StopSignNode(SignalNode):
    ...


class StopSignVariable(Variable, StopSignNode):
    def __init__(self, name: str):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'StopSignVariable':
        return StopSignVariable(self.name)

    def __repr__(self):
        return f'StopSignVariable({self.name})'


class StopSignValue(StaticVariable, StopSignNode):
    def __init__(self, id_: str):
        self._init_static_variable(id_)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'StopSignValue':
        return StopSignValue(self.id)

    def __repr__(self):
        return f'StopSignValue({self.id})'


class TrafficLightNode(SignalNode):
    ...


class TrafficLightVariable(Variable, TrafficLightNode):
    def __init__(self, name: str):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'TrafficLightVariable':
        return TrafficLightVariable(self.name)

    def __repr__(self):
        return f'TrafficLightVariable({self.name})'


class TrafficLightValue(StaticVariable, TrafficLightNode):
    def __init__(self, id_: str):
        self._init_static_variable(id_)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'TrafficLightValue':
        return TrafficLightValue(self.id)

    def __repr__(self):
        return f'TrafficLightValue({self.id})'


class TrafficLightColorNode(Expression):
    ...


class TrafficLightColorVariable(Variable, TrafficLightColorNode):
    def __init__(self, name):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'TrafficLightColorVariable':
        return TrafficLightColorVariable(self.name)

    def __repr__(self):
        return f'TrafficLightColorVariable({self.name})'


class TrafficLightColorValue(StaticValue, TrafficLightColorNode):
    def __init__(self, color: TrafficLightColor):
        self._init_static_value(color)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'TrafficLightColorValue':
        return TrafficLightColorValue(self.value)

    def __repr__(self):
        return f'TrafficLightColorValue({self.value.name})'


class TrafficLightColorConstraint(AtomicProposition):
    def __init__(self, traffic_light_node: 'TrafficLightNode', color: 'TrafficLightColorNode'):
        self.traffic_light_node = traffic_light_node
        self.color = color

    @property
    def sub_nodes(self) -> Tuple['TrafficLightNode', 'TrafficLightColorNode']:
        return self.traffic_light_node, self.color

    def apply_sub_nodes(self, traffic_light_node: 'TrafficLightNode',
                        color: 'TrafficLightColorNode') -> 'TrafficLightColorConstraint':
        return TrafficLightColorConstraint(traffic_light_node, color)

    def __repr__(self):
        return f'TrafficLightColorConstraint({self.traffic_light_node}, {self.color})'
