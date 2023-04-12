from math import pi
from adsv.utils.types import *
from adsv.geometry.common import FLOAT_EPS
import adsv.geometry.proto.geometry_pb2 as geometry_pb2


class Radian(ProtoClass):
    @singledispatchmethod
    def __init__(self, r: Number = 0):
        self._r = (r + (-r // (2 * pi) + 1) * 2 * pi) % (2 * pi)

    @__init__.register(dict)
    def __init__config(self, config: dict):
        r = config['r']
        self.__init__(r)

    @__init__.register(geometry_pb2.Radian)
    def __init__proto(self, proto: 'geometry_pb2.Radian'):
        self.__init__(proto.r)

    def dump(self) -> 'geometry_pb2.Radian':
        proto = geometry_pb2.Radian()
        proto.r = self.r
        return proto

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, r):
        self.__init__(r)

    def to_dict(self) -> dict:
        return {'r': self.r}

    def rotate(self, r) -> None:
        self.r = (self.r + r + (-r // (2 * pi) + 1) * 2 * pi) % (2 * pi)

    @property
    def angle(self) -> Number:
        return self.r / pi * 180

    def __eq__(self, other: 'Radian'):
        return abs(self.r - other.r) < FLOAT_EPS

    def __add__(self, r: Union['Radian', Number]) -> 'Radian':
        if isinstance(r, Radian):
            return Radian(self.r + r.r)
        else:
            return Radian(self.r + r)

    def __sub__(self, r) -> 'Radian':
        return self.__add__(-r)

    def __neg__(self) -> 'Radian':
        return Radian(-self.r)

    def __repr__(self) -> str:
        return f'{self.r} rad'

    def __str__(self) -> str:
        return f'{self.r} rad'
