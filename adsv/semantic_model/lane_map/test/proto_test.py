import unittest

# from adsv.semantic_model.lane_map import Lane
from adsv.semantic_model.lane_map.adapter import ApolloMapAdapter


class TestProto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('apollo_map/BorregasAve.bin', 'rb') as f:
            cls.lane_map = ApolloMapAdapter(f.read()).lane_map

    @staticmethod
    def make_copy_by_proto(origin):
        origin_proto = origin.dump()
        origin_proto_str = origin_proto.SerializeToString()
        new_proto = type(origin_proto)()
        new_proto.ParseFromString(origin_proto_str)
        return type(origin)(new_proto)

    def test_lane_proto(self):
        for lane in self.lane_map.lanes.values():
            self.assertTrue(lane.strict_eq(self.make_copy_by_proto(lane), True))

    def test_section_proto(self):
        for section in self.lane_map.sections.values():
            self.assertTrue(section.strict_eq(self.make_copy_by_proto(section), True))

    def test_lane_map_proto(self):
        self.assertTrue(self.lane_map.strict_eq(self.make_copy_by_proto(self.lane_map)))


if __name__ == '__main__':
    unittest.main()
