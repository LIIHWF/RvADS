from adsv.utils.types import *
from adsv.geometry.feature.region_reference_line import RegionReferenceLine, SLPoint
import adsv.geometry.proto.geometry_pb2 as geometry_pb2
from .polyline import Polyline
from .point import Vertex


class RegionPolyline(RegionReferenceLine, ProtoClass):
    def _init_region_polyline(self, reference_line: 'Polyline', left_boundary: 'Polyline', right_boundary: 'Polyline'):
        self._reference_line = reference_line
        self._left_boundary_line = left_boundary
        self._right_boundary_line = right_boundary
        self._init_bound_box(
            min(left_boundary.min_x, right_boundary.min_x) - 1,
            max(left_boundary.max_x, right_boundary.max_x) + 1,
            min(left_boundary.min_y, right_boundary.min_y) - 1,
            max(left_boundary.max_y, right_boundary.max_y) + 1
        )

    @singledispatchmethod
    def __init__(self, reference_line: 'Polyline', left_boundary: 'Polyline', right_boundary: 'Polyline'):
        self._init_region_polyline(reference_line, left_boundary, right_boundary)

    @__init__.register(geometry_pb2.RegionPolyline)
    def __init__proto(self, proto: 'geometry_pb2.RegionPolyline'):
        self._init_region_polyline(Polyline(proto.reference_line),
                                   Polyline(proto.left_boundary_line), Polyline(proto.right_boundary_line))

    def dump(self) -> 'geometry_pb2.RegionPolyline':
        proto = geometry_pb2.RegionPolyline()
        proto.reference_line.CopyFrom(self.reference_line.dump())
        proto.left_boundary_line.CopyFrom(self.left_boundary_line.dump())
        proto.right_boundary_line.CopyFrom(self.right_boundary_line.dump())
        return proto

    @property
    def length(self) -> Number:
        return self.reference_line.length

    @property
    def reference_line(self) -> Polyline:
        return self._reference_line

    @property
    def left_boundary_line(self):
        return self._left_boundary_line

    @property
    def right_boundary_line(self):
        return self._right_boundary_line

    def to_left_test(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        return self._reference_line.to_left_test(point, tolerance)

    def _within_boundary(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        return self._right_boundary_line.to_left_test(point, tolerance) and \
               not self._left_boundary_line.to_left_test(point, -tolerance)

    def within_region(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        return self.get_sl_by_xy(point.x, point.y, tolerance) is not None

    def get_sl_by_xy(self, x: 'Number', y: 'Number', tolerance: Number = 0) -> Optional['SLPoint']:
        point = Vertex(x, y)
        if self._within_boundary(point, tolerance):
            point_sl = self._reference_line.get_sl_by_xy(x, y)
            if point_sl is not None:
                return SLPoint(self, point_sl.s, point_sl.l)
        return None

    def get_xy_by_sl(self, s: 'Number', l: 'Number', tolerance: Number = 0) -> Optional['Vertex']:
        point = self._reference_line.get_xy_by_sl(s, l)
        if point is None:
            return None
        if self._within_boundary(point, tolerance):
            return point
        return None

    def __eq__(self, other: 'RegionPolyline'):
        return self.reference_line == other.reference_line and self.left_boundary_line == other.left_boundary_line and \
            self.right_boundary_line == other.right_boundary_line
