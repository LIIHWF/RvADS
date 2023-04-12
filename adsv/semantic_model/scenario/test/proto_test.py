import unittest

# from adsv.semantic_model.lane_map import Lane
from adsv.semantic_model.static_scene.adapter import ApolloMapAdapter as ApolloMapStaticSceneAdapter
from adsv.semantic_model.lane_map.adapter import ApolloMapAdapter as ApolloMapLaneMapAdapter
from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.scenario.proto import scenario_pb2
from adsv.semantic_model.scenario import TrafficLightColor, TrafficLightState
import json, sys


class TestProto(unittest.TestCase):
    def test_additional_loop(self):
        a = scenario_pb2.TrafficLightState(color=1)


if __name__ == '__main__':
    unittest.main()
