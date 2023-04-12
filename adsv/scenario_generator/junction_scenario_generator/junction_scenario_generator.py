from adsv.scenario_generator.scenario_pattern import JunctionPattern
from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration, VehicleConfiguration, Itinerary
from adsv.semantic_model.metric_graph import Junction, MetricGraph, Node, Edge
from adsv.utils.types import *
import itertools


def extend_edge_id_sequence(metric_graph: MetricGraph, edge: Edge) -> Tuple[str, str, str]:
    enter_edge = next(iter(metric_graph.enter_edges(edge.source_id)))
    exit_edge = next(iter(metric_graph.exit_edges(edge.target_id)))
    return enter_edge.id, edge.id, exit_edge.id


def check_junction_completeness(junction_pattern: JunctionPattern, way: int):
    if junction_pattern.entrance_num != way:
        return False

    prev_signal = None
    for i in range(junction_pattern.entrance_num):
        if junction_pattern.direction_num(i) != junction_pattern.entrance_num - 1:
            return False
        cur_signal = junction_pattern.entrance_signal(i)
        if i == 0:
            pass
        elif (prev_signal is None) ^ (cur_signal is None):
            return False
        elif (prev_signal is not None) and (
                cur_signal is not None) and prev_signal.signal_type != cur_signal.signal_type:
            return False
        prev_signal = cur_signal
    return True


class JunctionPatternGenerator(metaclass=multimeta):
    def __init__(self, map_name: str, way: int, junction_type: str):
        self._map_name = map_name
        self._map_loader = MapInfoLoader(map_name)
        self._way = way
        self._junction_type = junction_type
        allowed_junction_types = ['stop_sign', 'traffic_light']
        if self.junction_type not in allowed_junction_types:
            raise ValueError(
                f'the type of junction should be in {allowed_junction_types}')

    @property
    def map_name(self) -> str:
        return self._map_name

    @property
    def way(self) -> int:
        return self._way

    @property
    def junction_type(self) -> str:
        return self._junction_type

    @property
    def distances(self) -> Tuple[Number]:
        return self.distances

    @property
    def speeds(self) -> Tuple[Number]:
        return self.speeds

    def junction_patterns(self):
        for junction_id in self._map_loader.metric_graph.junctions.keys():
            junction_pattern = JunctionPattern(self._map_loader, junction_id)
            if check_junction_completeness(junction_pattern, self.way):
                if junction_pattern.entrance_signal(0) is None:
                    continue
                if self.junction_type.upper() == junction_pattern.entrance_signal(0).signal_type.name:
                    yield junction_pattern


class ScenarioGenerator(metaclass=multimeta):
    def __init__(self, scenario_pattern: JunctionPattern, candidate_distances: List[Number],
                 candidate_speeds: List[Number]):
        self._scenario_pattern = scenario_pattern
        self._candidate_distances = tuple(candidate_distances)
        self._candidate_speeds = tuple(candidate_speeds)

    @property
    def candidate_distances(self) -> Tuple[Number]:
        return self._candidate_distances

    @property
    def candidate_speeds(self) -> Tuple[Number]:
        return self._candidate_speeds

    @property
    def scenario_pattern(self):
        return self._scenario_pattern

    def _generate_vehicle_config(self, entrance_index: int,
                                 direction: int, distance: Number, speed: Number) -> VehicleConfiguration:
        edge_id_seq = extend_edge_id_sequence(self.scenario_pattern.metric_graph,
                                              self.scenario_pattern.direction(entrance_index, direction))
        end_offset = 15 * (self.scenario_pattern.entrance_num - 1)
        return VehicleConfiguration(Itinerary(distance, end_offset, edge_id_seq), speed)

    def scenario_configurations(self, time_limit: Number, seed: int, rotate: int = 0, time_interval: Number = 0.01,
                                initialization_order: Optional[List[int]] = None) \
            -> Iterable[Tuple[ScenarioConfiguration, Tuple[Tuple[Number, ...], Tuple[Number, ...], Tuple[Number, ...]]]]:
        entrance_num = self.scenario_pattern.entrance_num
        if not -entrance_num < rotate < entrance_num:
            raise ValueError(f'`rotate` should in the range [-{entrance_num - 1}, {entrance_num - 1}]. {rotate} was given')
        if initialization_order is None:
            initialization_order = range(entrance_num)
        if sorted(initialization_order) != list(range(len(initialization_order))):
            raise ValueError(f'initialization_order is not complete. {initialization_order} is given')

        def shift(i):
            return (entrance_num + i + rotate) % entrance_num

        for directions in itertools.product(*[range(self.scenario_pattern.direction_num(i)) for i in range(entrance_num)]):
            for distances in itertools.product(*([self.candidate_distances] * entrance_num)):
                for speeds in itertools.product(*([self.candidate_speeds] * entrance_num)):
                    vehicle_id_cnt = itertools.count()
                    vehicles_config = dict()
                    for entrance_index, (direction, distance, speed) in enumerate(zip(directions, distances, speeds)):
                        vehicles_config[f'c{next(vehicle_id_cnt)}'] = \
                            self._generate_vehicle_config(shift(entrance_index), direction, distance, speed)
                    yield ScenarioConfiguration(self.scenario_pattern.map_name, seed, vehicles_config,
                                                [f'c{i}' for i in initialization_order],
                                                {self.scenario_pattern.entrance_signal(i).id for i in
                                                 range(entrance_num)
                                                 if self.scenario_pattern.entrance_signal(
                                                    i).signal_type.name == 'TRAFFIC_LIGHT'},
                                                True if rotate % 2 == 1 else False,
                                                time_limit, time_interval), (directions, distances, speeds)
