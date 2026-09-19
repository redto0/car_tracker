"""IMU calibration and filtering. See car_tracker_design/nodes/ekf.md.

Topic surface
-------------
subscribes  ros_robot_controller/imu_raw  sensor_msgs/Imu   raw, from the board
                                                            or from Gazebo
publishes   imu_corrected                 sensor_msgs/Imu   after apply_calib
publishes   imu                           sensor_msgs/Imu   ekf_odom's imu0
publishes   imu/rpy/filtered, imu/steady_state               diagnostics

Split out of the vendor's controller.launch.py, which bundled the IMU chain
with the motor driver. They have nothing to do with each other, and the bundling
meant simulation could not run the IMU chain without also trying to open
/dev/rrc. controller.launch.py is now launched with use_imu_filter:=false and
both bringups include this instead, so the chain is visible in the subsystem
list rather than implied.

Source topic is identical in both cases: on hardware ros_robot_controller
publishes it, in simulation the Gazebo IMU sensor does, under the same name.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import PushRosNamespace, SetRemap

_VENDOR = os.path.join(
    get_package_share_directory('peripherals'), 'launch', 'imu_filter.launch.py')


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')

    vendor = IncludeLaunchDescription(PythonLaunchDescriptionSource(_VENDOR))

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the IMU chain into.'),

        GroupAction([
            PushRosNamespace(namespace),
            # Written out even though every one is an identity mapping, so the
            # chain is readable here without opening the vendor launch file.
            SetRemap(src='imu_corrected', dst='imu_corrected'),
            SetRemap(src='imu', dst='imu'),
            vendor,
        ]),
    ])
