# rviz.launch.py

## Summary

RViz. Runs on the **desktop**, never the Pi — rendering on the robot wastes CPU that Nav2
and slam_toolbox need.

## Arguments

- `use_sim_time` (`false`)
- `use_rviz` (`true`) - set false to include this file without actually starting rviz.
- `rviz_config` - defaults to slam_toolbox's shipped config, which has the map, scan and
  pose graph already set up. That is the right starting view for steps 5–6 of the build
  order. Swap for a project config once one exists.
