from adsv.utils.types import *
from adsv.utils import Counter
from adsv.ads_libs.apollo.map.parser import ApolloMapParser
from adsv.ads_libs.apollo.map.proto import map_pb2
from adsv.semantic_model.common.map_common import TurnType, RJType
from adsv.semantic_model.lane_map import Lane, LaneId, Section, SectionId
from adsv.geometry import Polyline, Vertex, average_vertex
from .lanes_adapter import LanesAdapter


BoundaryTypeMap = {
    0: Lane.BoundType.VIRTUAL,
    2: Lane.BoundType.DOTTED_WHITE,
    1: Lane.BoundType.DOTTED_YELLOW,
    5: Lane.BoundType.DOUBLE_YELLOW,
    4: Lane.BoundType.SOLID_WHITE,
    3: Lane.BoundType.SOLID_YELLOW,
    6: Lane.BoundType.CURB
}

TurnTypeMap = {
    4: TurnType.U_TURN,
    1: TurnType.NO_TURN,
    2: TurnType.LEFT_TURN,
    3: TurnType.RIGHT_TURN
}


def get_junction_lanes_id(map_proto) -> Set[LaneId]:
    junction_lanes_id = set()
    overlap_map = {overlap.id.id: overlap for overlap in map_proto.overlap}
    for junction in map_proto.junction:
        for overlap_id in junction.overlap_id:
            if 'lane' in overlap_id.id:
                overlap = overlap_map[overlap_id.id]
                for obj in overlap.object:
                    if 'lane' in obj.id.id:
                        junction_lanes_id.add(obj.id.id)
    return junction_lanes_id


def get_lanes_from_proto(proto_lanes, junction_lanes_id: Set[LaneId], lane_id_prefix: LaneId) -> Tuple[List[Lane], List[Tuple[str, LaneId]]]:
    lanes = []
    lane_counter = Counter()
    proto_id_lane_id_map: Dict[str, LaneId] = dict()
    lane_id_proto_id_map: Dict[LaneId, str] = dict()
    proto_id_lane_id_pair: List[Tuple[str, LaneId]] = []
    for lane_proto in proto_lanes:
        lane_id = f'{lane_id_prefix}{lane_counter.get()}'
        proto_id = lane_proto.id.id
        proto_id_lane_id_map[proto_id] = lane_id
        lane_id_proto_id_map[lane_id] = proto_id
        proto_id_lane_id_pair.append((proto_id, lane_id))

    for lane_proto in proto_lanes:
        lanes.append(Lane(proto_id_lane_id_map[lane_proto.id.id],
                          [proto_id_lane_id_map[pred.id] for pred in lane_proto.predecessor_id],
                          [proto_id_lane_id_map[suc.id] for suc in lane_proto.successor_id],
                          proto_id_lane_id_map[lane_proto.left_neighbor_forward_lane_id[0].id] if len(
                              lane_proto.left_neighbor_forward_lane_id) > 0 else None,
                          proto_id_lane_id_map[lane_proto.right_neighbor_forward_lane_id[0].id] if len(
                              lane_proto.right_neighbor_forward_lane_id) > 0 else None,
                          proto_id_lane_id_map[lane_proto.left_neighbor_reverse_lane_id[0].id] if len(
                              lane_proto.left_neighbor_reverse_lane_id) > 0 else None,
                          proto_id_lane_id_map[lane_proto.right_neighbor_reverse_lane_id[0].id] if len(
                              lane_proto.right_neighbor_reverse_lane_id) > 0 else None,
                          BoundaryTypeMap[lane_proto.left_boundary.boundary_type[0].types[0]],
                          BoundaryTypeMap[lane_proto.right_boundary.boundary_type[0].types[0]],
                          RJType.JUNCTION if lane_proto.id.id in junction_lanes_id else RJType.ROAD,
                          TurnTypeMap[lane_proto.turn],
                          Polyline([Vertex(point.x, point.y) for point in
                                    lane_proto.central_curve.segment[0].line_segment.point]),
                          Polyline([Vertex(point.x, point.y) for point in
                                    lane_proto.left_boundary.curve.segment[0].line_segment.point]),
                          Polyline([Vertex(point.x, point.y) for point in
                                    lane_proto.right_boundary.curve.segment[0].line_segment.point]),
                          0.1))
    return lanes, proto_id_lane_id_pair


class ApolloMapAdapter(metaclass=multimeta):
    @overload
    def __init__(self, proto: 'map_pb2.Map', lane_id_prefix: LaneId = 'lane_', section_id_prefix: SectionId = 'section_'):
        junction_lanes_id = get_junction_lanes_id(proto)
        lanes, self.proto_id_lane_id_pairs = get_lanes_from_proto(proto.lane, junction_lanes_id, lane_id_prefix)
        self.lane_map = LanesAdapter(lanes, section_id_prefix).lane_map

    @overload
    def __init__(self, proto_bytes: bytes, lane_id_prefix: LaneId = 'lane_', section_id_prefix: SectionId = 'section_'):
        self.__init__(ApolloMapParser(proto_bytes).proto, lane_id_prefix, section_id_prefix)
