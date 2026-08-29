# car_tracker

Main repo for the ROS side of the car-tracker stack, running on a Hiwonder **MentorPi M1**
(mecanum, Raspberry Pi 5, ROS 2 Humble). Holds the launch tree and shared configuration;
contains no nodes of its own.

Architecture, conventions and per-node docs live in
[car_tracker_design](https://github.com/redto0/car_tracker_design).

### Dependencies

Most dependencies for car_tracker are described in cmake and package files.
This means that if you are missing a package somewhere, it will error for you.

To ensure you have all source nodes, be sure to `vcs import` `car_tracker.repos` in your
workspace `/src`. Make sure to then Rosdep all these source nodes to drag in all binary
dependencies.

**Two exceptions where rosdep will not save you**, because Hiwonder's `peripherals`
package ships an untouched `package.xml` template that declares no dependencies at all.
Both are now declared on `car_tracker` so rosdep does pull them in, but if you build only
part of the workspace you will hit them:

- `laser_filters` — used by `peripherals/lidar.launch.py`
- `imu_complementary_filter` — used by `peripherals/imu_filter.launch.py`

The depth camera driver, `ascamera`, is **not obtainable from the internet** — see
[The depth camera](#the-depth-camera) below.

#### Where each dependency comes from

| Source | What |
|---|---|
| **apt** (public) | ROS 2 Humble, `navigation2`, `nav2_bringup`, `slam_toolbox`, `laser_filters`, `imu_complementary_filter`, `joy`, `teleop_twist_joy`, `image_proc`, `image_transport_plugins`, `rmw_cyclonedds_cpp`, `rviz2` |
| **`car_tracker.repos`** (public GitHub, anonymous HTTPS works) | `robot_localization`, `ldlidar_stl_ros2`, `imu_calib`, `robot_state_controller`, `MentorPiDrivers`, `semantic_segmentation_layer`, `camera_to_ground_projection` |
| **`car_tracker.repos`** (**private**, needs an authorised SSH key) | `car_tracker_path_resolver` |
| **Not on the internet at all** | `ascamera` — binary blob, ships only inside Hiwonder's ~12 GB VM image. Must be self-hosted to be reproducible. |

Do not add `slam_toolbox` to `.repos`. Upstream's `ros2` branch is 2.10.0 and targets
Jazzy; Humble ships 2.6.10 via apt. Both declare `project(slam_toolbox)`, so the source
copy shadows the apt one and the build breaks in confusing ways.

## Building

1. Install ROS2 Humble, and ROS2 tools
2. Install `sudo apt install python3-vcstool` & `sudo apt install python3-rosdep2`
3. Create your ros workspace, a dir of `ws_name/src`
4. In `src`, clone this repo with Git
5. Still in `src`, run `cat car_tracker/car_tracker.repos | vcs import` to import source
   dependencies. One entry (`car_tracker_path_resolver`) is a private repo, so your SSH key
   must be authorised on it or the import fails for that repo only
6. Cd to the workspace root, and run `rosdep install --from-paths src --ignore-src -r -y` to
   install binary dependencies
7. Remember to source ROS2 before building `source /opt/ros/humble/setup.bash` and add to
   your bashrc with `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`
8. Still in workspace root, run `colcon build --symlink-install` to build the workspace.
   **`--symlink-install` is required**, not optional: the wiring YAMLs are read eagerly from
   the installed share directory, so without symlinks you edit a stale copy and your changes
   appear to do nothing
9. Make sure your user is a part of the unix `dialout`, `video` and `input` groups. This
   allows it to connect to USB devices. Log out and back in afterwards — group changes do not
   apply to an existing session
10. Install the udev rules so the drivers find their devices, then replug:
    `./docker/install-udev.sh` and verify with `ls -l /dev/rrc /dev/ldlidar`.
    The vendor drivers open **symlinks**, not raw devices, and no rule shipped by Hiwonder
    creates `/dev/ldlidar` even though the LD19 launch opens it

The repo should now be built, and launch-able on the robot or the desktop.

### On the Pi, ROS runs in Docker

The Pi was reflashed with **Ubuntu 26.04** and Humble is jammy-only, so there is no
`ros-humble-*` for the host. Steps 1-8 above happen **inside the container**; the 26.04 host
only provides kernel, udev and network. The desktop is jammy and runs Humble natively, so it
needs no container.

```bash
cp src/car_tracker/docker/env.example .env      # then set PI_IP / DESKTOP_IP
docker compose -f src/car_tracker/docker/docker-compose.yml up -d --build ros
docker compose -f src/car_tracker/docker/docker-compose.yml exec ros colcon build --symlink-install
```

The workspace is bind-mounted, so an edit on the Pi needs a `colcon build`, not an image
rebuild. Full detail, and the order the setup steps have to happen in, is in
[deployment.md](https://github.com/redto0/car_tracker_design/blob/main/deployment.md).

### The depth camera

`ascamera` drives the Angstrong HP60C and **cannot be fetched from anywhere**. It ships as
`linux_ros.pkg`, a binary archive of closed-source libraries, distributed only inside
Hiwonder's ~12 GB VMware image. There is no repo to clone and no apt package.

To make a fresh workspace reproducible, that pkg has to be **uploaded to a repo of our own**
and added to `car_tracker.repos`. Until then this one step is manual and undocumented by
upstream. Its build dependencies (`libgflags-dev`, `nlohmann-json3-dev`,
`libgoogle-glog-dev`, `camera-info-manager`, `image-publisher`) are already in the
Dockerfile.

**Check the architecture before trusting it**: the vendor's own docs show the libraries under
`arm-linux-gnueabihf`, which is 32-bit ARM. The Pi 5 and our container are both arm64 and a
32-bit `.so` cannot link into a 64-bit binary. Run `ls linux_ros/libs/lib/` and confirm an
`aarch64-linux-gnu` directory exists.

Nothing else in the stack depends on the camera, so the rest can be brought up without it
using `use_camera:=false`.

## Launching

### Robot

Brings up description, base, lidar, camera, EKF, SLAM, Nav2 and the mission manager. Every
subsystem sits behind an enable flag so the build order can be walked one piece at a time.

```bash
ros2 launch car_tracker robot.launch.py
```

Until `ascamera` is installed, the camera will fail to start. Skip it with:

```bash
ros2 launch car_tracker robot.launch.py use_camera:=false
```

Flags: `use_description`, `use_base`, `use_lidar`, `use_camera`, `use_ekf`, `use_slam` and
`use_nav` default true; `use_teleop` and `use_mission` default false.

### Desktop

Runs rviz and, later, the perception nodes. This half is deliberately expendable — everything
safety-critical stays on the Pi, because WiFi will drop.

```bash
ros2 launch car_tracker desktop.launch.py
```

Both machines need `chrony` (Pi as client of the desktop), a matching `ROS_DOMAIN_ID`, and
CycloneDDS with explicit unicast peers. Clock skew breaks TF in ways that look exactly like
SLAM bugs, and multicast discovery does not survive most WiFi APs. Do the time sync before
debugging anything else, ever.

### Teleop only

For a minimal bringup that just drives the robot, with no autonomy running:

```bash
ros2 launch car_tracker teleop.launch.py
```

Hold **LB** as a deadman; left stick is translation, right stick X is yaw. Triggers cannot be
used for yaw with the stock `teleop_twist_joy`: they rest at `+1.0`, so binding one to yaw
spins the robot at full rate while untouched, and two-directional yaw would need `RT - LT`,
which the node has no way to express.

Confirm the pad index from the `joy_node` startup line, which logs the device it opened. Do
not infer it from `ls /dev/input/by-id/` — that is the legacy `jsN` numbering and is unrelated
to `device_id`. A wrong index logs nothing at all and `/joy` simply never publishes.

## Reference

### Launch files

Each is independently launchable, so a subsystem can be debugged on its own.

| File | Runs on | Doc |
|---|---|---|
| `robot.launch.py` | Pi | [robot](https://github.com/redto0/car_tracker_design/blob/main/launch/robot.launch.md) |
| `desktop.launch.py` | desktop | [desktop](https://github.com/redto0/car_tracker_design/blob/main/launch/desktop.launch.md) |
| `include/base/controller.launch.py` | Pi | [controller](https://github.com/redto0/car_tracker_design/blob/main/nodes/controller.md) |
| `include/base/description.launch.py` | Pi | [description](https://github.com/redto0/car_tracker_design/blob/main/nodes/description.md) |
| `include/sensors/camera.launch.py` | Pi | [camera](https://github.com/redto0/car_tracker_design/blob/main/nodes/camera.md) |
| `include/sensors/lidar.launch.py` | Pi | [lidar](https://github.com/redto0/car_tracker_design/blob/main/nodes/lidar.md) |
| `include/localization/ekf.launch.py` | Pi | [ekf](https://github.com/redto0/car_tracker_design/blob/main/nodes/ekf.md) |
| `include/slam/slam.launch.py` | Pi | [slam](https://github.com/redto0/car_tracker_design/blob/main/nodes/slam.md) |
| `include/navigation/nav2.launch.py` | Pi | [nav2](https://github.com/redto0/car_tracker_design/blob/main/nodes/nav2.md) |
| `include/navigation/mission.launch.py` | Pi | [path_resolver](https://github.com/redto0/car_tracker_design/blob/main/nodes/path_resolver.md) |
| `include/teleop/teleop.launch.py` | either | [teleop](https://github.com/redto0/car_tracker_design/blob/main/nodes/teleop.md) |
| `include/rviz/rviz.launch.py` | desktop | [rviz](https://github.com/redto0/car_tracker_design/blob/main/nodes/rviz.md) |

`ros2 launch car_tracker <file>.launch.py` finds these by name; the `include/` path is
only needed on disk.

### Config

Launch-time **wiring** (topic names, vendor packages, environment variables) is separate from
runtime **parameters**, because remaps and package names are resolved before any node exists
and so can never be ROS parameters.

| File | Read by |
|---|---|
| `robot_wiring.yaml`, `camera_wiring.yaml` | the launch system, at description-build time |
| `ekf.yaml`, `slam_toolbox.yaml`, `nav2_params.yaml`, `camera_params.yaml`, `teleop.yaml` | nodes, at runtime |
