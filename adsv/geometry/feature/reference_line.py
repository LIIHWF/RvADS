from adsv.utils.types import *
from adsv.geometry.element.point import Vertex
from adsv.geometry.common import FLOAT_EPS


class SLPoint:
    def __init__(self, ref: 'ReferenceLine', s: Number, l: Number):
        self.s = s
        self.l = l
        self._ref = ref

    @property
    def d(self):
        return abs(self.l)

    @property
    def ref(self) -> 'ReferenceLine':
        return self._ref

    def __repr__(self):
        return f'SLPoint({self.ref}, {self.s}, {self.l})'

    def __str__(self):
        return self.__repr__()

    def __eq__(self, sl_point: 'SLPoint'):
        return self.ref == sl_point.ref and self.s == sl_point.s and self.l == sl_point.l


class ReferenceLine:
    def get_sl_by_xy(self, x: 'Number', y: 'Number') -> Optional['SLPoint']:
        raise NotImplementedError

    def get_xy_by_sl(self, s: 'Number', l: 'Number') -> Optional['Vertex']:
        raise NotImplementedError

    @property
    def length(self) -> Number:
        raise NotImplementedError

    @property
    def id(self) -> Optional[str]:
        return None

    def lerp(self, t: Number) -> 'Vertex':
        t = max(min(1 - FLOAT_EPS, t), FLOAT_EPS)
        return self.get_xy_by_sl(t * self.length, 0)

    def to_left_test(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        raise NotImplementedError
