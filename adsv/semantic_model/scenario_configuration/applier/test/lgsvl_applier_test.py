import unittest
from adsv.utils.types import *
from adsv.semantic_model.scenario_configuration import ScenarioConfiguration, VehicleConfiguration, Itinerary
from adsv.semantic_model.scenario_configuration.applier import LgsvlApplier
import json


class TestApplier(unittest.TestCase):
    def test_cubetown(self):
        scenario_configuration = ScenarioConfiguration('CubeTown', {
            'c1': VehicleConfiguration(Itinerary(20, 20, ['e17', 'e8', 'e12']), 0),
            'c2': VehicleConfiguration(Itinerary(20, 20, ['e9', 'e2', 'e3']), 0)
        }, 15, 0.1)
        s = LgsvlApplier(scenario_configuration).apply()
        print(s.dump())


if __name__ == '__main__':
    unittest.main()
