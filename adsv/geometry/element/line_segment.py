from adsv.utils.types import *
from adsv.utils import And
from adsv.geometry.common import lerp
import adsv.geometry.proto.geometry_pb2 as geometry_pb2
from adsv.geometry.feature.reference_line import ReferenceLine, SLPoint
from adsv.geometry.feature.bound_box import BoundBox
from .point import Vertex, Vector


class DisInfo(NamedTuple):
    distance: Number
    point: Vertex


class LineSegment(BoundBox, ProtoClass, ReferenceLine):
    @singledispatchmethod
    def __init__(self, v1: 'Vertex', v2: 'Vertex'):
        self.v1: Vertex = v1
        self.v2: Vertex = v2
        self._init_bound_box(
            min(v1.x, v2.x),
            max(v1.x, v2.x),
            min(v1.y, v2.y),
            max(v1.y, v2.y)
        )

    @__init__.register
    def __init__dict(self, config: dict):
        self.__init__(Vertex(config['v1']), Vertex(config['v2']))

    @__init__.register
    def __init__proto(self, proto: geometry_pb2.LineSegment):
        self.__init__(Vertex(proto.v1), Vertex(proto.v2))

    def dump(self) -> 'geometry_pb2.LineSegment':
        proto = geometry_pb2.LineSegment()
        proto.v1.CopyFrom(self.v1.dump())
        proto.v2.CopyFrom(self.v2.dump())
        return proto

    def to_dict(self) -> Mapping:
        return MappingProxyType({'v1': self.v1.to_dict(), 'v2': self.v2.to_dict()})

    @property
    def length(self) -> Number:
        return self.v1.dis_to(self.v2)

    @property
    def vec(self) -> Vector:
        return Vector(self.v2.x - self.v1.x, self.v2.y - self.v1.y)

    @property
    def unit(self) -> Vector:
        return self.vec.unit

    def lerp(self, t: Number) -> Vertex:
        return self.v1 + self.vec * t

    def inner_to_left_test(self, point: 'Vertex') -> bool:
        return self.v1.x * self.v2.y - self.v1.y * self.v2.x + \
               self.v2.x * point.y - self.v2.y * point.x + \
               point.x * self.v1.y - point.y * self.v1.x > 0

    def to_left_test(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        return self.get_sl_by_xy(point.x, point.y).l > -tolerance

    def cover_in_parallel(self, point) -> bool:
        if LineSegment(self.v1, self.v1 + self.vec.left_unit).inner_to_left_test(point) ^ \
                LineSegment(self.v2, self.v2 + self.vec.left_unit).inner_to_left_test(point):
            return True
        else:
            return False

    def dis_to_point(self, point: Vertex) -> DisInfo:
        cross = (self.v2.x - self.v1.x) * (point.x - self.v1.x) + (self.v2.y - self.v1.y) * (point.y - self.v1.y)
        if cross <= 0:
            result = DisInfo(point.dis_to(self.v1), Vertex(self.v1.x, self.v1.y))
            return result
        d2 = (self.v2.x - self.v1.x) ** 2 + (self.v2.y - self.v1.y) ** 2
        if cross >= d2:
            result = DisInfo(point.dis_to(self.v2), Vertex(self.v2.x, self.v2.y))
            return result

        r = cross / d2
        closest_point = Vertex(
            lerp(self.v1.x, self.v2.x, r),
            lerp(self.v1.y, self.v2.y, r)
        )
        result = DisInfo(point.dis_to(closest_point), closest_point)
        return result

    def get_sl_by_xy(self, x: 'Number', y: 'Number') -> Optional[SLPoint]:
        point = Vertex(x, y)
        if self.cover_in_parallel(point):
            dis_info = self.dis_to_point(point)
            s = dis_info.point.dis_to(self.v1)
            l = dis_info.distance
            if not self.inner_to_left_test(point):
                l = -l
            return SLPoint(self, s, l)
        else:
            return None

    def get_xy_by_sl(self, s: 'Number', l: 'Number') -> Optional['Vertex']:
        if s > self.length or s < 0: return None
        return self.v1 + self.vec.unit * s + self.vec.left_unit * l

    def check_intersect(self, other: 'LineSegment') -> bool:
        return check_intersect(self, other)

    def intersect_point(self, other: 'LineSegment') -> Optional['Vertex']:
        return intersect_point(self, other)

    def __eq__(self, other: 'LineSegment'):
        return self.v1 == other.v1 and self.v2 == other.v2

    def __str__(self) -> str:
        return 'Segment({}, {})'.format(str(self.v1), str(self.v2))

    def __repr__(self) -> str:
        return 'Segment({}, {})'.format(self.v1.__repr__(), self.v2.__repr__())


def check_intersect(seg1: 'LineSegment', seg2: 'LineSegment') -> bool:
    p1 = (seg1.v1.x, seg1.v1.y)
    p2 = (seg1.v2.x, seg1.v2.y)
    p3 = (seg2.v1.x, seg2.v1.y)
    p4 = (seg2.v2.x, seg2.v2.y)

    def cross(v1, v2, v3):
        x1 = v2[0] - v1[0]
        y1 = v2[1] - v1[1]
        x2 = v3[0] - v1[0]
        y2 = v3[1] - v1[1]
        return x1 * y2 - x2 * y1

    if (And(max(p1[0], p2[0]) >= min(p3[0], p4[0]),
            max(p3[0], p4[0]) >= min(p1[0], p2[0]),
            max(p1[1], p2[1]) >= min(p3[1], p4[1]),
            max(p3[1], p4[1]) >= min(p1[1], p2[1]))):
        if (cross(p1, p2, p3) * cross(p1, p2, p4) <= 0
                and cross(p3, p4, p1) * cross(p3, p4, p2) <= 0):
            ret = True
        else:
            ret = False
    else:
        ret = False
    return ret


def intersect_point(seg1: 'LineSegment', seg2: 'LineSegment') -> Optional[Vertex]:
    if not check_intersect(seg1, seg2):
        return None
    point_is_exist = False
    x = y = 0
    x1, y1, x2, y2 = seg1.v1.x, seg1.v1.y, seg1.v2.x, seg1.v2.y
    x3, y3, x4, y4 = seg2.v1.x, seg2.v1.y, seg2.v2.x, seg2.v2.y

    if (x2 - x1) == 0:
        k1 = None
        b1 = 0
    else:
        k1 = (y2 - y1) * 1.0 / (x2 - x1)
        b1 = y1 * 1.0 - x1 * k1 * 1.0
    if (x4 - x3) == 0:
        k2 = None
        b2 = 0
    else:
        k2 = (y4 - y3) * 1.0 / (x4 - x3)
        b2 = y3 * 1.0 - x3 * k2 * 1.0

    if k1 is None:
        if k2 is not None:
            x = x1
            y = k2 * x1 + b2
            point_is_exist = True
    elif k2 is None:
        x = x3
        y = k1 * x3 + b1
    elif not k2 == k1:
        x = (b2 - b1) * 1.0 / (k1 - k2)
        y = k1 * x * 1.0 + b1 * 1.0
        point_is_exist = True

    if point_is_exist:
        return Vertex(x, y)
    else:
        return None
