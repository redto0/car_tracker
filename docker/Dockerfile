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
      # --- teleop. Same story: referenced by teleop.launch.py only. ---
      ros-humble-joy ros-humble-teleop-twist-joy \
      # --- DDS. Cyclone with unicast peers; multicast does not survive WiFi. ---
      ros-humble-rmw-cyclonedds-cpp \
      # --- vendor driver python deps (Hiwonder declares none of these) ---
      python3-numpy python3-serial python3-transforms3d python3-yaml \
      python3-pygame \
    && rm -rf /var/lib/apt/lists/*

# The base image already has a 'ubuntu' user on some tags; create ours only if
# the UID is free, otherwise reuse it.
RUN if ! getent group ${USER_GID} >/dev/null; then groupadd -g ${USER_GID} ${USERNAME}; fi \
 && if ! getent passwd ${USER_UID} >/dev/null; then \
      useradd -u ${USER_UID} -g ${USER_GID} -m -s /bin/bash ${USERNAME}; \
    fi \
 && HOME_USER=$(getent passwd ${USER_UID} | cut -d: -f1) \
 # dialout: /dev/rrc and /dev/ldlidar are tty devices.
 # video:   the depth camera.  input: /dev/input/js* for the gamepad.
 && usermod -aG dialout,video,input,plugdev ${HOME_USER} \
 && echo "${HOME_USER} ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/${HOME_USER} \
 && chmod 0440 /etc/sudoers.d/${HOME_USER}

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER ${USER_UID}:${USER_GID}
WORKDIR /ws

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
