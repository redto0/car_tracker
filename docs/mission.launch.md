# mission.launch.py

## Summary

Mission manager. Runs on the **Pi**.

Thin wrapper over `car_tracker_path_resolver`'s own launch file, so the node stays
independently launchable from its package and this tree only supplies bringup-level
arguments.

The node decides *where* to go; Nav2 plans and follows. See
[path_resolver.md](https://github.com/redto0/car_tracker_path_resolver/blob/master/path_resolver.md).

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `auto_explore` (`true`) - frontier detection is currently a stub, so this idles.
