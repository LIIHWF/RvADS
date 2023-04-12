from adsv.utils.types import *
from .element.lane import Lane, LaneId
from .element.section import Section, SectionId
from adsv.semantic_model.lane_map.proto import lane_map_pb2


class LaneMap(ProtoClass):
    @singledispatchmethod
    def __init__(self, sections: Iterable['Section']):
        self._sections: Mapping['SectionId', 'Section'] = MappingProxyType({
            section.id: section for section in sections
        })

        self._lanes: Mapping['LaneId', 'Lane'] = MappingProxyType({
            lane.id: lane for section in sections for lane in section.ordered_lanes
        })

        self._lane_section_map = MappingProxyType({
            lane.id: section for section in sections for lane in section.ordered_lanes
        })

    @__init__.register
    def __init__proto(self, proto: lane_map_pb2.LaneMap):
        self.__init__([Section(section_proto) for section_proto in proto.sections])

    def dump(self) -> lane_map_pb2.LaneMap:
        proto = lane_map_pb2.LaneMap()
        for section in self.sections.values():
            section_proto = proto.sections.add()
            section_proto.CopyFrom(section.dump())
        return proto

    @property
    def sections(self) -> Mapping['SectionId', 'Section']:
        return self._sections

    @property
    def lanes(self) -> Mapping['LaneId', 'Lane']:
        return self._lanes

    def get_lane_section(self, lane_id: 'LaneId') -> 'Section':
        return self._lane_section_map[lane_id]

    def strict_eq(self, other: 'LaneMap') -> bool:
        for section_id, section in self.sections.items():
            if not section.strict_eq(other.sections[section_id]):
                return False
        return True
