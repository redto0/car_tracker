"""slam_toolbox, online async. See car_tracker_design/deployment/slam.launch.md."""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')
_DEFAULT_PARAMS = PathJoinSubstitution([FindPackageShare(_PKG), 'config', 'slam_toolbox.yaml'])


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    scan_topic = wiring['topics']['scan']
    frames = wiring['frames']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    mode = LaunchConfiguration('mode')
    publish_tf = LaunchConfiguration('transform_publish_period')

    sim_time = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push slam_toolbox into.'),
        DeclareLaunchArgument(
            'params_file', default_value=_DEFAULT_PARAMS,
            description='slam_toolbox parameters (config/slam_toolbox.yaml).'),
        DeclareLaunchArgument(
            'mode', default_value='mapping',
            description="'mapping' to build a new map, 'localization' to "
                        'relocalize in a serialized one.'),
        DeclareLaunchArgument(
            'transform_publish_period', default_value='0.02',
            description='Rate for the map -> odom broadcast. Set 0.0 to disable '
                        'it entirely, which is REQUIRED before enabling ekf_map '
                        'or the two fight over that transform.'),
    ]

    slam = Node(
        package='slam_toolbox',
        executable='async_slam_toolbox_node',
        name='slam_toolbox',
        output='screen',
        parameters=[
            params_file,
            {
                'use_sim_time': sim_time,
                'mode': mode,
                'transform_publish_period': ParameterValue(publish_tf, value_type=float),
                'base_frame': frames['base'],
                'odom_frame': frames['odom'],
                'map_frame': frames['map'],
            },
        ],
        remappings=[
            ('scan', scan_topic),
            # slam_toolbox's map-frame estimate. ekf_map consumes this when the
            # dual-EKF setup is enabled.
            ('pose', 'pose'),
            ('map', 'map'),
            ('map_metadata', 'map_metadata'),
        ],
    )

    return LaunchDescription(
        args + [
            GroupAction([
                PushRosNamespace(namespace),
                slam,
            ])
        ]
    )
