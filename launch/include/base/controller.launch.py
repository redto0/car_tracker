"""MentorPi base driver. See car_tracker_design/nodes/controller.md."""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            SetEnvironmentVariable)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import PushRosNamespace, SetRemap
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    base = wiring['base']
    topics = wiring['topics']
    frames = wiring['frames']

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')
    enable_odom = LaunchConfiguration('enable_odom')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the base driver into.'),
        DeclareLaunchArgument(
            'enable_odom', default_value='false',
            description="Run Hiwonder's own EKF. FALSE here on purpose -- ours "
                        'owns odom -> base_footprint. Setting this true without '
                        'also disabling ekf.launch.py gives two broadcasters on '
                        'that transform.'),
    ]

    # need_compile must be 'True' or their launch files fall back to hardcoded
    # /home/ubuntu/ros2_ws paths that do not exist here.
    env = [SetEnvironmentVariable(k, str(v)) for k, v in wiring['env'].items()]

    # The base's whole topic surface, identity mappings included, so the wiring
    # is readable without opening the vendor launch file.
    remaps = [
        SetRemap(src='odom_raw', dst=topics['odom_raw']),
        SetRemap(src='odom', dst=topics['odom']),
        SetRemap(src='cmd_vel', dst=topics['cmd_vel']),
        SetRemap(src='imu', dst=topics['imu']),
    ]

    vendor = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(base['package']), 'launch', base['launch_file']])),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'enable_odom': enable_odom,
            'base_frame': frames['base'],
            'odom_frame': frames['odom'],
            'map_frame': frames['map'],
            'imu_frame': frames['imu'],
        }.items(),
    )

    return LaunchDescription(
        args + env + [
            GroupAction([PushRosNamespace(namespace)] + remaps + [vendor])
        ]
    )
