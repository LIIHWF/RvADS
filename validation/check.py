import sys, os, time
from adsv.semantic_model.scenario import Scenario, TrafficLightColor
from adsv.semantic_model.scenario.proto import scenario_pb2
from adsv.scenario_generator.junction_scenario_generator import JunctionPatternGenerator
from adsv.tm2cl.ast import *
from adsv.monitor import Monitor, Property
from adsv.map_manager import MapInfoLoader
from adsv.utils.types import *
from multiprocessing import Pool
import argparse

arg_parser = argparse.ArgumentParser('check')
arg_parser.add_argument('RUNS_DIR', help='absolute path to the simulated runs')
arg_parser.add_argument('VERDICTS_DIR', help='absolute path to save the verdicts')
arg_parser.add_argument('--type', choices=['stop_sign', 'traffic_light'], required=True,
                        help='type of the junction')
arg_parser.add_argument('--way', help='way of the junction', required=True, choices=['4', 'T'])
arg_parser.add_argument('--pool_size', default=1, type=int,
                        help='process pool size N (allow simultaneous checking of N runs, default=1)')

args = arg_parser.parse_args()
SCENARIO_DIR = args.RUNS_DIR
SAVE_DIR = args.VERDICTS_DIR
assert os.path.isabs(SCENARIO_DIR) and os.path.isabs(SAVE_DIR), 'RUNS_DIR and VERDICTS_DIR should be absolute path'
WAY = 3 if args.way == 'T' else 4 if args.way == '4' else None
MAP_NAME = 'CubeTown' if WAY == 3 else 'SanFrancisco'
POOL_SIZE = args.pool_size
TYPE = args.type

mg = MapInfoLoader(MAP_NAME).metric_graph
pattern = next(JunctionPatternGenerator(MAP_NAME, WAY, TYPE).junction_patterns())
target_junction = pattern.junction

focus_edges_id = set(target_junction.edges_id)
for node_id in target_junction.entrance_nodes_id:
    focus_edges_id |= set(edge.id for edge in mg.enter_edges(node_id))
for node_id in target_junction.exit_nodes_id:
    focus_edges_id |= set(edge.id for edge in mg.exit_edges(node_id))

c = VehicleVariable('c')
cc = VehicleVariable('c\'')
st = StopSignVariable('st')
j = JunctionVariable('j')
jen = JunctionEntranceVariable(j, 'en')
jenn = JunctionEntranceVariable(j, 'en\'')
lt = TrafficLightVariable('lt')

traffic_light_properties = {
    'traffic-light': Property(
        (j, jen, c, lt),
        And(
            And(At(c, jen), At(lt, jen)),
            And(TrafficLightColorConstraint(lt, TrafficLightColorValue(TrafficLightColor.RED)),
                Not(NextTurnRight(c)))
        ),
        Until(At(c, jen), TrafficLightColorConstraint(lt, TrafficLightColorValue(TrafficLightColor.GREEN)))
    ),

    'right-turn-priority': Property(
        (j, jen, jenn, c, cc, lt),
        And(
            And(
                And(At(c, jen), At(cc, jenn)),
                And(
                    RightOf(jen, jenn), And(
                        At(lt, jen),
                        TrafficLightColorConstraint(lt, TrafficLightColorValue(TrafficLightColor.RED))
                    ))
            ),
            NextTurnRight(c)
        ),
        Until(Next(At(c, jen)), At(cc, j))
    ),

    'opposite-turn-priority': Property(
        (j, jen, jenn, c, cc),
        And(
            And(At(c, jen), At(cc, jenn)),
            And(
                Opposite(jen, jenn),
                And(
                    NextTurnLeft(c),
                    Not(NextTurnLeft(cc))
                )
            )
        ),
        Until(Next(At(c, jen)), At(cc, j))
    )
}

stop_sign_properties = {
    'one-car-in-junction': Property(
        (j, jen, c, cc),
        And(At(c, j), Not(ObjectEqual(c, cc))),
        Not(At(cc, j))
    ),

    'right-of-priority': Property(
        (j, jen, jenn, c, cc),
        And(
            And(
                And(At(c, jen), At(cc, jenn)),
                ArithmeticConstraint(WaitingTime(c), ArithmeticOperator.EQ, WaitingTime(cc))
            ),
            RightOf(jen, jenn)
        ),
        Until(Next(At(cc, jenn)), At(c, j))
    ),

    'fifo-priority': Property(
        (j, jen, jenn, c, cc),
        And(
            And(At(c, jen), At(cc, jenn)),
            ArithmeticConstraint(WaitingTime(c), ArithmeticOperator.LT, WaitingTime(cc))
        ),
        Until(Next(At(c, jen)), At(cc, j))
    )
}

properties = traffic_light_properties if TYPE == 'traffic_light' else stop_sign_properties

scenario_files = []
for file_name in os.listdir(SCENARIO_DIR):
    if file_name.split('.')[-1] == 'bin':
        scenario_files.append(os.path.join(SCENARIO_DIR, file_name))

with open(scenario_files[0], 'rb') as f:
    proto = scenario_pb2.Scenario()
    proto.ParseFromString(f.read())
sample_scenario = Scenario(proto).sub_scenario(focus_edges_id)

monitors: Dict[str, Monitor] = dict()

for pname, prop in properties.items():
    print(f'Building monitor for {pname}')
    start_time = time.time()
    monitors[pname] = Monitor(prop, sample_scenario.static_scene,
                              sample_scenario.vehicles_id, sample_scenario.traffic_lights_id)
    end_time = time.time()
    print(f'Monitor for {pname} has been built in {round(end_time - start_time, 2)} seconds')


def check_all(scenario_path, output_file, cnt):
    cum_time = 0
    with open(scenario_path, 'rb') as f:
        proto = scenario_pb2.Scenario()
        proto.ParseFromString(f.read())
    scenario = Scenario(proto).sub_scenario(focus_edges_id)

    if isinstance(output_file, str):
        output_file = open(f'{output_file}', 'w')

    for pname in monitors:
        prop_start = time.time()
        result = monitors[pname].check(scenario)
        prop_end = time.time()
        cum_time += prop_end - prop_start
        print(f'* {pname}: {result.specification}', file=output_file)
        print(f'- premise: {result.premise}', file=output_file)
        if result.premise is True:
            printed = set()
            for sat_formula in result.premise_core:
                if str(sat_formula) not in printed:
                    print('--', sat_formula, file=output_file)
                    printed.add(str(sat_formula))
        print(f'- formula: {result.formula}', file=output_file)
        if result.formula is False:
            printed = set()
            for unsat_formula in result.formula_core:
                if str(unsat_formula) not in printed:
                    print('--', unsat_formula, file=output_file)
                    printed.add(str(unsat_formula))
        print(f'# Time cost: {prop_end - prop_start} s', file=output_file)
        print('==============', file=output_file)

    print(f'# Total time cost: {cum_time} s', file=output_file)
    print(f'#{cnt} Checking for {os.path.split(scenario_path)[-1]} has been done in {round(cum_time, 2)} seconds')


def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    cnt = 0
    pool = Pool(POOL_SIZE)
    start_time = time.time()
    print('Start to check properties')
    for full_path in scenario_files:
        cnt += 1
        save_path = f'{full_path[:-4]}_verdict.txt'
        save_path = os.path.join(SAVE_DIR, os.path.split(save_path)[-1])
        if POOL_SIZE > 1:
            pool.apply_async(check_all, (full_path, save_path, cnt))
        else:
            check_all(full_path, save_path, cnt)

    if POOL_SIZE > 1:
        pool.close()
        pool.join()
    end_time = time.time()

    print(f'Total time of all scenarios: {end_time - start_time} s')


if __name__ == '__main__':
    main()
