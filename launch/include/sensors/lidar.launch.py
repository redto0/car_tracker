"""
STL-19P lidar (an LDRobot LD19/D500). Runs on the Pi.

Wraps the vendor ldlidar_node launch file and normalizes its scan topic. The
driver publishes /ldlidar_node/scan, but slam_toolbox, Nav2 and rviz all expect
/scan -- normalizing here means nothing downstream needs to know otherwise.

  ros2 launch car_tracker lidar.launch.py

If the map smears on every turn, suspect the lidar extrinsics in the URDF before
suspecting SLAM. A 5 cm or 3 degree error looks exactly like a tuning problem.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import PushRosNamespace, SetRemap
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    lidar = wiring['lidar']
    scan_src = 'ldlidar_node/scan'
    scan_dst = wiring['remaps'][scan_src]

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the lidar driver into.'),
    ]

    vendor = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(lidar['package']), 'launch', lidar['launch_file']])),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    return LaunchDescription(
        args + [
            GroupAction([
                PushRosNamespace(namespace),
                SetRemap(src=scan_src, dst=scan_dst),
                vendor,
            ])
        ]
    )
