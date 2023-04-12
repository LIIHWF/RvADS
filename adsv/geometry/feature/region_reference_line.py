from adsv.utils.types import *
from .reference_line import ReferenceLine, SLPoint
from .region_item import RegionItem
from adsv.geometry.element.point import Vertex


class RegionReferenceLine(ReferenceLine, RegionItem):
    @abstractmethod
    def get_sl_by_xy(self, x: 'Number', y: 'Number', tolerance: Number = 0) -> Optional['SLPoint']:
        raise NotImplementedError

    @abstractmethod
    def get_xy_by_sl(self, s: 'Number', l: 'Number', tolerance: Number = 0) -> Optional['Vertex']:
        raise NotImplementedError

    @property
    @abstractmethod
    def length(self) -> Number:
        raise NotImplementedError

    @abstractmethod
    def to_left_test(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        raise NotImplementedError

    @abstractmethod
    def within_region(self, point: 'Vertex', tolerance: Number = 0) -> bool:
        raise NotImplementedError
