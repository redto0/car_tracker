# lidar.launch.py

## Summary

STL-19P lidar. Runs on the **Pi**.

Wraps Hiwonder's `peripherals/lidar.launch.py`, which dispatches on the `LIDAR_TYPE`
environment variable to the real driver — `ldlidar_stl_ros2` for the LD19 family (which
the STL-19P is), `oradar_lidar` for the MS200.

## Publishes

- `/scan` - `sensor_msgs/LaserScan` in `lidar_frame`. The vendor wrapper already uses the
  conventional name, so unlike the camera there is nothing to normalize away.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)

## Notes

`LIDAR_TYPE` is set from `robot_wiring.yaml` via `SetEnvironmentVariable`; their launch
file reads it with `os.environ[...]`, so leaving it unset is a `KeyError` that aborts the
launch.

If the map smears on every turn, suspect the lidar extrinsics in the URDF before
suspecting SLAM.
