from adsv.utils.types import *
from adsv.geometry.element.point import Vertex


class BoundBox:
    def _init_bound_box(self, min_x, max_x, min_y, max_y):
        self._min_x = min_x
        self._min_y = min_y
        self._max_x = max_x
        self._max_y = max_y

    @property
    def min_x(self):
        return self._min_x

    @property
    def min_y(self):
        return self._min_y

    @property
    def max_x(self):
        return self._max_x

    @property
    def max_y(self):
        return self._max_y

    def within_box(self, point: 'Vertex'):
        return self.min_x <= point.x <= self.max_x and self.min_y <= point.y <= self.max_y
