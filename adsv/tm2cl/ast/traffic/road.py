from adsv.utils.types import *
from .position import PositionSet
from adsv.tm2cl.ast.common import StaticVariable, Variable, AstNode


class RoadNode(PositionSet):
    ...


class RoadVariable(Variable, RoadNode):
    def __init__(self, name: str):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'RoadVariable':
        return RoadVariable(self.name)

    def __str__(self):
        return f'RoadVariable({self.name})'


class RoadValue(StaticVariable, RoadNode):
    def __init__(self, id_: str):
        self._init_static_variable(id_)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'RoadValue':
        return RoadValue(self.id)

    def __str__(self):
        return f'RoadValue({self.id})'


class RoadEndpoint(PositionSet):
    def _init(self, road_node: 'RoadNode'):
        self.road_node = road_node

    def apply_sub_nodes(self, road_node: 'RoadNode') -> 'RoadEndpoint':
        return RoadEndpoint(road_node)

    @property
    def sub_nodes(self) -> Tuple['RoadNode']:
        return self.road_node,


class RoadEntrance(RoadEndpoint, StaticVariable):
    def __init__(self, road_node: 'RoadNode'):
        self._init(road_node)

    def apply_sub_nodes(self, road_node: 'RoadNode') -> 'RoadEntrance':
        return RoadEntrance(road_node)

    def __repr__(self):
        return f'RoadEntrance({self.road_node})'


class RoadExit(RoadEndpoint, StaticVariable):
    def __init__(self, road_node: 'RoadNode'):
        self._init(road_node)

    def apply_sub_nodes(self, road_node: 'RoadNode') -> 'RoadExit':
        return RoadExit(road_node)

    def __repr__(self):
        return f'RoadExit({self.road_node})'
