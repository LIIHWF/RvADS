from adsv.utils.types import *
from adsv.tm2cl.ast.common import AtomicProposition
from adsv.tm2cl.ast.arithmetic import ArithmeticExpression
from adsv.tm2cl.ast.traffic.vehicle import VehicleNode
from .object import Object
from .position import PositionSet


class At(AtomicProposition):
    def __init__(self, object_: Object, position_set: PositionSet):
        self.object = object_
        self.position_set = position_set

    @property
    def sub_nodes(self) -> Tuple[Object, PositionSet]:
        return self.object, self.position_set

    def apply_sub_nodes(self, object_: Object, position_set: PositionSet) -> 'At':
        return At(object_, position_set)

    def __str__(self):
        return f'[{str(self.object)} @ {str(self.position_set)}]'

    def __repr__(self):
        return f'At({self.object}, {self.position_set})'


class Dist(ArithmeticExpression):
    def __init__(self, from_obj: Object, to_obj: Object):
        self.from_obj = from_obj
        self.to_obj = to_obj

    @property
    def sub_nodes(self) -> Tuple[Object, Object]:
        return self.from_obj, self.to_obj

    def apply_sub_nodes(self, from_obj: Object, to_obj: Object) -> 'Dist':
        return Dist(from_obj, to_obj)

    def __repr__(self):
        return f'Meet({self.from_obj}, {self.to_obj})'


class WaitingTime(ArithmeticExpression):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple[VehicleNode]:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: VehicleNode) -> 'WaitingTime':
        return WaitingTime(vehicle)

    def __str__(self):
        return f'wt({str(self.vehicle)})'

    def __repr__(self):
        return f'WaitingTime({self.vehicle})'


class Speed(ArithmeticExpression):
    def __init__(self, vehicle: VehicleNode):
        self.vehicle = vehicle

    @property
    def sub_nodes(self) -> Tuple['VehicleNode']:
        return self.vehicle,

    def apply_sub_nodes(self, vehicle: 'VehicleNode') -> 'Speed':
        return Speed(vehicle)

    def __repr__(self):
        return f'Speed({self.vehicle})'
