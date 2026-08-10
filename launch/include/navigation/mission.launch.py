"""
Mission manager. Runs on the Pi.

Thin wrapper over car_tracker_path_resolver's own launch file, so the node stays
independently launchable from its package and this tree only supplies the
bringup-level arguments.

The node decides WHERE to go; Nav2 plans and follows.

  ros2 launch car_tracker mission.launch.py
  ros2 launch car_tracker mission.launch.py auto_explore:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    auto_explore = LaunchConfiguration('auto_explore')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the mission manager into.'),
        DeclareLaunchArgument(
            'auto_explore', default_value='true',
            description='Fall back to frontier exploration when there is no POI. '
                        'Frontier detection is currently a stub, so this idles.'),
    ]

    mission = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare('car_tracker_path_resolver'),
                                  'launch', 'path_resolver.launch.py'])),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'namespace': namespace,
            'auto_explore': auto_explore,
        }.items(),
    )

    return LaunchDescription(args + [mission])
