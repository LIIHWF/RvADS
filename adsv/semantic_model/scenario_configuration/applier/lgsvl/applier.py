from adsv.utils.types import *
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration
from adsv.semantic_model.scenario import DynamicScenario, Scenario, VehicleState, TrafficLightState, \
    TrafficLightColor, PhysicalState, Vector3
from adsv.map_manager import MapInfoLoader
from adsv.semantic_model.lane_map import Lane
from adsv.utils.sequence_solver import SequenceSolver, Symbol
import math, time
import lgsvl


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


class LgsvlApplier:
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

    def apply(self, address='localhost', port=8181) -> Tuple[Scenario, LgsvlSimulationInfo]:
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
            sim.remote.command('signals/start_record', {'signals': traffic_lights_uids})

        agents = self._create_agents_and_apply_itinerary(sim, self.scenario_configuration.initialization_order,
                                                         lane_sequences, initial_speeds)
        _, lane_id_map = self._get_self_sim_lane_id_map(sim)

        reached_destination = {
            agent.uid: False for agent in agents.values()
        }

        def check_reach_destination(_agent):
            reached_destination[_agent.uid] = True
            if all(reached_destination.values()):
                sim.stop()

        for aid, agent in agents.items():
            agent.remote.command("agent/on_destination_reached", {"uid": agent.uid})
            agent.simulator._add_callback(agent, "destination_reached", check_reach_destination)

        time_scale = 0.01 / self.scenario_configuration.time_interval
        simulation_start = time.time()
        sim_time_start = sim.current_time
        sim.run(self.scenario_configuration.time_limit, time_scale)
        sim_time_end = sim.current_time
        simulation_finish = time.time()

        agents_state_seq = dict()
        aggressions = dict()
        agent_seq_length = 0
        for aid, agent in agents.items():
            if self.scenario_configuration.vehicles_configuration[aid].init_speed < 0:
                continue
            state_mapping_seq = sim.remote.command("vehicle/get_state_record", {"uid": agent.uid})
            agents_state_seq[aid] = self._get_vehicles_states(sim, state_mapping_seq, lane_id_map)
            agent_seq_length = len(agents_state_seq[aid])
            aggressions[aid] = sim.remote.command("vehicle/get_aggression", {"uid": agent.uid})

        color_map = {
            'green': TrafficLightState(TrafficLightColor.GREEN),
            'yellow': TrafficLightState(TrafficLightColor.YELLOW),
            'red': TrafficLightState(TrafficLightColor.RED)
        }

        traffic_lights_state_seq = dict()
        if len(record_traffic_lights) > 0:
            original_traffic_lights_state_seq = sim.remote.command('signals/get_record')
            for tid in record_traffic_lights:
                uid = traffic_lights[tid].uid
                traffic_lights_state_seq[tid] = \
                    [color_map[cl] for cl in original_traffic_lights_state_seq[uid]][:agent_seq_length]

        dynamic_scenario = DynamicScenario(agents_state_seq, traffic_lights_state_seq)
        sim.close()
        apply_finish = time.time()

        return Scenario(self.scenario_configuration, self.map_config.static_scene, dynamic_scenario), \
            LgsvlSimulationInfo(
                sim_time_end - sim_time_start,
                LgsvlTimeCost(apply_finish - apply_start, simulation_finish - simulation_start),
                aggressions)

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
        for i, vid in enumerate(initialization_order):
            start_offset, lane_id_seq, end_offset = lane_sequences[vid]
            # if i == 0:
            #     agent: lgsvl.agent.NpcVehicle = sim.add_agent('Sedan', lgsvl.AgentType.NPC, color=lgsvl.Vector(0.529, 0.807, 1)) # blue
            # elif i == 1:
            #     agent: lgsvl.agent.NpcVehicle = sim.add_agent('Sedan', lgsvl.AgentType.NPC,
            #                                                   color=lgsvl.Vector(0.9569, 0.8157, 0))  # yellow
            # else:
            #     agent: lgsvl.agent.NpcVehicle = sim.add_agent('Sedan', lgsvl.AgentType.NPC, color=lgsvl.Vector(0.65, 0.65, 0.65))
            agent: lgsvl.agent.NpcVehicle = sim.add_agent('Sedan', lgsvl.AgentType.NPC, color=lgsvl.Vector(1, 1, 1))

            lane_id_seq = [lane_id_map[lane_id] for lane_id in lane_id_seq]

            sim.remote.command('vehicle/lane_state/set',
                               {'uid': agent.uid, 'lane_id': lane_id_seq[0],
                                'offset': lane_info[lane_id_seq[0]]['length'] - start_offset})

            if initial_speeds[vid] < 0:
                agent.follow_closest_lane(True, 0.00001, False)
            else:
                sim.remote.command("vehicle/follow_itinerary", {
                    'follow': True,
                    'uid': agent.uid,
                    'itinerary': lane_id_seq,
                    'end_offset': end_offset,
                    'initial_speed': initial_speeds[vid]
                })
                # sim.remote.command("vehicle/fix_rotation", {
                #     'uid': agent.uid
                # })

            agents[vid] = agent
        return agents

    def _set_agent_state(self, sim: lgsvl.Simulator, agent: lgsvl.agent.Agent, lane_id: str, offset: Number):
        front2mid = (agent.bounding_box.max - agent.bounding_box.min).z / 2
        # front2mid = sim.remote.command('vehicle/half_length/get', {'uid': agent.uid}) - 0.1
        lane = self.map_config.lane_map.lanes[lane_id]
        if not (front2mid <= offset <= lane.length): raise ValueError('offset is out of bound')

        xy_pos = lane.reference_line.get_xy_by_sl(offset - front2mid, 0)
        sim_state = agent.state
        sim_state.transform = sim.map_point_on_lane(lgsvl.Vector(-xy_pos.y, 0, xy_pos.x))
        # sim_state.transform.position = lgsvl.Vector(-xy_pos.y, 100, xy_pos.x)
        # hit = sim.raycast(sim_state.position, lgsvl.Vector(0, -1, 0), 1)
        # assert hit is not None, 'Raycast returns None.'
        # sim_state.transform.position.x, sim_state.transform.position.y, sim_state.transform.position.z = \
        #     hit.point.x, hit.point.y, hit.point.z
        # sim_state.rotation.y = - lane.reference_line.get_line_segment_by_s(
        #     offset - front2mid).vec.angle.r / math.pi * 180

        agent.state = sim_state
        # position = agent.state.transform.position
        # print(xy_pos, position.z, -position.x)
        # print(lane.reference_line.get_sl_by_xy(position.z, -position.x).s + front2mid, lane.length)

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
