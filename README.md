# car_tracker

Top-level bringup for the car-tracker stack on a Hiwonder MentorPi M1. Holds the launch
tree and shared configuration; contains no nodes of its own.

## Launch files

Each is independently launchable, so the build order can be walked one subsystem at a time.

| File | Runs on | Doc |
|---|---|---|
| `robot.launch.py` | Pi | [docs/robot.launch.md](docs/robot.launch.md) |
| `compute.launch.py` | desktop | [docs/compute.launch.md](docs/compute.launch.md) |
| `include/base/controller.launch.py` | Pi | [docs/controller.launch.md](docs/controller.launch.md) |
| `include/base/description.launch.py` | Pi | [docs/description.launch.md](docs/description.launch.md) |
| `include/sensors/camera.launch.py` | Pi | [docs/camera.launch.md](docs/camera.launch.md) |
| `include/sensors/lidar.launch.py` | Pi | [docs/lidar.launch.md](docs/lidar.launch.md) |
| `include/localization/ekf.launch.py` | Pi | [docs/ekf.launch.md](docs/ekf.launch.md) |
| `include/slam/slam.launch.py` | Pi | [docs/slam.launch.md](docs/slam.launch.md) |
| `include/navigation/nav2.launch.py` | Pi | [docs/nav2.launch.md](docs/nav2.launch.md) |
| `include/navigation/mission.launch.py` | Pi | [docs/mission.launch.md](docs/mission.launch.md) |
| `include/rviz/rviz.launch.py` | desktop | [docs/rviz.launch.md](docs/rviz.launch.md) |

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

## Source dependencies

```bash
vcs import src < src/car_tracker/car_tracker.repos
```

Architecture and conventions live in
[car_tracker_design](https://github.com/redto0/car_tracker_design).
