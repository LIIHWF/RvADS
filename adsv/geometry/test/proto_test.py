import unittest

from adsv.geometry import Vertex, Vector, LineSegment, Polyline, Radian, RegionPolyline
from adsv.utils.test import make_copy_by_proto


class TestProto(unittest.TestCase):
    def test_vertex_proto(self):
        vertex = Vertex(1.1, 20.2)
        self.assertEqual(vertex, make_copy_by_proto(vertex))

    def test_vector_proto(self):
        vector = Vector(1.1, 20.2)
        self.assertEqual(vector, make_copy_by_proto(vector))

    def test_line_segment_proto(self):
        line_segment = LineSegment(Vertex(1.1, 2.2), Vertex(3.3, 4.4))
        self.assertEqual(line_segment, make_copy_by_proto(line_segment))

    def test_polyline_proto(self):
        polyline = Polyline([Vertex(1, 2), Vertex(3, 4), Vertex(5, 6), Vertex(7, 8)])
        self.assertEqual(polyline, make_copy_by_proto(polyline))

    def test_radian_proto(self):
        radian = Radian(780)
        self.assertEqual(radian, make_copy_by_proto(radian))

    def test_region_polyline_proto(self):
        region_polyline = RegionPolyline(Polyline([Vertex(0, 0), Vertex(0, 1), Vertex(0, 2)]),
                                         Polyline([Vertex(-1, 0), Vertex(-1, 1), Vertex(-1, 2)]),
                                         Polyline([Vertex(1, 0), Vertex(1, 1), Vertex(1, 2)]))
        self.assertEqual(region_polyline, make_copy_by_proto(region_polyline))


if __name__ == '__main__':
    unittest.main()
