"""
MentorPi base driver: motors, wheel encoders, IMU. Runs on the Pi.

Wraps Hiwonder's own controller launch file rather than replacing it -- the
serial protocol to the STM32 is the tedious part and theirs works. Everything
above it is ours.

Because the vendor ships a launch file rather than a bare node, remaps are
applied with SetRemap inside the GroupAction. Remaps cannot be passed to an
IncludeLaunchDescription directly; SetRemap is the scoped equivalent.

  ros2 launch car_tracker controller.launch.py

BEFORE USING THIS: disable Hiwonder's auto-started app stack, or two things
will publish /cmd_vel and fight over the robot.
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

    base = wiring['base']

    namespace = LaunchConfiguration('namespace')
    use_sim_time = LaunchConfiguration('use_sim_time')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the base driver into.'),
    ]

    # Explicit remaps for the base's whole topic surface, including the identity
    # ones, so the wiring is readable without opening the vendor launch file.
    remaps = [SetRemap(src=src, dst=dst) for src, dst in wiring['remaps'].items()
              if not src.startswith('ldlidar')]

    vendor = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(base['package']), 'launch', base['launch_file']])),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    return LaunchDescription(
        args + [
            GroupAction([PushRosNamespace(namespace)] + remaps + [vendor])
        ]
    )
