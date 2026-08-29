#!/usr/bin/env bash
# Sources ROS and the workspace overlay, then execs the command.
# Docs: car_tracker_design/deployment.md
set -e

source /opt/ros/humble/setup.bash

# Overlay is only present after the first colcon build. Not an error before that.
# install_docker is the container's own install base (see colcon-defaults.yaml);
# /ws/install belongs to the host and is built against different absolute paths.
if [ -f /ws/install_docker/setup.bash ]; then
    source /ws/install_docker/setup.bash
else
    echo "[entrypoint] /ws/install_docker not found -- run 'colcon build --symlink-install' first." >&2
fi

# Vendor launch files read these with os.environ[...]; unset is a KeyError that
# aborts the launch before anything starts. The fork defaults them too, but the
# container sets them so a plain 'ros2 launch' from a shell also works.
export need_compile="${need_compile:-True}"
export LIDAR_TYPE="${LIDAR_TYPE:-LD19}"
export DEPTH_CAMERA_TYPE="${DEPTH_CAMERA_TYPE:-ascamera}"

# Opt-in drift check: catches a package.xml dependency added since the image build.
if [ "${CAR_TRACKER_ROSDEP:-0}" = "1" ]; then
    sudo apt-get update -qq
    rosdep update --rosdistro humble
    rosdep install --from-paths /ws/src --ignore-src -r -y
fi

exec "$@"
