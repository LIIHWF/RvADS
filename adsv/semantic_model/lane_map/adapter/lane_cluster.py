from adsv.utils.types import *
from adsv.semantic_model.lane_map import Lane, LaneId, SectionId
from adsv.semantic_model.common.map_common import RJType, TurnType


class LaneCluster(metaclass=multimeta):
    def __init__(self, lanes: List[Lane]):
        self._lanes: List[Lane] = lanes
        self._lane_section_map: Dict[LaneId, int] = {lane.id: sid for sid, lane in enumerate(self._lanes)}
        self._section_lanes_map: Dict[int, FrozenSet[Lane]] = {sid: frozenset({lane}) for sid, lane in enumerate(self._lanes)}
        self._process_cluster()
        self.clusters = frozenset(self._section_lanes_map.values())

    def _process_cluster(self):
        flag = True
        while flag:
            flag = False

            for i in range(len(self._lanes)):
                for j in range(i + 1, len(self._lanes)):
                    lane1 = self._lanes[i]
                    lane2 = self._lanes[j]
                    if self._lane_section_map[lane1.id] == self._lane_section_map[lane2.id]:
                        continue

                    if lane2.id == lane1.left_forward_neighbor_id:
                        self._union_section(lane1.id, lane2.id)
                        flag = True
                    elif lane2.id == lane1.right_forward_neighbor_id:
                        self._union_section(lane1.id, lane2.id)
                        flag = True
                    elif self._has_same_vertices(lane1.id, lane2.id) and \
                            lane1.rj_type == lane2.rj_type == RJType.JUNCTION and lane1.turn_type == lane2.turn_type:
                        self._union_section(lane1.id, lane2.id)
                        flag = True

    def _union_section(self, lane1_id: LaneId, lane2_id: LaneId):
        section1_id = self._lane_section_map[lane1_id]
        section2_id = self._lane_section_map[lane2_id]
        for lane in self._section_lanes_map[section2_id]:
            self._lane_section_map[lane.id] = section1_id
        self._section_lanes_map[section1_id] |= self._section_lanes_map[section2_id]
        self._section_lanes_map.pop(section2_id)

    def _has_same_vertices(self, lane1_id: 'LaneId', lane2_id: 'LaneId') -> bool:
        section1_id = self._lane_section_map[lane1_id]
        section2_id = self._lane_section_map[lane2_id]
        return self._get_section_predecessors_id(section1_id) == self._get_section_predecessors_id(section2_id) and \
               self._get_section_successors_id(section1_id) == self._get_section_successors_id(section2_id)

    def _get_section_predecessors_id(self, sec_id: int) -> Set[int]:
        ret = set()
        for lane in self._section_lanes_map[sec_id]:
            for pred_lane_id in lane.predecessors_id:
                pred_section_id = self._lane_section_map[pred_lane_id]
                ret.add(pred_section_id)
        return ret

    def _get_section_successors_id(self, sec_id: int) -> Set[int]:
        ret = set()
        for lane in self._section_lanes_map[sec_id]:
            for suc_lane_id in lane.successors_id:
                suc_section = self._lane_section_map[suc_lane_id]
                ret.add(suc_section)
        return ret
