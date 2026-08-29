# ROS 2 Humble for the MentorPi M1.
#
# The Pi runs Ubuntu 26.04, which has no ros-humble-* packages -- Humble is
# jammy-only. This image is the jammy/Humble environment the stack actually
# runs in. See car_tracker_design/deployment.md.
#
# Build ON THE PI (native arm64, no emulation needed):
#   docker compose -f docker/docker-compose.yml build
FROM ros:humble-ros-base

ARG DEBIAN_FRONTEND=noninteractive

# Host UID/GID, so files written into the bind-mounted workspace stay owned by
# the Pi user instead of root. Override if the Pi account is not 1000:1000.
ARG USER_UID=1000
ARG USER_GID=1000
ARG USERNAME=ros

# The base image has dialout(20), video(44) and plugdev(46) at the same GIDs as
# an Ubuntu host, but has NO `input` group -- that one is created by the host's
# udev, not by the base image, so usermod fails with "group does not exist".
# Device permissions are checked by NUMERIC gid, so this must match the host.
# Verify on the target machine: getent group input
ARG INPUT_GID=107

RUN apt-get update && apt-get install -y --no-install-recommends \
      # --- build tooling ---
      build-essential cmake git \
      python3-colcon-common-extensions python3-vcstool python3-rosdep \
      # --- localization / SLAM / navigation ---
      ros-humble-navigation2 ros-humble-nav2-bringup \
      ros-humble-slam-toolbox ros-humble-robot-localization \
      libgeographic-dev ros-humble-geographic-msgs ros-humble-angles \
      ros-humble-diagnostic-updater \
      # --- description / TF ---
      ros-humble-robot-state-publisher ros-humble-joint-state-publisher \
      ros-humble-xacro ros-humble-tf2-ros ros-humble-tf2-eigen \
      ros-humble-tf2-geometry-msgs ros-humble-tf2-sensor-msgs \
      # --- camera pipeline ---
      ros-humble-image-proc ros-humble-image-transport \
      ros-humble-image-transport-plugins ros-humble-cv-bridge \
      ros-humble-vision-msgs \
      # --- lidar. laser_filters is required by peripherals/lidar.launch.py but
      #     is declared in no package.xml, so rosdep will not pull it in. ---
      ros-humble-laser-filters \
      # --- IMU. peripherals/imu_filter.launch.py, same undeclared story. ---
      ros-humble-imu-complementary-filter \
      # --- teleop. Same story: referenced by teleop.launch.py only. ---
      ros-humble-joy ros-humble-teleop-twist-joy \
      # --- DDS. Cyclone with unicast peers; multicast does not survive WiFi. ---
      ros-humble-rmw-cyclonedds-cpp \
      # --- ascamera (Angstrong depth camera) SDK build deps, per Hiwonder's
      #     "1 Depth Camera Configuration". The driver itself is a binary blob
      #     that is not in any repo; see car_tracker_design/nodes/camera.md. ---
      libgflags-dev nlohmann-json3-dev libgoogle-glog-dev \
      ros-humble-camera-info-manager ros-humble-image-publisher \
      # --- ament lint/test deps. The packages declare these as test_depend, and
      #     BUILD_TESTING is on by default, so without them colcon build fails on
      #     find_package(ament_cmake_clang_format REQUIRED). Easy to miss: a dev
      #     machine has them already, so only a clean image exposes it. ---
      ros-humble-ament-cmake-clang-format ros-humble-ament-cmake-gtest \
      ros-humble-ament-cmake-xmllint ros-humble-ament-cmake-cppcheck \
      ros-humble-ament-cmake-flake8 ros-humble-ament-cmake-pep257 \
      ros-humble-ament-cmake-nose ros-humble-ament-clang-tidy \
      ros-humble-ament-copyright ros-humble-ament-flake8 \
      ros-humble-ament-pep257 ros-humble-ament-lint-auto \
      ros-humble-ament-lint-common ros-humble-launch-testing-ament-cmake \
      # --- ackermann_msgs is needed ONLY by camera_to_ground_projection, which is
      #     still the raw ISC template and builds as TODO_PACKAGE_NAME. The M1 is
      #     mecanum and wants nothing to do with Ackermann. DELETE THIS LINE once
      #     that repo is converted. It is here so the workspace that .repos
      #     actually delivers builds in a clean image. ---
      ros-humble-ackermann-msgs \
      # --- vendor driver python deps (Hiwonder declares none of these) ---
      python3-numpy python3-serial python3-transforms3d python3-yaml \
      # python3-pygame deliberately NOT installed. Only peripherals'
      # joystick_control_00.py imports it, and our launch tree never runs that
      # node. It pulls GTK3, LLVM and mesa -- roughly a gigabyte of image for
      # nothing, which matters on the Pi's SD card. Add it back only if you
      # actually launch Hiwonder's joystick node.

    && rm -rf /var/lib/apt/lists/*

# The base image already has a 'ubuntu' user on some tags; create ours only if
# the UID is free, otherwise reuse it.
RUN if ! getent group ${USER_GID} >/dev/null; then groupadd -g ${USER_GID} ${USERNAME}; fi \
 && if ! getent passwd ${USER_UID} >/dev/null; then \
      useradd -u ${USER_UID} -g ${USER_GID} -m -s /bin/bash ${USERNAME}; \
    fi \
 && HOME_USER=$(getent passwd ${USER_UID} | cut -d: -f1) \
 && if ! getent group input >/dev/null; then groupadd -g ${INPUT_GID} input; fi \
 # dialout: /dev/rrc and /dev/ldlidar are tty devices.
 # video:   the depth camera.  input: /dev/input/js* for the gamepad.
 && usermod -aG dialout,video,input,plugdev ${HOME_USER} \
 && echo "${HOME_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${HOME_USER} \
 && chmod 0440 /etc/sudoers.d/${HOME_USER}

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# `docker exec` does NOT run the ENTRYPOINT, so an exec'd shell would otherwise
# have no ROS: ROS_DISTRO is baked into the base image as an ENV and looks fine,
# while CMAKE_PREFIX_PATH is empty and colcon cannot even find ament_cmake.
# profile.d covers login shells (bash -lc), .bashrc covers interactive exec.
RUN printf '%s\n' \
      'source /opt/ros/humble/setup.bash' \
      '[ -f /ws/install_docker/setup.bash ] && source /ws/install_docker/setup.bash' \
      > /etc/profile.d/car_tracker_ros.sh \
 && chmod 0644 /etc/profile.d/car_tracker_ros.sh \
 && echo '. /etc/profile.d/car_tracker_ros.sh' >> /home/${USERNAME}/.bashrc \
 && chown ${USER_UID}:${USER_GID} /home/${USERNAME}/.bashrc

# Name form, NOT ${USER_UID}:${USER_GID}. With a numeric USER, Docker does not
# resolve supplementary groups from /etc/group, so dialout/video/input/plugdev
# are silently dropped at runtime and every device open fails with EACCES while
# `getent group` inside the container still looks correct. Compose `group_add`
# backs this up in case the base image ever ships its own uid 1000.
USER ${USERNAME}
WORKDIR /ws

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
