from adsv.semantic_model.lane_map import LaneMap
from matplotlib import pyplot as plt


class LaneMapVisualizer:
    def __init__(self, lane_map: LaneMap):
        self._lane_map = lane_map

    def plot(self, ax):
        for lane in self._lane_map.lanes.values():
            ax.plot([v.x for v in lane.left_boundary_line.vertices], [v.y for v in lane.left_boundary_line.vertices], c='blue')
            ax.plot([v.x for v in lane.right_boundary_line.vertices], [v.y for v in lane.right_boundary_line.vertices], c='blue')

        for section in self._lane_map.sections.values():
            ax.plot([v.x for v in section.reference_line.vertices], [v.y for v in section.reference_line.vertices], c='red')


    def show(self):
        self.plot(plt)
        plt.show()
