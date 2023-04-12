from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.metric_graph.tools.visualizer import MetricGraphVisualizer
import matplotlib.pyplot as plt
from adsv.semantic_model.scenario import Scenario, TrafficLightColor
from adsv.semantic_model.scenario.proto import scenario_pb2
import argparse


parser = argparse.ArgumentParser(description='Show metric graph')
parser.add_argument('SCENARIO_FILE_PATH', type=str)
args = parser.parse_args()


try:
    with open(args.SCENARIO_FILE_PATH, 'rb') as f:
        proto = scenario_pb2.Scenario()
        proto.ParseFromString(f.read())
    scenario = Scenario(proto)
    MetricGraphVisualizer(scenario.static_scene.metric_graph).plot(plt)
except FileNotFoundError:
    loader = MapInfoLoader(args.SCENARIO_FILE_PATH)
    MetricGraphVisualizer(loader.metric_graph).plot(plt)
except Exception as e:
    print('file not found', e)

plt.show()

