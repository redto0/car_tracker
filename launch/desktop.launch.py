"""Desktop bringup. See car_tracker_design/launch/desktop.launch.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def _subsystem(subdir, filename, launch_arguments, condition=None):
    """One file from launch/include/, wrapped in its own scope.

    Same helper and same reason as robot.launch.py: scoped=True stops
    params_file leaking between includes. Kept here so the two top-level files
    read alike even though this one currently has a single entry.
    """
    return GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare(_PKG), 'launch', 'include', subdir, filename])),
                launch_arguments=launch_arguments.items(),
            )
        ],
        scoped=True,
        condition=condition,
    )


def generate_launch_description():
    # Launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    use_rviz = LaunchConfiguration('use_rviz')

    common = {'use_sim_time': use_sim_time, 'namespace': namespace}

    rviz = _subsystem(
        'rviz', 'rviz.launch.py',
        {**common, 'use_rviz': use_rviz},
        condition=IfCondition(use_rviz),
    )

    # TODO: perception nodes go here once they exist --
    #   include/perception/segmentation.launch.py   terrain classifier
    #   include/perception/semantic_grid.launch.py  log-odds accumulator
    # Both subscribe to /camera/color/downscaled/image_raw/compressed and
    # publish a map-frame grid the Pi's costmap layer consumes. See
    # car_tracker_design/architecture.md.

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False against a real robot.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace the robot is running under. Must match the Pi.'),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Launch RViz.'),

        # Subsystems
        rviz,
    ])
