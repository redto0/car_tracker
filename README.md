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
   install binary dependencies. On a fresh jammy box this resolves everything the
   `package.xml` files declare, which is the whole apt row of the table above. If you want
   the one-liner instead of trusting rosdep, or you are only building part of the tree:

   ```bash
   sudo apt install -y \
     ros-humble-navigation2 ros-humble-nav2-bringup ros-humble-slam-toolbox \
     ros-humble-robot-localization ros-humble-laser-filters \
     ros-humble-imu-complementary-filter ros-humble-joy ros-humble-teleop-twist-joy \
     ros-humble-image-proc ros-humble-image-transport-plugins \
     ros-humble-rmw-cyclonedds-cpp ros-humble-xacro

   # desktop only -- deliberately NOT in the Dockerfile, rviz has no business
   # running on the Pi and it is a large install
   sudo apt install -y ros-humble-rviz2
   ```

   `rmw_cyclonedds_cpp` matters on **both** machines, not just the Pi. The compose file
   sets `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` for the container; if the desktop falls
   back to Fast DDS you get a uniquely misleading half-failure — the desktop **lists**
   every container node and topic, so everything looks fine, but `ros2 topic hz` on them
   returns nothing. Measured: desktop on Cyclone reads a containerised `/scan` at
   9.998 Hz; the same publisher read from Fast DDS never delivers a message.

   So the desktop shell needs both, not just the package:

   ```bash
   export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
   export CYCLONEDDS_URI=file://$PWD/src/car_tracker/docker/cyclonedds.xml
   ```
7. Remember to source ROS2 before building `source /opt/ros/humble/setup.bash` and add to
   your bashrc with `echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc`
8. Still in workspace root, run `colcon build --symlink-install` to build the workspace.
   **`--symlink-install` is required**, not optional: the wiring YAMLs are read eagerly from
   the installed share directory, so without symlinks you edit a stale copy and your changes
   appear to do nothing
9. Make sure your user is a part of the unix `dialout`, `video` and `input` groups. This
   allows it to connect to USB devices:

   ```bash
   sudo usermod -aG dialout,video,input $USER
   ```

   Log out and back in afterwards — group changes do not apply to an existing session, and
   `newgrp` only fixes the one shell you run it in. Verify with `id -nG`.

   Each group gates a different device, and the failure is silent in every case:
   `dialout` for the lidar and controller board (both tty), `video` for the cameras,
   `input` for `/dev/input/js*`. Without `input` the gamepad cannot be opened and `/joy`
   simply never publishes — which looks exactly like the wrong `device_id`, so you can
   lose an afternoon to it.
10. Install the udev rules so the drivers find their devices: `./docker/install-udev.sh`.
    It reloads and triggers, so devices already plugged in get their symlinks without a
    replug, and it prints what it created — `/dev/rrc`, `/dev/imu`, `/dev/ldlidar`. A
    `MISSING` line means that device is not plugged in.
    The vendor drivers open **symlinks**, not raw devices, and no rule shipped by Hiwonder
    creates `/dev/ldlidar` even though the LD19 launch opens it.
    `/dev/imu` is an alias for `/dev/rrc`: the IMU is on the controller board and shares
    its serial stream, so there is no separate device to open

The repo should now be built, and launch-able on the robot or the desktop.

11. Check it actually came up. `--show-args` proves a launch file parses, not that it runs:

    ```bash
    ros2 launch car_tracker robot.launch.py use_camera:=false
    # in another shell:
    ros2 topic hz /scan                     # ~10 Hz
    ros2 topic hz /imu                      # ~48 Hz raw, ~96 Hz filtered
    ros2 topic hz /odometry/filtered/local  # 30 Hz, matches ekf.yaml
    ros2 lifecycle get /controller_server   # active [3]
    ```

    `use_camera:=false` is required until `ascamera` exists. Do **not** reach for
    `use_base:=false` to skip missing motors: the IMU and wheel odometry come from the same
    launch file, so it leaves `ekf_odom` with no inputs, no `odom -> base_footprint`, and
    Nav2 stuck `inactive` — which reads as a Nav2 bug and is not one.

    Full bring-up detail, expected rates and the failure modes behind each are in
    [deployment.md](https://github.com/redto0/car_tracker_design/blob/main/deployment.md).

#### If SLAM dies on a missing libceres

```
[FATAL] [slam_toolbox]: Failed to create solver_plugins::CeresSolver ...
  dlopen error: libceres.so.2: cannot open shared object file
```

`libceres2` is a declared dependency **of `ros-humble-slam-toolbox`**, not of this repo, so
apt normally pulls it in and neither the table above nor rosdep needs to mention it. Seeing
this error means slam_toolbox got onto the machine some way other than apt (check with
`dpkg-query -W ros-humble-slam-toolbox`; "no packages found" while
`/opt/ros/humble/share/slam_toolbox` exists is the giveaway). Hiwonder's original image is
one way that happens. Fix the runtime library directly:

```bash
sudo apt install -y libceres2
```

or reinstall the package properly with `sudo apt install --reinstall ros-humble-slam-toolbox`
so its dependencies are tracked from then on. The Docker image is unaffected: it apt-installs
slam_toolbox, so `libceres2` comes with it.

### On the Pi, ROS runs in Docker

The Pi was reflashed with **Ubuntu 26.04** and Humble is jammy-only, so there is no
`ros-humble-*` for the host. Steps 1-8 above happen **inside the container**; the 26.04 host
only provides kernel, udev and network. The desktop is jammy and runs Humble natively, so it
needs no container.

```bash
cp src/car_tracker/docker/env.example .env      # then set PI_IP / DESKTOP_IP
docker compose --env-file .env -f src/car_tracker/docker/docker-compose.yml up -d --build ros
docker compose --env-file .env -f src/car_tracker/docker/docker-compose.yml exec ros bash -lc 'colcon build --symlink-install'
```

**`bash -lc` is not optional on that last line.** `docker exec` does not run the
ENTRYPOINT, so a bare `exec ros colcon build` starts with an empty `AMENT_PREFIX_PATH` and
fails with `Could not find a package configuration file provided by "ament_cmake"`. Only a
login shell sources `/etc/profile.d/car_tracker_ros.sh`.

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

**`use_base` also gates the IMU and the wheel odometry**, not just the motors — the whole
`controller.launch.py` sits behind it. Turning it off leaves `ekf_odom` with no inputs, so
there is no `odom -> base_footprint` and every Nav2 lifecycle node stays `inactive` waiting
on a transform that will never arrive. Nothing errors; it just never comes up.

### Desktop

Runs rviz and, later, the perception nodes. This half is deliberately expendable — everything
safety-critical stays on the Pi, because WiFi will drop.

```bash
ros2 launch car_tracker desktop.launch.py
```

The desktop needs CycloneDDS too, not just the Pi:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=file://$PWD/src/car_tracker/docker/cyclonedds.xml
```

Without both, you get the confusing half-failure: `ros2 node list` and `ros2 topic list`
show everything the Pi publishes, while `ros2 topic hz` on those same topics returns
nothing. Discovery is UDP and crosses vendors; data does not.

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
