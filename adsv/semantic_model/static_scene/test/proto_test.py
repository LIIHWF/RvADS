import unittest

# from adsv.semantic_model.lane_map import Lane
from adsv.semantic_model.static_scene.adapter import ApolloMapAdapter


class TestProto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('apollo_map/SanFrancisco.bin', 'rb') as f:
            cls.static_scene = ApolloMapAdapter(f.read()).static_scene

    @staticmethod
    def make_copy_by_proto(origin):
        origin_proto = origin.dump()
        origin_proto_str = origin_proto.SerializeToString()
        new_proto = type(origin_proto)()
        new_proto.ParseFromString(origin_proto_str)
        return type(origin)(new_proto)

    def test_metric_graph_proto(self):
        self.assertTrue(self.static_scene.strict_eq(self.make_copy_by_proto(self.static_scene)))


if __name__ == '__main__':
    unittest.main()
