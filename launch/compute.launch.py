"""Desktop bringup. See car_tracker_design/deployment/compute.launch.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False against a real robot.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace the robot is running under. Must match the Pi.'),
        DeclareLaunchArgument('use_rviz', default_value='true',
                              description='Launch RViz.'),
    ]

    rviz = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(_PKG), 'launch', 'include', 'rviz', 'rviz.launch.py'])),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'use_rviz': LaunchConfiguration('use_rviz'),
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    # TODO: perception nodes go here once they exist --
    #   include/perception/segmentation.launch.py   terrain classifier
    #   include/perception/semantic_grid.launch.py  log-odds accumulator
    # Both subscribe to /camera/color/downscaled/image_raw/compressed and
    # publish a map-frame grid the Pi's costmap layer consumes. See
    # car_tracker_design/architecture.md.

    return LaunchDescription(args + [GroupAction([rviz])])
