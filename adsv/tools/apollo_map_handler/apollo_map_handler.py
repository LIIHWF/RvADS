import json
import os
import sys

from adsv.ads_libs.apollo.map.proto import map_pb2
from adsv.semantic_model.static_scene.adapter import ApolloMapAdapter
from adsv.utils.types import *
from adsv.map_manager import MapManagerConfig


class Saver:
    def __init__(self, map_name: str):
        self.map_name = map_name
        with open(MapManagerConfig.apollo_map_file_path(map_name), 'rb') as f:
            map_proto = map_pb2.Map()
            map_proto.ParseFromString(f.read())
        self._build_traffic_lights_position(map_proto)
        self._apollo_static_scene_adapter = ApolloMapAdapter(map_proto)

    def _build_traffic_lights_position(self, map_proto: map_pb2.Map):
        self._traffic_lights_position = dict()
        for signal_proto in map_proto.signal:
            points_proto = signal_proto.boundary.point
            sum_x, sum_y, sum_z = 0, 0, 0
            for point_proto in points_proto:
                sum_x += point_proto.x
                sum_y += point_proto.y
                sum_z += point_proto.z
            num = len(points_proto)
            self._traffic_lights_position[signal_proto.id.id] = {
                'x': sum_x / num, 'y': sum_y / num, 'z': sum_z / num
            }

    def save(self, workspace_dir):
        def abs_path(path):
            return os.path.join(workspace_dir, path)

        with open(abs_path(MapManagerConfig.lane_map_path(self.map_name)), 'wb') as f:
            f.write(self._apollo_static_scene_adapter.lane_map.dump().SerializeToString())

        with open(abs_path(MapManagerConfig.lane_map_path(self.map_name) + '.txt'), 'w') as f:
            f.write(str(self._apollo_static_scene_adapter.lane_map.dump()))

        with open(abs_path(MapManagerConfig.static_scene_file_path(self.map_name)), 'wb') as f:
            f.write(self._apollo_static_scene_adapter.static_scene.dump().SerializeToString())

        with open(abs_path(MapManagerConfig.static_scene_file_path(self.map_name) + '.txt'), 'w') as f:
            f.write(str(self._apollo_static_scene_adapter.static_scene.dump()))

        with open(abs_path(MapManagerConfig.proto_signal_id_pairs_file_path(self.map_name)), 'w') as f:
            json.dump(list(self._apollo_static_scene_adapter.proto_id_signal_id_pairs), f)

        with open(abs_path(MapManagerConfig.section_edge_id_pairs_path(self.map_name)), 'w') as f:
            json.dump(list(self._apollo_static_scene_adapter.section_edge_id_pairs), f)

        with open(abs_path(MapManagerConfig.traffic_lights_position_file_path(self.map_name)), 'w') as f:
            json.dump(self._traffic_lights_position, f)


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise ValueError("A single map name should be specified")
    map_name = sys.argv[1]
    saver = Saver(map_name)
    workspace_dir = sys.argv[2]
    saver.save(workspace_dir)
