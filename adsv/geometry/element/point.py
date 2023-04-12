from math import sqrt, cos, sin, acos, pi
from adsv.utils.types import *
import adsv.geometry.proto.geometry_pb2 as geometry_pb2
from adsv.geometry.common import FLOAT_EPS
from .radian import Radian


class Vertex(ProtoClass):
    @singledispatchmethod
    def __init__(self, x: Number = 0, y: Number = 0):
        self._x = x
        self._y = y

    @__init__.register(dict)
    def __init__dict(self, config: dict):
        self.__init__(config['x'], config['y'])

    @__init__.register(geometry_pb2.Vertex)
    def __init__proto(self, proto: 'geometry_pb2.Vertex'):
        self.__init__(proto.x, proto.y)

    def dump(self) -> 'geometry_pb2.Vertex':
        proto = geometry_pb2.Vertex()
        proto.x = self.x
        proto.y = self.y
        return proto

    def to_dict(self) -> Mapping[str, Number]:
        return MappingProxyType({'x': self.x, 'y': self.y})

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = val

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = val

    def dis_sq_to(self, other: 'Vertex') -> Number:
        return (self.x - other.x) ** 2 + (self.y - other.y) ** 2

    def dis_to(self, other: 'Vertex') -> Number:
        return sqrt(self.dis_sq_to(other))

    @property
    def to_vec(self) -> 'Vector':
        return Vector(self.x, self.y)

    def __add__(self, vec: 'Vector') -> 'Vertex':
        return Vertex(self.x + vec.x, self.y + vec.y)

    def __sub__(self, vert: 'Vertex') -> 'Vector':
        return Vector(self.x - vert.x, self.y - vert.y)

    def __eq__(self, other) -> bool:
        return abs(self.x - other.x) < FLOAT_EPS and abs(self.y - other.y) < FLOAT_EPS

    def __hash__(self):
        return hash((self.x, self.y))

    def __str__(self) -> str:
        return f'({self.x}, {self.y})'

    def __repr__(self) -> str:
        return f'Vertex({self.x}, {self.y})'


class Vector(ProtoClass):
    @singledispatchmethod
    def __init__(self, x: Number = 0, y: Number = 0):
        self._x = x
        self._y = y

    @__init__.register(Vertex)
    def __init__vertex(self, start: 'Vertex', end: 'Vertex'):
        self.__init__(end.x - start.x, end.y - start.y)

    @__init__.register(dict)
    def __init__dict(self, config: dict):
        self.__init__(config['x'], config['y'])

    @__init__.register
    def __init__proto(self, proto: geometry_pb2.Vector):
        self.__init__(proto.x, proto.y)

    def dump(self) -> 'geometry_pb2.Vector':
        proto = geometry_pb2.Vector()
        proto.x = self.x
        proto.y = self.y
        return proto

    def to_dict(self) -> dict:
        return {'x': self.x, 'y': self.y}

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = val

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = val

    def add_x(self, x) -> 'Vector':
        return Vector(self.x + x, self.y)

    def add_y(self, y) -> 'Vector':
        return Vector(self.x, self.y + y)

    def copy(self) -> 'Vector':
        return Vector(self.x, self.y)

    @property
    def length(self) -> Number:
        return sqrt(self.x ** 2 + self.y ** 2)

    @property
    def unit(self) -> 'Vector':
        if self.length == 0:
            return Vector(0, 0)
        return self / self.length

    def rotate(self, r) -> 'Vector':
        return Vector(
            cos(r) * self.x - sin(r) * self.y,
            sin(r) * self.x + cos(r) * self.y
        )

    @property
    def left_unit(self) -> 'Vector':
        return self.rotate(pi / 2).unit

    @property
    def angle(self) -> 'Radian':
        unit = self.unit
        if unit.y >= 0:
            return Radian(acos(unit.x))
        else:
            return Radian(2 * pi - acos(unit.x))

    def angle_with(self, vec) -> Number:
        return acos(self.dot(vec) / self.length / vec.magnitude())

    def angle_with_in_xoy(self, vec) -> Number:
        if self.x * vec.y - self.y * vec.x > 0:
            return self.angle_with(vec)
        else:
            return - self.angle_with(vec)

    def dot(self, vec) -> 'Vector':
        return self.x * vec.x + self.y * vec.y

    def dis_to(self, vec) -> Number:
        return (self - vec).magnitude()

    @property
    def to_vert(self) -> 'Vertex':
        return Vertex(self.x, self.y)

    def __add__(self, vec) -> 'Vector':
        return Vector(self.x + vec.x, self.y + vec.y)

    def __neg__(self) -> 'Vector':
        return Vector(-self.x, -self.y)

    def __sub__(self, vec) -> 'Vector':
        return Vector(self.x - vec.x, self.y - vec.y)

    def __mul__(self, k) -> 'Vector':
        return Vector(k * self.x, k * self.y)

    def __rmul__(self, k) -> 'Vector':
        return Vector(k * self.x, k * self.y)

    def __truediv__(self, k) -> 'Vector':
        return Vector(self.x / k, self.y / k)

    def __eq__(self, other: 'Vector'):
        return self.x == other.x and self.y == other.y

    def __str__(self) -> str:
        return '({}, {})'.format(self.x, self.y)

    def __repr__(self) -> str:
        return 'Vector' + self.__str__()

    @classmethod
    def create_unit(cls, r: 'Radian') -> 'Vector':
        if isinstance(r, Radian):
            return cls.create_unit(r.r)
        else:
            return Vector(cos(r), sin(r))


def average_vertex(*vertices: Vertex) -> 'Vertex':
    sum_x = 0
    sum_y = 0
    for vert in vertices:
        sum_x += vert.x
        sum_y += vert.y
    return Vertex(sum_x / len(vertices), sum_y / len(vertices))
