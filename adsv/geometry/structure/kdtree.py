from math import sqrt
from enum import Enum, auto
from adsv.utils.types import *
from adsv.geometry.feature.region_item import RegionItem
from adsv.geometry.element.point import Vertex


class BoundaryInfo(NamedTuple):
    min_x: Number
    max_x: Number
    min_y: Number
    max_y: Number


def _compute_boundary(objects: Iterable['RegionItem']):
    result = BoundaryInfo(INF, -INF, INF, -INF)
    for object_ in objects:
        result = BoundaryInfo(
            max_x=max(result.max_x, object_.max_x),
            min_x=min(result.min_x, object_.min_x),
            max_y=max(result.max_y, object_.max_y),
            min_y=min(result.min_y, object_.min_y)
        )
    return result


class KDTreeNode:
    class Partition(Enum):
        X = auto()
        Y = auto()

    def __init__(self, objects: Iterable['RegionItem']):
        self._objects_sorted_by_min: List['RegionItem'] = []
        self._objects_sorted_by_max: List['RegionItem'] = []
        self._objects_sorted_by_min_bound: List['Number'] = []
        self._objects_sorted_by_max_bound: List['Number'] = []
        self._num_objects = 0
        self._boundary = _compute_boundary(objects)

        self._mid_x = (self._boundary.max_x + self._boundary.min_x) / 2
        self._mid_y = (self._boundary.max_y + self._boundary.min_y) / 2

        self._partition, self._partition_position = self._compute_partition()

        self._left_node = None
        self._right_node = None

        left_node_objects, right_node_objects, other_objects = self._partition_objects(objects)

        if len(left_node_objects) > 0:
            self._left_node = KDTreeNode(left_node_objects)

        if len(right_node_objects) > 0:
            self._right_node = KDTreeNode(right_node_objects)

        self._init_objects(other_objects)

        for i in range(self._num_objects - 1):
            assert self._objects_sorted_by_max_bound[i] >= self._objects_sorted_by_max_bound[i + 1]
            assert self._objects_sorted_by_min_bound[i] <= self._objects_sorted_by_min_bound[i + 1]

    def _compute_partition(self):
        if self._boundary.max_x - self._boundary.min_x >= self._boundary.max_y - self._boundary.min_y:
            return self.Partition.X, self._mid_x
        else:
            return self.Partition.Y, self._mid_y

    def _init_objects(self, objects):
        self._num_objects = len(objects)
        self._objects_sorted_by_min = [item for item in objects]
        self._objects_sorted_by_max = [item for item in objects]

        self._objects_sorted_by_min.sort(key=lambda
            region: region.min_x if self._partition == self.Partition.X else region.min_y)
        self._objects_sorted_by_max.sort(key=lambda
            region: -region.max_x if self._partition == self.Partition.X else -region.max_y)

        self._objects_sorted_by_min_bound = [
            (object_.min_x if self._partition == self.Partition.X else object_.min_y)
            for object_ in self._objects_sorted_by_min]
        self._objects_sorted_by_max_bound = [
            (object_.max_x if self._partition == self.Partition.X else object_.max_y)
            for object_ in self._objects_sorted_by_max]

        for i in range(self._num_objects - 1):
            assert self._objects_sorted_by_max_bound[i] >= self._objects_sorted_by_max_bound[i + 1]
            assert self._objects_sorted_by_min_bound[i] <= self._objects_sorted_by_min_bound[i + 1]

    def _partition_objects(self, objects: Iterable['RegionItem']):
        left_node_objects = []
        right_node_objects = []
        other_objects = []
        if self._partition == self.Partition.X:
            for object_ in objects:
                if object_.max_x < self._partition_position:
                    left_node_objects.append(object_)
                elif object_.min_x > self._partition_position:
                    right_node_objects.append(object_)
                else:
                    other_objects.append(object_)
        else:
            for object_ in objects:
                if object_.max_y < self._partition_position:
                    left_node_objects.append(object_)
                elif object_.min_y > self._partition_position:
                    right_node_objects.append(object_)
                else:
                    other_objects.append(object_)
        return left_node_objects, right_node_objects, other_objects

    def _lower_distance_to_point(self, point):
        dx = 0
        if point.x < self._boundary.min_x:
            dx = self._boundary.min_x - point.x
        elif point.x > self._boundary.max_x:
            dx = point.x - self._boundary.max_x

        dy = 0
        if point.y < self._boundary.min_y:
            dy = self._boundary.min_y - point.y
        elif point.y > self._boundary.max_y:
            dy = point.y - self._boundary.max_y

        return sqrt(dx * dx + dy * dy)

    def get_all_objects(self):
        ret = []
        if self._left_node is not None:
            ret += self._left_node.get_all_objects()

        ret += self._objects_sorted_by_min

        if self._right_node is not None:
            ret += self._right_node.get_all_objects()
        return ret

    def get_covered_objects(self, point: 'Vertex', tolerance: Number = 0) -> List['RegionItem']:
        ret: List['RegionItem'] = []
        for object_ in self._objects_sorted_by_min:
            if object_.within_box(point):
                if object_.within_region(point, tolerance):
                    ret.append(object_)
        if self._partition == self.Partition.X:
            if self._left_node is not None and point.x < self._partition_position:
                ret.extend(self._left_node.get_covered_objects(point, tolerance))
            if self._right_node is not None and point.x > self._partition_position:
                ret.extend(self._right_node.get_covered_objects(point, tolerance))
        else:
            if self._left_node is not None and point.y < self._partition_position:
                ret.extend(self._left_node.get_covered_objects(point, tolerance))
            if self._right_node is not None and point.y > self._partition_position:
                ret.extend(self._right_node.get_covered_objects(point, tolerance))
        return ret


class KDTree:
    def __init__(self, objects: Iterable['RegionItem']):
        self._root = KDTreeNode(objects)

    def get_covered_objects(self, point: 'Vertex', tolerance: Number = 0) -> List[Any]:
        return self._root.get_covered_objects(point, tolerance)
