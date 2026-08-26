# car_tracker

Top-level bringup for the car-tracker stack on a Hiwonder MentorPi M1. Holds the launch
tree and shared configuration; contains no nodes of its own.

## Launch files

Each is independently launchable, so the build order can be walked one subsystem at a time.

| File | Runs on | Doc |
|---|---|---|
| `robot.launch.py` | Pi | [robot](https://github.com/redto0/car_tracker_design/blob/main/deployment/robot.launch.md) |
| `compute.launch.py` | desktop | [compute](https://github.com/redto0/car_tracker_design/blob/main/deployment/compute.launch.md) |
| `include/base/controller.launch.py` | Pi | [controller](https://github.com/redto0/car_tracker_design/blob/main/deployment/controller.launch.md) |
| `include/base/description.launch.py` | Pi | [description](https://github.com/redto0/car_tracker_design/blob/main/deployment/description.launch.md) |
| `include/sensors/camera.launch.py` | Pi | [camera](https://github.com/redto0/car_tracker_design/blob/main/deployment/camera.launch.md) |
| `include/sensors/lidar.launch.py` | Pi | [lidar](https://github.com/redto0/car_tracker_design/blob/main/deployment/lidar.launch.md) |
| `include/localization/ekf.launch.py` | Pi | [ekf](https://github.com/redto0/car_tracker_design/blob/main/deployment/ekf.launch.md) |
| `include/slam/slam.launch.py` | Pi | [slam](https://github.com/redto0/car_tracker_design/blob/main/deployment/slam.launch.md) |
| `include/navigation/nav2.launch.py` | Pi | [nav2](https://github.com/redto0/car_tracker_design/blob/main/deployment/nav2.launch.md) |
| `include/navigation/mission.launch.py` | Pi | [mission](https://github.com/redto0/car_tracker_design/blob/main/deployment/mission.launch.md) |
| `include/rviz/rviz.launch.py` | desktop | [rviz](https://github.com/redto0/car_tracker_design/blob/main/deployment/rviz.launch.md) |

## Config

Launch-time **wiring** (topic names, vendor packages, environment variables) is separate
from runtime **parameters**, because remaps and package names are resolved before any node
exists and can never be ROS parameters.

| File | Read by |
|---|---|
| `robot_wiring.yaml` | the launch system, at description-build time |
| `camera_wiring.yaml` | the launch system, at description-build time |
| `ekf.yaml`, `slam_toolbox.yaml`, `nav2_params.yaml`, `camera_params.yaml` | nodes, at runtime |

## Building

`--symlink-install` is **required**: the wiring YAMLs are read eagerly from the installed
share directory, so without symlinks you would be editing a stale copy.

```bash
colcon build --symlink-install --packages-select car_tracker
```

## Running

```bash
ros2 launch car_tracker robot.launch.py
```

## Bootstrap

From the workspace root, in order:

```bash
vcs import src < src/car_tracker/car_tracker.repos
```

```bash
./src/car_tracker/scripts/prune_mentorpi.sh
```

```bash
rosdep install --from-paths src --ignore-src -r -y
```

```bash
colcon build --symlink-install
```

The prune step is **not optional**. Hiwonder ship a 17-package monorepo; without it,
`yolov5_ros2` drags in torch and `large_models` drags in LLM clients, neither of which
this project uses. The script drops `COLCON_IGNORE` **and** `AMENT_IGNORE` — colcon
honours the first, rosdep's crawler honours the second, and skipping either leaves one
tool walking into packages you meant to exclude. It is idempotent, so re-run it after
every `vcs import`.

Apt packages the vendor launch files need but declare nowhere:

```bash
sudo apt install ros-humble-imu-complementary-filter ros-humble-laser-filters ros-humble-nav2-common
```

Architecture and conventions live in
[car_tracker_design](https://github.com/redto0/car_tracker_design).
