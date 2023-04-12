import unittest

# from adsv.semantic_model.lane_map import Lane
from adsv.semantic_model.lane_map.adapter import ApolloMapAdapter
from adsv.semantic_model.metric_graph.adapter import LaneMapAdapter


class TestProto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('data/apollo_map/BorregasAve.bin', 'rb') as f:
            lane_map = ApolloMapAdapter(f.read()).lane_map
            cls.metric_graph = LaneMapAdapter(lane_map).metric_graph

    @staticmethod
    def make_copy_by_proto(origin):
        origin_proto = origin.dump()
        origin_proto_str = origin_proto.SerializeToString()
        new_proto = type(origin_proto)()
        new_proto.ParseFromString(origin_proto_str)
        return type(origin)(new_proto)

    def test_metric_graph_proto(self):
        self.assertTrue(self.metric_graph.strict_eq(self.make_copy_by_proto(self.metric_graph)))


if __name__ == '__main__':
    unittest.main()
