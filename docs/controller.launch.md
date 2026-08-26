# controller.launch.py

## Summary

MentorPi base driver: motors, wheel encoders, IMU. Runs on the **Pi**.

Wraps Hiwonder's `controller/controller.launch.py` rather than replacing it — the STM32
serial protocol is the tedious part and theirs works.

## Publishes (via the vendor stack)

- `/odom_raw` - raw wheel odometry. What `ekf.launch.py` consumes.
- `/odom` - **their** EKF output when `enable_odom:=true`. Ours publishes here otherwise.
- `/imu` - filtered IMU. Chain is `ros_robot_controller` → `imu_calib/apply_calib` →
  `/imu_corrected` → `imu_complementary_filter` → `/imu`.

## Subscribes

- `/cmd_vel` - `geometry_msgs/Twist`.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `enable_odom` (**`false`**) - see below.

## Notes

Two things this file exists to get right.

**`enable_odom:=false`.** Their `controller.launch.py` runs its own `robot_localization`
`ekf_node`, fusing `odom_raw` + `odom_rf2o` + `imu` and publishing `/odom` plus the
`odom → base_footprint` transform. Leaving it on alongside our `ekf_odom` puts two EKFs
and two broadcasters on that transform. TF does not reject that — it interleaves them and
the robot appears to vibrate through walls. Set it true only if you want their filter
*instead* of ours, and then do not launch `ekf.launch.py` at all.

**Environment variables.** Their launch files read `os.environ['need_compile']` as a plain
dict lookup, so an unset variable is a `KeyError` that aborts the launch before anything
starts. Set here from `robot_wiring.yaml` so it cannot be forgotten. `need_compile` must
be `'True'`; `'False'` falls back to hardcoded `/home/ubuntu/ros2_ws` paths.
