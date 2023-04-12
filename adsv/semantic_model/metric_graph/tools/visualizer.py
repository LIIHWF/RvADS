from adsv.semantic_model.metric_graph import MetricGraph
from adsv.semantic_model.common.map_common import RJType
from matplotlib import pyplot as plt


class MetricGraphVisualizer:
    def __init__(self, metric_graph: MetricGraph):
        self._metric_graph = metric_graph

    def plot(self, ax):
        node_x = []
        node_y = []
        width = 0.2
        for node in self._metric_graph.nodes.values():
            ax.text(node.display_position.x, node.display_position.y, node.id,
                    zorder=1)
            node_x.append(node.display_position.x)
            node_y.append(node.display_position.y)
        ax.scatter(node_x, node_y, zorder=1, c='r')
        for edge in self._metric_graph.edges.values():
            cnt = 0
            for line_seg in edge.display_line.line_segments:
                color = 'blue' if edge.rj_type == RJType.ROAD else 'green'
                if cnt == len(edge.display_line.line_segments) - 1:
                    ax.annotate("", xytext=(line_seg.v1.x, line_seg.v1.y), xy=(line_seg.v2.x, line_seg.v2.y),
                                arrowprops=dict(width=width, color=color, headwidth=width * 40, headlength=width * 40),
                                annotation_clip=False, zorder=1)
                else:
                    ax.plot([line_seg.v1.x, line_seg.v2.x], [line_seg.v1.y, line_seg.v2.y], c=color,
                            linewidth=width * 7,
                            zorder=1)
                cnt += 1
            center_point = edge.display_line.lerp(0.5)
            ax.text(center_point.x, center_point.y, edge.id)

    def show(self):
        self.plot(plt)
        plt.show()
