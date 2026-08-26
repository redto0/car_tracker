# ekf.launch.py

## Summary

`robot_localization` EKFs. Runs on the **Pi**.

`ekf_odom` publishes `odom → base_footprint` and is always on. `ekf_map` publishes
`map → base_footprint` and is off by default.

## Subscribes

- `/odom_raw` - raw wheel odometry. **Not `/odom`** — that is Hiwonder's own EKF output.
  `controller.launch.py` is launched with `enable_odom:=false` so this filter owns the
  transform.
- `/imu` - filtered IMU. Yaw **rate** only.
- `/pose` - `ekf_map` only. slam_toolbox's map-frame estimate.

## Publishes

- `/odometry/filtered/local`, `/accel/filtered/local` (`ekf_odom`)
- `/odometry/filtered/global`, `/accel/filtered/global` (`ekf_map`)
- TF: `odom → base_footprint`, and `map → odom` when `ekf_map` is on.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `params_file` (`config/ekf.yaml`)
- `use_map_ekf` (**`false`**) - requires `slam.launch.py transform_publish_period:=0.0`.

## Notes

**The landmine.** slam_toolbox publishes `map → odom` itself. Running `ekf_map` as well
gives two broadcasters on one transform. TF does not error — it interleaves them and the
robot appears to vibrate through walls.

Start with `ekf_odom` only and let slam_toolbox own `map → odom`. `ekf_map` earns its keep
only with a *second* absolute source (GPS, AprilTags); with lidar alone it is added
latency and tuning for near-zero gain.

**Filter rules that are easy to get wrong.** `two_d_mode: true` is non-negotiable for a
ground robot. Fuse gyro yaw *rate*, never absolute yaw — no magnetometer indoors. Never
fuse the same quantity twice; that makes the filter drift smoothly while reporting tight
covariance, which looks healthy and is the worst failure mode. Keep the accelerometer out
entirely: a 1° attitude error leaks `g·sin(1°)` = 0.17 m/s² into the horizontal axes,
which is a third of this robot's real acceleration and integrates without bound.
Translational drift is corrected by lidar SLAM, not by the IMU.

**Mecanum.** `vy` is observable but the rollers slip laterally far more than
longitudinally, so it deserves a much larger covariance than `vx`. `robot_localization`
takes that from the message, not the config — if the vendor publishes zeros, add a
republisher injecting sane values.
