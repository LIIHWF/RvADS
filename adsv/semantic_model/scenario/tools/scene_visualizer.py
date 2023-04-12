from adsv.utils.types import *
from adsv.semantic_model.scenario import Scene, TrafficLightState, TrafficLightColor
from adsv.semantic_model.metric_graph import NodeId
from adsv.semantic_model.static_scene import SignalType
from adsv.semantic_model.metric_graph.tools.visualizer import MetricGraphVisualizer
from adsv.semantic_model.common.map_common import RJType
from matplotlib import pyplot as plt


class SceneVisualizer:
    def __init__(self, scene: Scene):
        self._scene = scene

    def plot(self, ax):
        metric_graph = self._scene.metric_graph

        stop_sign_nodes_id = {signal.state.control_node_id
                              for signal in self._scene.static_scene.signals.values()
                              if signal.signal_type == SignalType.STOP_SIGN}

        traffic_lights_color: Dict[NodeId, str] = {
            self._scene.static_scene.signals[tid].state.control_node_id: traffic_light_state.color.name.lower()
            for tid, traffic_light_state in self._scene.dynamic_scene.traffic_lights_state.items()
        }

        node_x = []
        node_y = []
        node_c = []
        width = 0.2
        for node in metric_graph.nodes.values():
            ax.text(node.display_position.x, node.display_position.y, node.id,
                    zorder=3, size='large')
            node_x.append(node.display_position.x)
            node_y.append(node.display_position.y)
            node_c.append('salmon' if node.id in stop_sign_nodes_id
                          else traffic_lights_color[node.id] if node.id in traffic_lights_color else 'gray')
        ax.scatter(node_x, node_y, zorder=2, c=node_c)

        for edge in metric_graph.edges.values():
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
            ax.text(center_point.x, center_point.y, f'{edge.id}: {round(edge.length, 3)}', zorder=3, fontsize='large')

        for vehicle_id, vehicle_state in self._scene.dynamic_scene.vehicles_state.items():
            edge = metric_graph.edge(vehicle_state.edge_id)
            show_point = edge.display_line.lerp(vehicle_state.offset / edge.length)
            ax.plot(show_point.x, show_point.y, "*", c='orange')
            ax.text(show_point.x, show_point.y, f'{vehicle_id}: ({vehicle_state.edge_id}, {round(vehicle_state.offset, 3)})', fontsize='large')

    def show(self):
        self.plot(plt)
        plt.show()
