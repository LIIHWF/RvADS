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

#
parser = argparse.ArgumentParser(description='Scenario Info')
parser.add_argument('FILE_PATH', type=str)
parser.add_argument('-l', type=int, default=0, required=False)
parser.add_argument('-u', type=int, default=-1, required=False)
#
# parser.add_argument('-e', action='store_true', help='output edge_id')
# parser.add_argument('-o', action='store_true', help='output offset')
# parser.add_argument('-s', action='store_true', help='output speed')

SEP = 50
TICK_SEP = 6

args = parser.parse_args()



with open(args.FILE_PATH, 'rb') as f:
    proto = scenario_pb2.Scenario()
    proto.ParseFromString(f.read())

scenario = Scenario(proto)


lower_bound = args.l if args.l >= 0 else scenario.ticks_num + args.l
upper_bound = args.u if args.u >= 0 else scenario.ticks_num + args.u


sorted_vid = sorted(scenario.vehicles_id)

print(' ' * TICK_SEP, end='')
for vid in sorted_vid:
    print(vid, end=' ' * (SEP - len(vid)))
print()

for tick in range(lower_bound, upper_bound + 1):
    print(tick, end=' ' * (TICK_SEP - len(str(tick))))
    for vid in sorted_vid:
        vstate = scenario.dynamic_scenario.dynamic_scene(tick).vehicle_state(vid)
        edge_id = vstate.edge_id
        offset = round(vstate.lane_begin_offset, 3)
        endoffset = round(vstate.lane_end_offset, 3)
        speed = round(vstate.control_speed, 2)
        is_stop = ', S' if vstate.at_stop_target else ''
        turn = round(vstate.turn, 2)
        target_turn = round(vstate.target_turn, 2)
        target_speed = round(vstate.target_speed, 2)
        vinfo = f'({edge_id}, {offset}/{endoffset}, {speed}/{target_speed}, {turn}/{target_turn}{is_stop})'
        print(vinfo, end=' ' * (SEP - len(vinfo)))
    print()
