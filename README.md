# RvADS: Simulation-based Validation for Autonomous Driving Systems

RvADS is a simulation-based validation framework for autonomous driving systems which contains three components: 1) Simulator, 2) Scenario Generator, and 3) Monitor.

 <img src="images/framework.png" alt="framework" style="zoom:50%;" />

## Experimental Data

There are 4 groups of experimental data located in [experiments](./experiments), including `4-way-stop`, `4-way-traffic-light`, `T-way-stop`, and `T-way-traffic-light`. They are the raw data for the experiments listed in the paper and the attached video. 



## Usage

### Requirements

RvADS has been tested in the following environments. Please confirm compatibility when using other software versions.

- **Ubuntu 22.04 (x86_64)**
- **Bazel release 5.2.0**: Please download [here](https://github.com/bazelbuild/bazel/releases/tag/5.2.0) and add it to `$PATH`, or refer https://bazel.build/ to install.
- **Python 3.9** 
  (PyPy is recommended for performance reasons. The official Python interpreter also works but with  efficiency loss)
- **Python Packages**:
  - **LGSVL Python API 2021.3**: Please refer [here](https://github.com/lgsvl/PythonAPI) to install.
  - **Z3 Solver**: `pip install z3-solver`

### Simulator

The executable Extended Simulator is in the release of this repository (`extended-simulator.zip`). Please run

````shell
$ ./run-simulator.sh
````

after unzipping and click the start button.

The code for the extension is located in `svl-extension/`. One can also follow the instructions detailed [here](https://www.svlsimulator.com/docs/installation-guide/build-instructions/) to build it along with the simulator.



### Scenario Generator

After starting the Simulator, scenarios for a 4-way stop junction can be generated using the following command. The simulated runs will be saved to `experiments/new_scenarios` as the argument specified.

```shell
$ bazel run -- //validation:generate \
            --type stop_sign \
            --way 4 \
            --candidate_distance 0.3 20 \
            --candidate_speed 0 \
            --time_limit 30 \
            /absolute/path/to/experiments/new_scenarios
# Note that absolute path is needed
```



Here is the detailed usage of  `generate`:

```
usage: generate [-h] --type {stop_sign,traffic_light} --way {T,4} 
                     --candidate_distance CANDIDATE_DISTANCE [CANDIDATE_DISTANCE ...] 
                     --candidate_speed CANDIDATE_SPEED [CANDIDATE_SPEED ...]
                     --time_limit TIME_LIMIT
                     RUNS_DIR

positional arguments:
  RUNS_DIR              absolute path to save the simulated runs

optional arguments:
  -h, --help            show this help message and exit
  --type {stop_sign,traffic_light}
                        type of the junction
  --way {T,4}           way of the junction
  --candidate_distance CANDIDATE_DISTANCE [CANDIDATE_DISTANCE ...]
                        candidate initial distance to the entrance of the junction
  --candidate_speed CANDIDATE_SPEED [CANDIDATE_SPEED ...]
                        candidate initial speed
  --time_limit TIME_LIMIT
                        maximum simulation time
```



### Monitor

The following command produces the verdicts to `experiments/st_verdicts` for all the simulated runs located in `experiments/st_scenarios`, where the scenarios are for a 4-way stop junction.

```shell
$ bazel run -- //validation:check --type stop_sign --way 4 \
        /absolute/path/to/experiments/4-way-stop \
        /absolute/path/to/experiments/4-way-stop-verdicts
# Note that absolute path is needed
```

Multiple runs can be checked in parallel by specifying the argument `pool_size` (16 runs for the following case).

```shell
$ bazel run -- //validation:check --type stop_sign --way 4 --pool_size 16 \
                                  /absolute/path/to/experiments/4-way-stop \
                                  /absolute/path/to/experiments/4-way-stop-verdicts
```

Note:

- PyPy is recommend for this step. It will significantly improve the checking performance.

- (CentOS may cause this problem) If the execution is abnormal, please ensure `third-party/ltl2fsm/ltl2fsm "a"` can be executed correctly. Otherwise, please refer [here](https://ltl3tools.sourceforge.net/) to replace the third party tools with the executable ones.



Here is the detailed usage of `check`:

```
usage: check [-h] --type {stop_sign,traffic_light} --way {4,T} [--pool_size POOL_SIZE] RUNS_DIR VERDICTS_DIR

positional arguments:
  RUNS_DIR              absolute path to simulated runs
  VERDICTS_DIR          absolute path to save the verdicts

optional arguments:
  -h, --help            show this help message and exit
  --type {stop_sign,traffic_light}
                        type of the junction
  --way {4,T}           number of way for the junction
  --pool_size POOL_SIZE
                        process pool size N (allow simultaneous checking of N runs, default=1)
```



## License

AGPL v3.0

(Please know the implication of LICENSE before using or contributing to the code)

