"""
Robot description: robot_state_publisher broadcasting base_footprint -> sensor
frames from Hiwonder's mecanum xacro. Runs on the Pi.

Wraps mentorpi_description rather than maintaining a second URDF that will drift
out of sync with theirs.

VERIFY THE URDF AGAINST THE PHYSICAL ROBOT before trusting any of it. A 5 cm or
3 degree lidar extrinsic error smears the map on every turn and is
indistinguishable from a SLAM tuning problem -- one of the most expensive
mistakes available on this project.

  ros2 launch car_tracker description.launch.py
  ros2 run tf2_tools view_frames        # then check the tree
"""

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

    desc = wiring['description']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push robot_state_publisher into.'),
    ]

    env = [SetEnvironmentVariable(k, str(v)) for k, v in wiring['env'].items()]

    vendor = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(desc['package']), 'launch', desc['launch_file']])),
        launch_arguments={'use_sim_time': use_sim_time}.items(),
    )

    return LaunchDescription(
        args + env + [
            GroupAction([
                PushRosNamespace(namespace),
                SetRemap(src='robot_description', dst='robot_description'),
                SetRemap(src='joint_states', dst='joint_states'),
                vendor,
            ])
        ]
    )
