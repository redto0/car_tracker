"""Mission manager. See car_tracker_design/nodes/path_resolver.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import SetRemap
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

    # Topic surface of the included node, recorded here so it is visible without
    # opening path_resolver. Confirmed against PathResolver_node.cpp:
    #   goal_poi  PoseStamped     target of interest
    #   map       OccupancyGrid   transient_local, matches slam_toolbox's latch
    #   navigate_to_pose          Nav2 action, remaps on its base name
    topics = GroupAction([
        SetRemap(src='goal_poi', dst='goal_poi'),
        SetRemap(src='map', dst='map'),
        mission,
    ])

    return LaunchDescription(args + [topics])
