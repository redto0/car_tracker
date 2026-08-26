"""STL-19P lidar. See car_tracker_design/deployment/lidar.launch.md."""

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

    lidar = wiring['lidar']
    topics = wiring['topics']
    frames = wiring['frames']

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

    env = [SetEnvironmentVariable(k, str(v)) for k, v in wiring['env'].items()]

    vendor = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(lidar['package']), 'launch', lidar['launch_file']])),
        launch_arguments={
            'scan_topic': topics['scan'],
            'lidar_frame': frames['lidar'],
        }.items(),
    )

    return LaunchDescription(
        args + env + [
            GroupAction([
                PushRosNamespace(namespace),
                # Identity, but written out so the lidar's output topic is
                # visible here rather than only inside the vendor launch file.
                SetRemap(src='scan', dst=topics['scan']),
                vendor,
            ])
        ]
    )
