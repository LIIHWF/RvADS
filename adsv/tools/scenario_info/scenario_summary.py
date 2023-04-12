from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.metric_graph.tools.visualizer import MetricGraphVisualizer
import matplotlib.pyplot as plt
from adsv.semantic_model.scenario import Scenario, TrafficLightColor
from adsv.semantic_model.scenario.proto import scenario_pb2
from adsv.tm2cl.automata.parser import parse_ltl_formula
from adsv.tm2cl.automata.automata import Symbol
import sys

import argparse
import sys


parser = argparse.ArgumentParser(description='Scenario Info')
parser.add_argument('FILE_PATH', type=str)
args = parser.parse_args()

with open(args.FILE_PATH, 'rb') as f:
    proto = scenario_pb2.Scenario()
    proto.ParseFromString(f.read())

scenario = Scenario(proto)


sorted_vid = sorted(scenario.vehicles_id)


itineraries = {
    vid: None for vid in sorted_vid
}
print('===== Itineraries =====')
for vid in sorted_vid:
    vconfig = scenario.scenario_configuration.vehicles_configuration[vid]
    sid_seq = vconfig.itinerary.segment_id_seq
    turn_type = scenario.static_scene.metric_graph.edge(sid_seq[1]).turn_type
    print(vid, turn_type.name, sid_seq)
    itineraries[vid] = sid_seq
print()


segment_last_tick = {
    vid: [None for _ in range(3)] for vid in sorted_vid
}

for tick in range(scenario.ticks_num):
    for vid in sorted_vid:
        vstate = scenario.dynamic_scenario.dynamic_scene(tick).vehicle_state(vid)
        edge_id = vstate.edge_id
        if edge_id == itineraries[vid][0]:
            segment_last_tick[vid][0] = tick
        elif edge_id == itineraries[vid][1]:
            segment_last_tick[vid][1] = tick
        elif edge_id == itineraries[vid][2]:
            segment_last_tick[vid][2] = tick

entering_info = {
    vid: {'stop_distance': None, 'stop_time': None} for vid in sorted_vid
}

for vid in sorted_vid:
    last_stop_time = 0
    stop_distance = 0
    for tick in range(segment_last_tick[vid][0], -1, -1):
        vstate = scenario.dynamic_scenario.dynamic_scene(tick).vehicle_state(vid)
        if vstate.target_speed == 0:
            stop_distance = vstate.lane_end_offset
            last_stop_time = tick
            break
    entering_info[vid]['stop_distance'] = stop_distance
    entering_info[vid]['entering_time'] = \
        (segment_last_tick[vid][0] - last_stop_time) * scenario.scenario_configuration.time_interval


print('===== Entering Info =====')
for vid in sorted_vid:
    print('-', vid)
    print('-- stop distance:', round(entering_info[vid]['stop_distance'], 3))
    print('-- entering time:', round(entering_info[vid]['entering_time'], 3), 's')
print()


leaving_info = {
    vid: {'leaving_time': None, 'leaving_distance': None} for vid in sorted_vid[:-1]
}

for i, c_vid in enumerate(sorted_vid[:-1]):
    n_vid = sorted_vid[i+1]
    for tick in range(segment_last_tick[c_vid][1], -1, -1):
        c_vstate = scenario.dynamic_scenario.dynamic_scene(tick).vehicle_state(c_vid)
        n_vstate = scenario.dynamic_scenario.dynamic_scene(tick).vehicle_state(n_vid)
        if n_vstate.target_speed == 0:
            leaving_info[c_vid]['leaving_time'] = \
                (segment_last_tick[c_vid][1] - tick) * scenario.scenario_configuration.time_interval
            leaving_info[c_vid]['leaving_distance'] = c_vstate.lane_end_offset
            break

print('===== Leaving Info =====')
for vid in sorted_vid[:-1]:
    print('-', vid)
    print('-- leaving distance:', round(leaving_info[vid]['leaving_distance'], 3))
    print('-- leaving time:', round(leaving_info[vid]['leaving_time'], 3), 's')
print()


