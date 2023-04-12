import os


class MapManagerConfig:
    APOLLO_MAP_DIR = 'data/apollo_map'
    MAP_DATA_DIR = 'data/map'
    LANE_MAP_FILE_NAME = 'lane_map.bin'
    STATIC_SCENE_FILE_NAME = 'static_scene.bin'
    PROTO_SIGNAL_ID_PAIRS_FILE_NAME = 'proto_signal_id_pairs.json'
    SECTION_EDGE_ID_PAIRS_FILE_NAME = 'section_edge_id_pairs.json'
    TRAFFIC_LIGHTS_POSITION_FILE_NAME = 'traffic_lights_position.json'

    @classmethod
    def lane_map_path(cls, map_name: str):
        return os.path.join(cls.MAP_DATA_DIR, map_name, cls.LANE_MAP_FILE_NAME)

    @classmethod
    def section_edge_id_pairs_path(cls, map_name: str):
        return os.path.join(cls.MAP_DATA_DIR, map_name, cls.SECTION_EDGE_ID_PAIRS_FILE_NAME)

    @classmethod
    def proto_signal_id_pairs_file_path(cls, map_name: str):
        return os.path.join(cls.MAP_DATA_DIR, map_name, cls.PROTO_SIGNAL_ID_PAIRS_FILE_NAME)

    @classmethod
    def static_scene_file_path(cls, map_name: str):
        return os.path.join(cls.MAP_DATA_DIR, map_name, cls.STATIC_SCENE_FILE_NAME)

    @classmethod
    def traffic_lights_position_file_path(cls, map_name: str):
        return os.path.join(cls.MAP_DATA_DIR, map_name, cls.TRAFFIC_LIGHTS_POSITION_FILE_NAME)

    @classmethod
    def apollo_map_file_path(cls, map_name: str):
        return os.path.join(cls.APOLLO_MAP_DIR, f'{map_name}.bin')
