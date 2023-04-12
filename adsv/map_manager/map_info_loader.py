from adsv.utils.types import *
from adsv.semantic_model.lane_map import LaneMap
from adsv.semantic_model.static_scene import StaticScene
from adsv.semantic_model.static_scene.proto import static_scene_pb2
from adsv.semantic_model.lane_map.proto import lane_map_pb2
from .common import MapManagerConfig
import json
import os


class MapInfoLoader:
    def __init__(self, map_name: str):
        self.map_name = map_name
        self._load_lane_map()
        self._load_segment_section_map()
        self._load_signal_proto_map()
        self._load_semantic_model()
        self._load_traffic_lights_position()

    def _load_lane_map(self):
        with open(os.path.join(MapManagerConfig.lane_map_path(self.map_name)), 'rb') as f:
            lane_map_proto = lane_map_pb2.LaneMap()
            lane_map_proto.ParseFromString(f.read())
        self.lane_map = LaneMap(lane_map_proto)

    def _load_segment_section_map(self):
        with open(MapManagerConfig.section_edge_id_pairs_path(self.map_name)) as f:
            section_edge_id_pairs = json.load(f)
        self.section_edge_id_pairs = section_edge_id_pairs
        self.seg_sec_id_map = {
            edge_id: section_id for section_id, edge_id in section_edge_id_pairs
        }
        self.sec_seg_id_map = {
            section_id: edge_id for section_id, edge_id in section_edge_id_pairs
        }

    def _load_signal_proto_map(self):
        with open(MapManagerConfig.proto_signal_id_pairs_file_path(self.map_name)) as f:
            proto_signal_id_pairs = json.load(f)
        self.proto_signal_id_pairs = proto_signal_id_pairs
        self.signal_pb_mg_map = {
            pb_id: mg_id for pb_id, mg_id in proto_signal_id_pairs
        }
        self.signal_mg_pb_map = {
            mg_id: pb_id for pb_id, mg_id in proto_signal_id_pairs
        }

    def _load_semantic_model(self):
        with open(MapManagerConfig.static_scene_file_path(self.map_name), 'rb') as f:
            static_scene_proto = static_scene_pb2.StaticScene()
            static_scene_proto.ParseFromString(f.read())
        self.static_scene = StaticScene(static_scene_proto)
        self.metric_graph = self.static_scene.metric_graph

    def _load_traffic_lights_position(self):
        with open(MapManagerConfig.traffic_lights_position_file_path(self.map_name)) as f:
            self.traffic_lights_position = json.load(f)

