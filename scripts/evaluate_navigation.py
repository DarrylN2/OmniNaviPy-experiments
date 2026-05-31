from OmniNaviPy.modules import Utils
from pathlib import Path

stopwatch = Utils.Stopwatch()

# set absolute path to AirSim release .sh/.exe file, or set to None if you launch AirSim separately
release_path = 'path/to/AirSimNH.sh/or/AirSimNH.exe'

# experiment setup
mllm_model = 'gemma3:27b'  # name of llama model to use, default to 'gemma3:27b', None will not use MLLM
agent_type = 'DataMap'  # options: 'MicrosoftAirSim', 'DataMap'

# trigger parameter experiment settings
n_per_difficulty = 10  # if None then will read all trajectories from file, otherwise an integer value specifying number of trajectories to evaluate PER DIFFICULTY
n_difficulties = 1  # the first n many difficulties, up to 11

progress_threshold = 1
waypoint_threshold = 4
n_points = 5

avoid_repeat_waypoints = True
obstruction_aware_waypoints = True
waypoint_aware_stuck_detection = True

experiment_label = 'small_10x1__pt1_wp4_np5__avoidrepeat__balanced_obstructionaware__wpawarestuck'

# make test name to create directory and save results to
mllm_model_name = 'None' if mllm_model is None else mllm_model.replace(':', '_')
test_name = f'Agent_{agent_type}__MLLM_{mllm_model_name}__{experiment_label}'

## set random seed for reproducibility
seed = 777
Utils.set_random_seed(seed)

# other params
pause_after_waypoint = True  # pauses querying the MLLM for n_steps after generating a new waypoint
overwrite = True  # True will delete all previous evaluations saved to file for this test_name and will instead overwrite it
                  # False will read in any already written episodes.p and continue previous evaluations until it reaches the maximum number of episodes
map_name = 'AirSimNH'  # which map to use, should correspond to that in the data directory or map in airsim_maps if real_time
mllm_device = 'cuda:0'  # load MLLM high-level policy onto this device (cuda:0, cuda:1, etc)
write_dir = Path(Utils.get_global('repository_directory'), 'ignore', 'results', test_name)
view_live_plt = True  # if True will show live visualization of depth map and state map if using MLLM
policy_name = 'DQN_beta'  # mid-level policy name to load
policy_device = 'cuda:0'  # load mid-level policy onto this device (cpu, cuda:0, cuda:1, etc)


## define the agent to evaluate, defining an abstract Agent child class with defined low-level control and sensor collection methods
# Microsoft AirSim (realistic physics-based simulator ran in real-time)
if agent_type == 'MicrosoftAirSim':
    from OmniNaviPy.modules import MicrosoftAirSim

    flags = ['-windowed']  # command line arguments to pass when launching AirSim, this uses windowed rather than full screen
    clock_speed = 10  # speed up (>1) or slow down (<1) the simulation, generally don't go higher than 10, depends on your setup
    move_speed = 1  # speed at which drone moves when taking an action, in meters per second
    navigation_frequency = 0.01 / clock_speed  # how often we check action status using the low-level control loop
    agent = MicrosoftAirSim.MicrosoftAirSim(
        release_path=release_path,
        flags=flags,
        clock_speed=clock_speed,
        move_speed=move_speed,
        navigation_frequency=navigation_frequency,
    )

# Discrete Data-Map Cache (reads data files from disk, cache in RAM, use voxels for collision detection and movement)
if agent_type == 'DataMap':
    from OmniNaviPy.modules import DataMap

    memory_saver = False  # WARNING - False will cache all data as its accessed into RAM (requires < 60gb for some larger maps), use True to save RAM
    cache_size = 4  # if memory_saver is True, then this is the parameter which controls the size of the cache for storing the number of recently accessed datamap files
    agent = DataMap.DataMap(map_name=map_name, memory_saver=memory_saver, cache_size=cache_size)

# set bounds of map that agent can move in
if map_name in ['AirSimNH']:
    x_min, x_max, y_min, y_max, z_min, z_max = -240, 241, -240, 241, 0, 20

agent.set_bounds(x_min, x_max, y_min, y_max, z_min, z_max)


## load mid-level policy to evaluate with
from OmniNaviPy.modules import Config
from OmniNaviPy.modules import Policy

if policy_name == 'DQN_beta':
    depth_sensor_name = 'DepthV1'  # name of depth sensor camera to grab data from for observations

    # load the configuration of actor, observer, and terminators which defines how the environment steps through the policy
    actor, observer, terminators = Config.beta(agent, depth_sensor_name=depth_sensor_name)

    pytorch_model_path = Path(Utils.get_global('policies_directory'), policy_name, 'pytorch_model.p')

    # load the specific policy that maps observations to actions
    policy = Policy.read_dqn_policy(pytorch_model_path, device=policy_device)


## load trajectories to evaluate against
from OmniNaviPy.modules import Trajectory
from OmniNaviPy.modules import Spawner

# read in ground truth curriculum trajectories which are saved as {difficulty: [ [start_point, waypoint1, waypoint2, ..., goal_point] ]}
curriculum_path = Path(
    Utils.get_global('repository_directory'),
    'data',
    map_name,
    'trajectories',
    'astar_1',
    'test_curriculum.p',
)

difficulties = ['low', '5', '6', '7', '8', '9', '10', '11', '12', '13', 'high'][:n_difficulties]
trajectories = Trajectory.read_curriculum(curriculum_path, difficulties, n_per_difficulty, as_list=True)

# create spawner object to call at start of each episode and load the next ground truth trajectory
spawner = Spawner.Spawner(agent, trajectories)


# make and set directory to write all output files to
import os

os.makedirs(write_dir, exist_ok=True)
episodes_write_path = Path(write_dir, 'episodes.p')

ckpt_freq = 1  # frequency of episodes to checkpoint at, None will not checkpoint
ckpt_dir = Path(write_dir, 'checkpoints')
os.makedirs(ckpt_dir, exist_ok=True)


## optionally, use MLLM for high-level logic?
from OmniNaviPy.modules import Other

others = []
generate_waypoints = mllm_model is not None  # we will only generate waypoints if using MLLM

# otherwise high-level policy is just used to visualize global map during evaluations
options = {
    'seed': seed,
    'temperature': 0,  # 0 temperature gives deterministic outputs, higher temperature gives more randomness
}

image_path = Path(write_dir, 'image.png')  # used to write image to file that is used as visual input to MLLM
state_map_path = Path(write_dir, 'image_display.png')  # used for display purposes only, not input to MLLM

others.append(
    Other.HighLevelPolicy(
        agent,
        observer=observer,
        model=mllm_model,
        cuda_device=mllm_device,
        options=options,
        image_path=image_path,
        image_path2=state_map_path,
        generate_waypoints=generate_waypoints,
        pause_after_waypoint=pause_after_waypoint,
        avoid_repeat_waypoints=avoid_repeat_waypoints,
        obstruction_aware_waypoints=obstruction_aware_waypoints,
        waypoint_aware_stuck_detection=waypoint_aware_stuck_detection,
        progress_threshold=progress_threshold,
        waypoint_threshold=waypoint_threshold,
        n_points=n_points,
        x_min=x_min,
        x_max=x_max,
        y_min=y_min,
        y_max=y_max,
    )
)


## create environment used to step through with given objects as set above
from OmniNaviPy.modules import Environment

environment = Environment.Episodic(agent, policy, spawner, actor, observer, terminators, others)


## create evaluation Run
from OmniNaviPy.modules import Run

run = Run.Evaluate(environment, ckpt_freq=ckpt_freq, ckpt_dir=ckpt_dir)
episodes = run.run(
    write_path=episodes_write_path,
    overwrite=overwrite,
    view_live_plt=view_live_plt,
    state_map_path=state_map_path,
)


## apply metrics on episodes from eval
metrics_write_path = Path(write_dir, 'metrics.json')
metrics = {}

# navigation accuracy -- percent that reached goal within a certain threshold distance
n_successes = 0

for path_idx in episodes:
    episode = episodes[path_idx]
    termination = episode.termination

    if termination == 'goal_reached':
        n_successes += 1

accuracy = 100 * n_successes / len(episodes)

print(f'finished with accuracy {accuracy:.2f}% in {stopwatch.stop():.2f} seconds')

metrics['accuracy'] = accuracy
Utils.json_write(metrics_write_path, metrics)

agent.disconnect()