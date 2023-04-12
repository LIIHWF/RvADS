from adsv.utils.types import *
from .object import Object
from adsv.tm2cl.ast.common import Variable, StaticVariable, AstNode


class VehicleNode(Object):
    ...


class VehicleVariable(Variable, VehicleNode):
    def __init__(self, name: str):
        self._init_variable(name)

    @property
    def sub_nodes(self) -> Tuple:
        return ()

    def apply_sub_nodes(self) -> 'VehicleVariable':
        return VehicleVariable(self.name)

    def __repr__(self):
        return f'VehicleVariable({self.name})'


class VehicleValue(StaticVariable, VehicleNode):
    def __init__(self, id_: str):
        self._init_static_variable(id_)

    @property
    def sub_nodes(self) -> Iterable['AstNode']:
        return ()

    def apply_sub_nodes(self) -> 'VehicleValue':
        return VehicleValue(self.id)

    def __str__(self):
        return str(self.id)

    def __repr__(self):
        return f'VehicleValue({self.id})'
