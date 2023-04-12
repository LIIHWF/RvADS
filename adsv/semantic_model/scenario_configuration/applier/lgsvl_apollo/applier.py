from adsv.utils.types import *
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration
from adsv.semantic_model.scenario import DynamicScenario, Scenario, VehicleState, TrafficLightState, \
    TrafficLightColor, PhysicalState, Vector3
from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.lane_map import Lane
from adsv.utils.sequence_solver import SequenceSolver, Symbol
import math, time, json
import lgsvl
from websocket import create_connection


NAME_LIST = [
    '2e9095fa-c9b9-4f3f-8d7d-65fa2bb03921',
    '2e9095fa-c9b9-4f3f-8d7d-65fa2bb03922',
    '2e9095fa-c9b9-4f3f-8d7d-65fa2bb03923',
    '2e9095fa-c9b9-4f3f-8d7d-65fa2bb03924',
]

# (address, bridge_port, dreamview_port)
APOLLO_LIST = [
    ('172.17.0.4', 9090, 8888),
    ('172.17.0.5', 9090, 8888),
    ('10.42.0.158', 9090, 8888),
    ('10.42.0.158', 9191, 8001),
]


def encode_traffic_light_control(control_list) -> str:
    ret = ''
    for control_item in control_list:
        if control_item['action'] == 'state':
            ret += control_item['value']
        elif control_item['action'] == 'wait':
            ret += f'={control_item["value"]};'
        elif control_item['action'] == 'loop':
            ret += f'loop'
    return ret


def get_traffic_light_default_initial_state(traffic_light: lgsvl.controllable.Controllable):
    return traffic_light.default_control_policy[0]['value']


def get_traffic_lights_default_control_code(traffic_lights: Mapping[str, lgsvl.controllable.Controllable]) -> Tuple[
    str, str]:
    green_controls = set()
    red_controls = set()
    for tid, traffic_light in traffic_lights.items():
        if get_traffic_light_default_initial_state(traffic_light) == 'green':
            green_controls.add(encode_traffic_light_control(traffic_light.default_control_policy))
        elif get_traffic_light_default_initial_state(traffic_light) == 'red':
            red_controls.add(encode_traffic_light_control(traffic_light.default_control_policy))
        else:
            raise NotImplementedError
    if len(green_controls) != 1 or len(red_controls) != 1:
        raise NotImplementedError
    return next(iter(green_controls)), next(iter(red_controls))


class LgsvlTimeCost:
    def __init__(self, total: Number, simulation: Number):
        self._total = total
        self._simulation = simulation

    @property
    def total(self):
        return self._total

    @property
    def simulation(self):
        return self._simulation


class LgsvlSimulationInfo:
    def __init__(self, simulated_time: Number, time_cost: LgsvlTimeCost, vehicle_aggression: Mapping[str, int]):
        self._simulated_time = simulated_time
        self._time_cost = time_cost
        self._vehicle_aggression = MappingProxyType(vehicle_aggression)

    @property
    def simulated_time(self) -> Number:
        return self._simulated_time

    @property
    def time_cost(self) -> LgsvlTimeCost:
        return self._time_cost

    @property
    def vehicle_aggression(self) -> Mapping[str, int]:
        return self._vehicle_aggression


class LgsvlApolloApplier:
    def __init__(self, scenario_configuration: ScenarioConfiguration):
        self._scenario_configuration = scenario_configuration
        self._init_map()

    def _init_map(self):
        map_name = self.scenario_configuration.map_name
        self.map_config = MapInfoLoader(map_name)

    def _build_traffic_light_map(self, sim: lgsvl.Simulator, record_traffic_lights: Set[str]) -> Mapping[
        str, lgsvl.controllable.Controllable]:
        traffic_lights = dict()
        for tid in record_traffic_lights:
            position = self.map_config.traffic_lights_position[self.map_config.signal_mg_pb_map[tid]]
            traffic_lights[tid] = \
                sim.get_controllable(lgsvl.Vector(-position['y'], position['z'], position['x']), 'signal')
        return traffic_lights

    def _get_vehicles_states(self, sim: lgsvl.Simulator, state_mapping_seq: List[Mapping], lane_id_map):
        state_seq = []
        lane_info = sim.remote.command('map/get_lanes')
        for state_mapping in state_mapping_seq:
            lane_id, lane_offset = lane_id_map[state_mapping['lane_id']], state_mapping['lane_offset']
            seg_offset = lane_offset / self.map_config.lane_map.lanes[
                lane_id].length * self.map_config.lane_map.get_lane_section(lane_id).length
            section = self.map_config.lane_map.get_lane_section(lane_id)
            seg_id = self.map_config.sec_seg_id_map[section.id]
            state_seq.append(VehicleState(
                seg_id,
                section.get_lane_order(lane_id),
                seg_offset,
                state_mapping['longitudinal_speed'],
                state_mapping['control_speed'],
                state_mapping['longitudinal_acceleration'],
                state_mapping['control_acceleration'],
                state_mapping['target_speed'],
                state_mapping['itinerary_index'],
                state_mapping['at_stop_target'],
                state_mapping['reached_destination'],
                state_mapping['turn'],
                state_mapping['target_turn'],
                state_mapping['lane_offset'],
                lane_info[state_mapping['lane_id']]['length'] - state_mapping['lane_offset'],
                PhysicalState(
                    Vector3(state_mapping['physical_state']['position']['x'], state_mapping['physical_state']['position']['y'],
                            state_mapping['physical_state']['position']['z']),
                    Vector3(state_mapping['physical_state']['velocity']['x'], state_mapping['physical_state']['velocity']['y'],
                            state_mapping['physical_state']['velocity']['z'])
                )
            ))
        return state_seq

    @property
    def scenario_configuration(self) -> ScenarioConfiguration:
        return self._scenario_configuration

    def apply(self, address='localhost', port=8181): # -> Tuple[Scenario, LgsvlSimulationInfo]:
        apply_start = time.time()
        lane_sequences = self._get_lane_sequences()
        initial_speeds = {vid: config.init_speed
                          for vid, config in self.scenario_configuration.vehicles_configuration.items()}

        sim = lgsvl.Simulator(address, port, )

        sim.remote.command('simulator/load_local_scene',
                           {'scene': self.scenario_configuration.map_name, 'seed': self.scenario_configuration.seed})

        traffic_lights = dict()
        record_traffic_lights = {tid for tid in self.scenario_configuration.traffic_lights}

        if len(record_traffic_lights) > 0:
            traffic_lights = self._build_traffic_light_map(sim, record_traffic_lights)
            green_control_code, red_control_code = get_traffic_lights_default_control_code(traffic_lights)

            if self.scenario_configuration.reverse_traffic_lights:
                for traffic_light in traffic_lights.values():
                    if get_traffic_light_default_initial_state(traffic_light) == 'green':
                        traffic_light.control(red_control_code)
                    else:
                        traffic_light.control(green_control_code)

            traffic_lights_uids = []
            for tid in record_traffic_lights:
                traffic_lights_uids.append(traffic_lights[tid].uid)


        agents = self._create_agents_and_apply_itinerary(sim, self.scenario_configuration.initialization_order,
                                                         lane_sequences, initial_speeds)
        input('Ready to run')
        sim.run(self.scenario_configuration.time_limit)
        sim.close()
        apply_finish = time.time()

        # return Scenario(self.scenario_configuration, self.map_config.static_scene, dynamic_scenario), \
        #     LgsvlSimulationInfo(
        #         sim_time_end - sim_time_start,
        #         LgsvlTimeCost(apply_finish - apply_start, simulation_finish - simulation_start),
        #         aggressions)

    def _get_self_sim_lane_id_map(self, sim: lgsvl.Simulator):
        self_unpaired = [lane for lane in self.map_config.lane_map.lanes.values()]
        sim_lane_info = sim.remote.command('map/get_lanes')
        sim_unpaired = [lane_id for lane_id in sim_lane_info.keys()]
        self_sim_lane_id_map = dict()
        sim_self_lane_id_map = dict()

        def lane_eq(lane: Lane, sim_lane):
            self_point_seq = [(v.x, v.y) for v in lane.reference_line.vertices]
            sim_point_seq = [(p['x'], p['y']) for p in sim_lane['positions']]
            if len(self_point_seq) != len(sim_point_seq):
                return False
            for p1, p2 in zip(self_point_seq, sim_point_seq):
                if abs(p1[0] - p2[0]) > 1 or abs(p1[1] - p2[1]) > 1:
                    return False
            return True

        while len(self_unpaired) > 0:
            matching_self_lane = self_unpaired.pop()
            for i in range(len(sim_unpaired)):
                sim_lane = sim_lane_info[sim_unpaired[i]]
                if lane_eq(matching_self_lane, sim_lane):
                    self_sim_lane_id_map[matching_self_lane.id] = sim_unpaired[i]
                    sim_self_lane_id_map[sim_unpaired[i]] = matching_self_lane.id
                    sim_unpaired.pop(i)
                    break
            else:
                raise ValueError(f'Unmatched lane: {matching_self_lane}')
        return self_sim_lane_id_map, sim_self_lane_id_map

    def _create_agents_and_apply_itinerary(self, sim: lgsvl.Simulator,
                                           initialization_order: Tuple[str, ...],
                                           lane_sequences: Mapping[str, Tuple[Number, List[str], Number]],
                                           initial_speeds: Mapping[str, Number]) -> Mapping[str, lgsvl.agent.Agent]:
        agents = dict()
        lane_id_map, _ = self._get_self_sim_lane_id_map(sim)
        lane_info = sim.remote.command('map/get_lanes')
        for i, (vid, vname, (address, bridge_port, dreamview_port)) in enumerate(zip(initialization_order, NAME_LIST, APOLLO_LIST)):
            start_offset, lane_id_seq, end_offset = lane_sequences[vid]
            agent: lgsvl.agent.EgoVehicle = sim.add_agent(vname, lgsvl.AgentType.EGO)
            lane_id_seq = [lane_id_map[lane_id] for lane_id in lane_id_seq]
            start_lane = self.map_config.lane_map.lanes[lane_id_seq[0]]
            start_xy, start_heading = self._set_agent_state(sim, agent, lane_id_seq[0], start_lane.length - start_offset)
            agent.connect_bridge(address, bridge_port)

            end_lane = self.map_config.lane_map.lanes[lane_id_seq[-1]]
            end_xy = end_lane.reference_line.get_xy_by_sl(end_offset, 0)
            ws_address = 'ws://' + address + ':' + str(dreamview_port) + '/websocket'
            ws = create_connection(ws_address)

            ws.send(json.dumps({
                "end": {
                    "x": end_xy.x,
                    "y": end_xy.y,
                    "z": 0
                },
                "start": {
                    "x": start_xy.x,
                    "y": start_xy.y,
                    "z": 0,
                    "heading": start_heading
                },
                "type": "SendRoutingRequest",
                "waypoint": []
            }))
            ws.close()

            agents[vid] = agent

        # sim.run(0.05)  # get location

        RESTART_MODULE = ['Localization', 'Transform', 'Prediction', 'Planning', 'Control']
        for i, (vid, vname, (address, bridge_port, dreamview_port)) in enumerate(
                zip(initialization_order, NAME_LIST, APOLLO_LIST)):
            ws_address = 'ws://' + address + ':' + str(dreamview_port) + '/websocket'
            ws = create_connection(ws_address)
            for module in RESTART_MODULE:
                ws.send(json.dumps({
                    'action': 'STOP_MODULE',
                    'type': 'HMIAction',
                    'value': module
                }))
            time.sleep(1)
            for module in RESTART_MODULE:
                ws.send(json.dumps({
                    'action': 'START_MODULE',
                    'type': 'HMIAction',
                    'value': module
                }))
            ws.close()

        return agents

    def _set_agent_state(self, sim: lgsvl.Simulator, agent: lgsvl.agent.Agent, lane_id: str, offset: Number):
        front2mid = (agent.bounding_box.max - agent.bounding_box.min).z / 2
        lane = self.map_config.lane_map.lanes[lane_id]
        if not (front2mid <= offset <= lane.length): raise ValueError('offset is out of bound')

        xy_pos = lane.reference_line.get_xy_by_sl(offset - front2mid, 0)
        start_vec = lane.reference_line.get_line_segment_by_s(offset - front2mid).vec
        heading = start_vec.angle.r
        sim_state = agent.state
        sim_state.transform.position = lgsvl.Vector(-xy_pos.y, 10, xy_pos.x)
        sim_state.transform.rotation = lgsvl.Vector(0, -heading / math.pi * 180, 0)
        # sim_state.transform = sim.map_point_on_lane(lgsvl.Vector(-xy_pos.y, 0, xy_pos.x))

        agent.state = sim_state
        return xy_pos - 3 * start_vec.unit, heading

    def _get_lane_sequences(self) -> Mapping[str, Tuple[Number, List[str], Number]]:
        lane_sequences = dict()
        for vid, vconfig in self.scenario_configuration.vehicles_configuration.items():
            segments_id = vconfig.itinerary.segment_id_seq

            for lane_index in [-1, 0]:
                lanes_seq = []
                lane_neighbors = {
                    Symbol(lane.id): {
                        Symbol(lid) for lid in lane.successors_id} for lane in
                    self.map_config.lane_map.lanes.values()
                }
                for i, segment_id in enumerate(segments_id):
                    ordered_lanes = self.map_config.lane_map.sections[
                        self.map_config.seg_sec_id_map[segment_id]].ordered_lanes
                    lanes_seq.append(set(
                        Symbol(lane.id) for lane in (ordered_lanes if i < 2 else ordered_lanes[lane_index:])
                    ))
                seq_solver = SequenceSolver(lanes_seq)
                lane_seq = seq_solver.solve(lane_neighbors)
                if lane_seq is not None:
                    break
            if lane_seq is None: raise ValueError(f'Given itinerary of {vid} is not connected')
            lane_seq: List[Any] = [lsym.id for lsym in lane_seq]
            start_lane_id, end_lane_id = lane_seq[0], lane_seq[-1]
            start_offset, end_offset = vconfig.itinerary.start_offset, vconfig.itinerary.end_offset
            start_section = self.map_config.lane_map.get_lane_section(start_lane_id)
            end_section = self.map_config.lane_map.get_lane_section(end_lane_id)
            if start_offset < 0 or start_offset > start_section.length:
                raise ValueError(f'Start offset is out of bound. '
                                 f'The segment has length {start_section.length}, but {start_offset} was given')
            if end_offset < 0 or end_offset > end_section.length:
                raise ValueError(f'End offset is out of bound. '
                                 f'The segment has length {end_section.length}, but {end_offset} was given')
            lane_sequences[vid] = (start_offset, lane_seq, end_offset)
        return lane_sequences
