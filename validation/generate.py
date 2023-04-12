from adsv.scenario_generator.junction_scenario_generator import JunctionPatternGenerator, ScenarioGenerator
from adsv.semantic_model.scenario_configuration.applier import LgsvlApplier, LgsvlSimulationInfo
import os, datetime
import argparse

arg_parser = argparse.ArgumentParser('generate')

arg_parser.add_argument('RUNS_DIR', help='absolute path to save the simulated runs')
arg_parser.add_argument('--type', help='type of the junction',
                        choices=['stop_sign', 'traffic_light'], required=True)
arg_parser.add_argument('--way', help='way of the junction', choices=['T', '4'], required=True)
arg_parser.add_argument('--candidate_distance', nargs='+', required=True,
                        help='candidate initial distance to the entrance of the junction')
arg_parser.add_argument('--candidate_speed', nargs='+', help='candidate initial speed', required=True)
arg_parser.add_argument('--time_limit', required=True, type=float, help='maximum simulation time')


args = arg_parser.parse_args()


SCENARIO_DIR = args.RUNS_DIR
assert os.path.isabs(SCENARIO_DIR), 'RUNS_DIR should be absolute path'
MAP_NAME = 'CubeTown' if args.way == 'T' else 'SanFrancisco'
WAY = 3 if args.way == 'T' else 4
TYPE = args.type
CANDIDATE_DISTANCE = [float(d) for d in args.candidate_distance]
CANDIDATE_SPEED = [float(sp) for sp in args.candidate_speed]
TIME_LIMIT = args.time_limit


pattern = next(JunctionPatternGenerator(MAP_NAME, WAY, TYPE).junction_patterns())
print(pattern.junction.entrance_nodes_id)
generator = ScenarioGenerator(pattern, CANDIDATE_DISTANCE, CANDIDATE_SPEED)


def check_scenario(directions, distances, speeds):
    # add conditions here
    return True


def print_simulation_info(info: LgsvlSimulationInfo, output_file):
    if isinstance(output_file, str):
        output_file = open(output_file, 'w')
    print(f'Simulated time: {info.simulated_time}', file=output_file)
    print(f'Simulation time: {info.time_cost.simulation}', file=output_file)
    print(f'Total time: {info.time_cost.total}', file=output_file)
    print(f'Aggressions: {info.vehicle_aggression}', file=output_file)


def main():
    os.makedirs(SCENARIO_DIR, exist_ok=True)
    for rotate in range(WAY):
        for config, (directions, distances, speeds) in generator.scenario_configurations(TIME_LIMIT, 28, rotate,
                                                                                         time_interval=0.01):

            if check_scenario(directions, distances, speeds):
                print(f'generating {directions}, {distances}, {speeds}, r={rotate}, {datetime.datetime.now()}')

                dir_name = ','.join(f'd_{str(d+1)}' for d in directions)
                dis_name = ','.join(str(d) for d in distances)
                sp_name = ','.join(str(sp) for sp in speeds)
                file_name = f'scenario_{dir_name}_{dis_name}_{sp_name}_r={rotate}'

                scenario_path = os.path.join(SCENARIO_DIR, f'{file_name}.bin')
                scenario_info_path = os.path.join(SCENARIO_DIR, f'{file_name}_info.txt')
                if os.path.exists(scenario_path):
                    print(file_name, 'simulated')
                    continue
                scenario, scenario_info = LgsvlApplier(config).apply(address='localhost')

                with open(scenario_path, 'wb') as f:
                    f.write(scenario.dump().SerializeToString())
                print_simulation_info(scenario_info, scenario_info_path)


if __name__ == '__main__':
    main()
