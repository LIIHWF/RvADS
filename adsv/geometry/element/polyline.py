from adsv.utils.types import *
from .point import Vertex
import adsv.geometry.proto.geometry_pb2 as geometry_pb2
from adsv.geometry.feature.reference_line import ReferenceLine, SLPoint
from adsv.geometry.feature.bound_box import BoundBox
from .line_segment import LineSegment
from .point import average_vertex


class Polyline(ProtoClass, ReferenceLine, BoundBox):
    @singledispatchmethod
    def __init__(self, *vertices: 'Vertex'):
        self._vertices = vertices
        self._line_segments: List[LineSegment] = []
        pre_vertex = None
        min_x, max_x, min_y, max_y = INF, -INF, INF, -INF
        self._length = 0
        vertex_number = 0
        for vertex in vertices:
            vertex_number += 1
            if pre_vertex is None:
                pre_vertex = vertex
            else:
                line_segment = LineSegment(pre_vertex, vertex)
                self._length += line_segment.length
                self._line_segments.append(line_segment)
                min_x = min(min_x, line_segment.min_x)
                min_y = min(min_y, line_segment.min_y)
                max_x = max(max_x, line_segment.max_x)
                max_y = max(max_y, line_segment.max_y)
                pre_vertex = vertex
        if vertex_number < 2:
            raise ValueError("Polyline should be constructed by at least 2 vertices")
        self._line_segments = tuple(self._line_segments)
        self._init_bound_box(min_x, max_x, min_y, max_y)

    @__init__.register(list)
    @__init__.register(tuple)
    def __init__iterable(self, vertices: Iterable['Vertex']):
        self.__init__(*vertices)

    @__init__.register(geometry_pb2.Polyline)
    def __init__proto(self, proto: 'geometry_pb2.Polyline'):
        vertices = [Vertex(vert_proto) for vert_proto in proto.vertices]
        self.__init__(vertices)

    def dump(self) -> 'geometry_pb2.Polyline':
        proto = geometry_pb2.Polyline()
        for vertex in self.vertices:
            proto.vertices.append(vertex.dump())
        return proto

    @property
    def length(self) -> Number:
        return self._length

    @property
    def line_segments(self) -> Tuple['LineSegment', ...]:
        return self._line_segments

    @property
    def vertices(self):
        return self._vertices

    @property
    def vertices_num(self):
        return len(self._vertices)

    def get_xy_by_sl(self, s: 'Number', l: 'Number') -> Optional['Vertex']:
        idx = 0
        while idx < len(self._line_segments) and s > self._line_segments[idx].length:
            s -= self._line_segments[idx].length
            idx += 1
        if idx == len(self._line_segments):
            return None
        return self._line_segments[idx].get_xy_by_sl(s, l)

    def get_sl_by_xy(self, x: 'Number', y: 'Number') -> Optional['SLPoint']:
        point = Vertex(x, y)
        res_s = None
        res_l = 0
        cum_s = 0
        pre_segment: Optional['LineSegment'] = None
        for cur_segment in self._line_segments:
            point_sl = cur_segment.get_sl_by_xy(x, y)
            if point_sl is not None:
                if res_s is None:
                    res_s = cum_s + point_sl.s
                    res_l = point_sl.l
                elif abs(res_l) > point_sl.d:
                    res_s = cum_s + point_sl.s
                    res_l = point_sl.l
            elif pre_segment is not None and (
                LineSegment(pre_segment.v2, pre_segment.v2 + pre_segment.vec.left_unit).to_left_test(point) ^
                LineSegment(cur_segment.v1, cur_segment.v1 + cur_segment.vec.left_unit).to_left_test(point)
            ):
                l = pre_segment.v2.dis_to(point)
                if abs(res_l) > l or res_s is None:
                    res_l = l if pre_segment.to_left_test(point) else -l
                    res_s = cum_s

            cum_s += cur_segment.length
            pre_segment = cur_segment
        if res_s is None:
            return None
        return SLPoint(self, res_s, res_l)

    def to_left_test(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        point_sl = self.get_sl_by_xy(point.x, point.y)
        if point_sl is not None:
            return point_sl.l > -tolerance
        # for line_segment in self.line_segments:
        #     if line_segment.cover_in_parallel(point) and line_segment.to_left_test(point):
        #         return True
        return False

    def intersect_with(self, other: 'Polyline') -> bool:
        for m_line in self._line_segments:
            for o_line in other.line_segments:
                if m_line.check_intersect(o_line):
                    return True
        return False

    def get_vertices_lerp(self) -> List[Number]:
        ts = [0]
        cum_length = 0
        for line_segment in self.line_segments[:-1]:
            cum_length += line_segment.length
            ts.append(cum_length / self.length)
        ts.append(1)
        return ts

    def get_line_segment_by_s(self, s: Number) -> Optional['LineSegment']:
        idx = 0
        while idx < len(self._line_segments) and s > self._line_segments[idx].length:
            s -= self._line_segments[idx].length
            idx += 1
        if idx == len(self._line_segments):
            return None
        return self._line_segments[idx]

    def extend(self, length: Number) -> 'Polyline':
        vertices = list(self.vertices)
        vertices[0] = vertices[0] + (vertices[0] - vertices[1]).unit * length
        vertices[-1] = vertices[-1] + (vertices[-1] - vertices[-2]).unit * length
        return Polyline(vertices)

    def __eq__(self, other: 'Polyline'):
        return self.vertices == other.vertices


def central_line(*polylines: "Polyline"):
    lerp_set = set()
    for polyline in polylines:
        for lerp_t in polyline.get_vertices_lerp():
            lerp_set.add(lerp_t)
    lerp_list = list(lerp_set)
    lerp_list.sort()
    polygon_vertices = []
    for lerp_t in lerp_list:
        vertices = [polyline.lerp(lerp_t) for polyline in polylines]
        polygon_vertices.append(average_vertex(*vertices))
    return Polyline(polygon_vertices)
