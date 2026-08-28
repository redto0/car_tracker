"""Xbox controller teleop. See car_tracker_design/nodes/teleop.md."""

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
_DEFAULT_PARAMS = PathJoinSubstitution([FindPackageShare(_PKG), 'config', 'teleop.yaml'])


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    cmd_vel_topic = wiring['topics']['cmd_vel']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    device_id = LaunchConfiguration('device_id')

    sim_time = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the teleop nodes into.'),
        DeclareLaunchArgument(
            'params_file', default_value=_DEFAULT_PARAMS,
            description='Axis mapping and scales (config/teleop.yaml).'),
        DeclareLaunchArgument(
            'device_id', default_value='0',
            description='Which /dev/input/jsN. Not always 0 -- resolve with '
                        '`ls -l /dev/input/by-id/ | grep joystick`.'),
    ]

    joy = Node(
        package='joy',
        executable='joy_node',
        name='joy_node',
        output='screen',
        parameters=[
            params_file,
            {
                'use_sim_time': sim_time,
                'device_id': ParameterValue(device_id, value_type=int),
            },
        ],
        remappings=[
            ('joy', 'joy'),
            ('joy/set_feedback', 'joy/set_feedback'),
        ],
    )

    teleop = Node(
        package='teleop_twist_joy',
        executable='teleop_node',
        name='teleop_twist_joy_node',
        output='screen',
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('joy', 'joy'),
            ('cmd_vel', cmd_vel_topic),
        ],
    )

    return LaunchDescription(
        args + [
            GroupAction([
                PushRosNamespace(namespace),
                joy,
                teleop,
            ])
        ]
    )
