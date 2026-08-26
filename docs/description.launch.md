# description.launch.py

## Summary

`robot_state_publisher` broadcasting `base_footprint` → sensor frames from Hiwonder's
mecanum xacro. Runs on the **Pi**.

Wraps `mentorpi_description` rather than maintaining a second URDF that will drift out of
sync with theirs.

## Publishes

- `/robot_description`
- `/joint_states`
- TF: `base_footprint` → `lidar_frame`, `imu_link`, camera frames

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)

## Notes

**Verify the URDF against the physical robot before trusting any of it.** A 5 cm or 3°
lidar extrinsic error smears the map on every turn and is indistinguishable from a SLAM
tuning problem — one of the most expensive mistakes available on this project.

```bash
ros2 run tf2_tools view_frames
```
