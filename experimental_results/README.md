# Experimental Data

### Overview

Four groups of experimental results are included:

- `4-way-stop` are the simulated runs for the 4-way stop junction listed in the paper.
- `4-way-traffic-light` are the simulated runs for the 4-way traffic light junction listed in the paper.
- `T-way-stop` are the simulated runs for the T-way stop junction shown in the attached video.
- `T-way-traffic-light` are the simulated runs for the T-way traffic light junction shown in the attached video.

### Scenario Files

#### Three Types of Files

Each folder contains a set of files whose name are encoded as 

- `scenario_{parameters}.bin`, which is the binary file for the simulated run,
- `scenario_{parameters}_info.txt`, which is the simulation information of the scenario, or
- `scenario_{parameters}_verdict.txt`, which is the verdict for the scenario.

#### Scenario Parameters

The parameter contains four parts: `{base_abstract_scenario}_{distances}_{speeds}_{rotation}`, where `base_abstract_scenario` and `rotation` determine the real abstract scenario corresponding to this concrete scenario. For example, if `base_abstract_scenario` is `d_1,d_1,d_2` and `rotation` is `r=1`, then the real abstract scenario is `base_abstract_scenario` after rotating once, which is `1_{d_1}2_{d_1}0_{d_2} = 0_{d_2}1_{d_1}2_{d_1}`

