# robot.launch.py

## Summary

Full robot bringup. Runs on the **Pi**.

Everything safety-critical lives here rather than on the desktop, on one rule: if it
stopping for 500 ms would crash the robot, it runs on the Pi. WiFi will drop. The
desktop only ever produces map-frame annotations, never control.

## Includes

`description`, `controller`, `lidar`, `camera`, `ekf`, `slam`, `nav2`, `mission` — each
behind its own enable flag.

## Arguments

- `use_sim_time` (`false`) - `true` with no clock publisher hangs every node silently.
- `namespace` (`''`) - leave empty for a single robot.
- `use_description` / `use_base` / `use_lidar` / `use_camera` / `use_ekf` / `use_slam` /
  `use_nav` (`true`)
- `use_mission` (**`false`**) - with it on, the robot starts choosing its own goals the
  moment the stack comes up. Not what you want next to a desk.

## Usage

Walk the build order one step at a time:

```bash
ros2 launch car_tracker robot.launch.py use_slam:=false use_nav:=false   # steps 3-4
ros2 launch car_tracker robot.launch.py use_nav:=false                   # step 5
ros2 launch car_tracker robot.launch.py                                  # step 6
```

## Notes

Disable Hiwonder's auto-started app stack (`start_app.launch.py`) first, or two things
publish `/cmd_vel`.
