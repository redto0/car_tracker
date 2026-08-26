# slam.launch.py

## Summary

`slam_toolbox` in online async mode. Runs on the **Pi**.

Async drops scans it cannot process in time rather than falling behind, which is the right
trade on a Pi 5 sharing CPU with Nav2.

## Subscribes

- `/scan` - `sensor_msgs/LaserScan`.

## Publishes

- `/map` - `nav_msgs/OccupancyGrid`, latched.
- `/map_metadata`
- `/pose` - `geometry_msgs/PoseWithCovarianceStamped`, the map-frame estimate. `ekf_map`
  consumes this when the dual-EKF setup is enabled.
- TF: `map → odom`, unless `transform_publish_period:=0.0`.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `params_file` (`config/slam_toolbox.yaml`)
- `mode` (`mapping`) - or `localization` to relocalize in a serialized map.
- `transform_publish_period` (`0.02`) - `0.0` disables the `map → odom` broadcast, which
  is **required** before enabling `ekf_map`.

## Usage

```bash
ros2 launch car_tracker slam.launch.py
ros2 launch car_tracker slam.launch.py mode:=localization
```

Save a map:

```bash
ros2 service call /slam_toolbox/serialize_map slam_toolbox/srv/SerializePoseGraph "{filename: '/maps/lab'}"
```

Prefer serialize/deserialize over `map_server` + AMCL: it keeps the pose graph, so the map
stays extendable instead of frozen.

## Algorithm

Three separable outputs people conflate: a **pose correction** (`map → odom`, what nav
consumes), a **map**, and **loop closure** (what keeps the map from smearing).

Scan matching finds the rigid transform aligning a new scan to the map — the offset
between that and odom *is* `map → odom`. A pose graph stores poses as nodes and
scan-match constraints as edges, adding nodes only after enough travel
(`minimum_travel_distance` / `minimum_travel_heading`). Loop closure matches against older
nearby nodes and re-optimises the whole graph, which bounds long-term drift.

## Notes

**Debug in this order.** Resist blaming SLAM; most reports are 1–4.

1. TF tree connected and single-rooted (`ros2 run tf2_tools view_frames`).
2. Lidar extrinsics match physical measurement. A 5 cm or 3° error smears the map on every
   turn and looks exactly like a tuning problem.
3. Scan timestamps sane (`ros2 topic delay /scan`). Bad timestamps make the map *shear*
   when rotating — the worst SLAM bug.
4. Odometry sane alone: drive a 2 m square, expect <10 cm drift. Bad odom gives SLAM
   nothing to correct from and loop closure fails.
5. *Then* tune SLAM.
