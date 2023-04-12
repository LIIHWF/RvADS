from adsv.utils.types import *
from adsv.tm2cl.ast.common import AtomicProposition
from adsv.tm2cl.ast.arithmetic import ArithmeticExpression
from .object import Object
from .position import PositionSet
from .junction import JunctionEntranceValue, JunctionEntranceVariable, JunctionExitValue, JunctionExitVariable
from .vehicle import VehicleNode


JunctionEndpointType = Union[JunctionEntranceValue, JunctionEntranceVariable, JunctionExitValue, JunctionExitVariable]

class Opposite(AtomicProposition):
    def __init__(self, position1: JunctionEndpointType, position2: JunctionEndpointType):
        self.position1 = position1
        self.position2 = position2

    @property
    def sub_nodes(self) -> Tuple[JunctionEndpointType, JunctionEndpointType]:
        return self.position1, self.position2

    def apply_sub_nodes(self, position1: JunctionEndpointType, position2: JunctionEndpointType) -> 'Opposite':
        return Opposite(position1, position2)

    def __repr__(self):
        return f'Opposite({self.position1}, {self.position2})'


class RightOf(AtomicProposition):
    def __init__(self, position1: JunctionEndpointType, position2: JunctionEndpointType):
        self.position1 = position1
        self.position2 = position2

    @property
    def sub_nodes(self) -> Tuple[JunctionEndpointType, JunctionEndpointType]:
        return self.position1, self.position2

    def apply_sub_nodes(self, position1: JunctionEndpointType, position2: JunctionEndpointType) -> 'RightOf':
        return RightOf(position1, position2)

    def __repr__(self):
        return f'RightOf({self.position1}, {self.position2})'


class TurnRight(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return TurnRight(vehicle)

    def __repr__(self):
        return f'TurnRight({self.vehicle})'


class TurnLeft(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return TurnLeft(vehicle)

    def __repr__(self):
        return f'TurnLeft({self.vehicle})'


class GoStraight(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return GoStraight(vehicle)

    def __repr__(self):
        return f'GoStraight({self.vehicle})'


class NextTurnLeft(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return NextTurnLeft(vehicle)

    def __repr__(self):
        return f'NextTurnLeft({self.vehicle})'


class NextTurnRight(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return NextTurnRight(vehicle)

    def __repr__(self):
        return f'NextTurnRight({self.vehicle})'


class NextGoStraight(AtomicProposition):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode):
        return NextGoStraight(vehicle)

    def __repr__(self):
        return f'NextGoStraight({self.vehicle})'
