# compute.launch.py

## Summary

Desktop bringup. Runs on the **desktop**, not the Pi.

Everything here is advisory and safe to lose: heavy inference and visualization. Nothing
is in a control loop, so a WiFi drop degrades the map rather than crashing the robot.

## Includes

`rviz`. Perception nodes (terrain segmentation, semantic grid accumulator) land here once
they exist.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`) - must match the Pi.
- `use_rviz` (`true`)

## Notes

Prerequisites, or nothing appears:

- `chrony` synced with the Pi. Clock skew breaks TF in ways that look exactly like SLAM bugs.
- CycloneDDS with unicast peers on both machines, matching `ROS_DOMAIN_ID`. Default
  multicast discovery does not survive most WiFi APs.
