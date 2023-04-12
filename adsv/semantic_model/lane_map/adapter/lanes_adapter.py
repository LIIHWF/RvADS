from adsv.utils.types import *
from adsv.utils import Counter
from adsv.geometry import Vertex, average_vertex, central_line
from adsv.semantic_model.lane_map import LaneMap, Lane, LaneId, Section, SectionId
from adsv.semantic_model.common.map_common import RJType, TurnType
from .lane_cluster import LaneCluster
from functools import cmp_to_key


def is_left_lane(lane1: 'Lane', lane2: 'Lane') -> bool:
    if lane1 == lane2:
        return False
    return lane1.reference_line.line_segments[0].to_left_test(lane2.reference_line.vertices[0])


def get_ordered_lanes(lanes: Iterable[Lane]) -> List[Lane]:
    ordered_lanes = list(lanes)
    ordered_lanes.sort(key=cmp_to_key(
        lambda lane1, lane2: 0 if lane1.id == lane2.id else 1 if is_left_lane(lane1, lane2) else -1
    ))
    return ordered_lanes


def get_section_lanes_map(lane_list: List[Lane], section_id_prefix) -> Mapping[SectionId, List[Lane]]:
    section_lanes_map: Dict[SectionId, List[Lane]] = dict()
    section_counter = Counter()
    for lanes in LaneCluster(lane_list).clusters:
        section_id = f'{section_id_prefix}{section_counter.get()}'
        section_lanes_map[section_id] = get_ordered_lanes(lanes)
    return MappingProxyType(section_lanes_map)


def get_section_left_right_neighbors(section_lanes_map: Mapping[SectionId, List[Lane]]):
    section_left_neighbor_id_map: Dict[SectionId, SectionId] = dict()
    section_right_neighbor_id_map: Dict[SectionId, SectionId] = dict()

    for section1_id, section1_lanes in section_lanes_map.items():
        for section2_id, section2_lanes in section_lanes_map.items():
            if section1_id != section2_id:
                if section1_lanes[0].left_reverse_neighbor_id == section2_lanes[0].id or \
                        section2_lanes[0].left_reverse_neighbor_id == section1_lanes[0].id:
                    section_left_neighbor_id_map[section1_id] = section2_id
                    section_left_neighbor_id_map[section2_id] = section1_id
                if section1_lanes[-1].right_reverse_neighbor_id == section2_lanes[-1].id or \
                        section2_lanes[-1].right_reverse_neighbor_id == section1_lanes[-1].id:
                    section_right_neighbor_id_map[section1_id] = section2_id
                    section_right_neighbor_id_map[section2_id] = section1_id
    return section_left_neighbor_id_map, section_right_neighbor_id_map


def generate_sections_by_lanes(lanes: List[Lane], section_id_prefix) -> List[Section]:
    section_lanes_map = get_section_lanes_map(lanes, section_id_prefix)
    section_left_neighbor_id_map, section_right_neighbor_id_map = \
        get_section_left_right_neighbors(section_lanes_map)
    sections = []
    for section_id, section_lanes in section_lanes_map.items():
        sections.append(Section(
            section_id, central_line(section_lanes[0].reference_line, section_lanes[-1].reference_line), section_lanes,
            section_left_neighbor_id_map[section_id] if section_id in section_left_neighbor_id_map else None,
            section_right_neighbor_id_map[section_id] if section_id in section_right_neighbor_id_map else None
        ))
    return sections


class LanesAdapter(metaclass=multimeta):
    def __init__(self, lanes: Iterable['Lane'], section_id_prefix: SectionId = 'section_'):
        self.lane_map = LaneMap(generate_sections_by_lanes(list(lanes), section_id_prefix))
