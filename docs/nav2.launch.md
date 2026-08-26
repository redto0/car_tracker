# nav2.launch.py

## Summary

Nav2. Runs on the **Pi**.

Deliberately on the Pi, not the desktop. Nav2 is not the heavy part — neural inference is
— and a global replan stalling behind a WiFi hiccup while the robot is moving puts it in a
wall.

Wraps `nav2_bringup/navigation_launch.py`, which brings up the controller, planner,
smoother, behavior, bt_navigator, velocity_smoother and their lifecycle manager.
Localization is **not** included: slam_toolbox provides `map → odom`, so there is no AMCL.

## Subscribes

- `/scan`, `/odom`, `/map`

## Publishes

- `/cmd_vel`
- `/plan`, costmaps, and the usual Nav2 topic surface

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `params_file` (`config/nav2_params.yaml`)
- `autostart` (`true`)
- `use_composition` (**`True`**, capitalized) - see below.

## Notes

Two `nav2_bringup` contract details, both found by running it rather than parsing it.

**`use_composition` must be capitalized `True`/`False`.** `navigation_launch.py` does
`IfCondition(PythonExpression(['not ', use_composition]))`, which evaluates the string as
Python. Lowercase `true` raises `NameError: name 'true' is not defined` at launch.
Upstream's own default is `'False'` for this reason.

**`navigation_launch.py` does not create the component container it loads into** —
`bringup_launch.py` normally does. Including it standalone with composition on starts
*nothing at all, silently*, with a clean exit. This file creates an
`rclcpp_components/component_container_isolated` named `nav2_container` and passes the
name through.

## Planner and controller

`SmacPlanner2D` — A* with costmap downsampling, correct for the holonomic M1.
`SmacPlannerHybrid` is the Ackermann one and is not wanted here.

DWB with `vy` samples enabled, since M1 is mecanum and the upstream TurtleBot defaults pin
`vy` to zero. MPPI is an upgrade if the Pi has headroom. Strafe mostly buys docking and
fine positioning, not cruising.
