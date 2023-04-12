from adsv.utils.types import *
from adsv.tm2cl.ast.common import Expression, AtomicProposition


class Object(Expression):
    ...

class ObjectEqual(AtomicProposition):
    def __init__(self, object1: 'Object', object2: 'Object'):
        self.object1 = object1
        self.object2 = object2

    @property
    def sub_nodes(self) -> Tuple['Object', 'Object']:
        return self.object1, self.object2

    def apply_sub_nodes(self, object1: 'Object', object2: 'Object') -> 'ObjectEqual':
        return ObjectEqual(object1, object2)

    def __repr__(self):
        return f'ObjectEqual({self.object1}, {self.object2})'
