"""Full robot bringup, runs on the Pi. See car_tracker_design/launch/robot.launch.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def _include(subdir, filename, condition=None, extra=None):
    """Include one file from include/, each in its own scope. See launch/robot.launch.md."""
    launch_args = {
        'use_sim_time': LaunchConfiguration('use_sim_time'),
        'namespace': LaunchConfiguration('namespace'),
    }
    if extra:
        launch_args.update(extra)
    return GroupAction(
        [
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    PathJoinSubstitution(
                        [FindPackageShare(_PKG), 'launch', 'include', subdir, filename])),
                launch_arguments=launch_args.items(),
            )
        ],
        scoped=True,  # pops each include's args; parent scope still forwarded in

        condition=condition,
    )


def generate_launch_description():
    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware: '
                        'true with no clock publisher hangs every node silently.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace for the whole robot. Leave empty for a single robot.'),

        DeclareLaunchArgument('use_description', default_value='true',
                              description='robot_state_publisher and the URDF.'),
        DeclareLaunchArgument('use_base', default_value='true',
                              description='Vendor base driver: motors, encoders, IMU.'),
        DeclareLaunchArgument('use_lidar', default_value='true',
                              description='STL-19P lidar driver.'),
        DeclareLaunchArgument('use_camera', default_value='true',
                              description='Depth camera driver and the wire stream.'),
        DeclareLaunchArgument('use_ekf', default_value='true',
                              description='robot_localization odom EKF.'),
        DeclareLaunchArgument('use_slam', default_value='true',
                              description='slam_toolbox.'),
        DeclareLaunchArgument('use_nav', default_value='true',
                              description='Nav2.'),
        DeclareLaunchArgument('use_teleop', default_value='false',
                              description='Xbox controller teleop. Publishes to the same '
                                          '/cmd_vel as Nav2, so run it with use_nav:=false '
                                          'and use_mission:=false.'),
        DeclareLaunchArgument('use_mission', default_value='false',
                              description='Mission manager. FALSE by default -- with '
                                          'it on the robot starts picking its own goals '
                                          'as soon as the stack is up.'),
    ]

    return LaunchDescription(
        args + [
            GroupAction([
                _include('base', 'description.launch.py',
                         IfCondition(LaunchConfiguration('use_description'))),
                _include('base', 'controller.launch.py',
                         IfCondition(LaunchConfiguration('use_base'))),
                _include('sensors', 'lidar.launch.py',
                         IfCondition(LaunchConfiguration('use_lidar'))),
                _include('sensors', 'camera.launch.py',
                         IfCondition(LaunchConfiguration('use_camera'))),
                _include('localization', 'ekf.launch.py',
                         IfCondition(LaunchConfiguration('use_ekf'))),
                _include('slam', 'slam.launch.py',
                         IfCondition(LaunchConfiguration('use_slam'))),
                _include('teleop', 'teleop.launch.py',
                         IfCondition(LaunchConfiguration('use_teleop'))),
                _include('navigation', 'nav2.launch.py',
                         IfCondition(LaunchConfiguration('use_nav'))),
                _include('navigation', 'mission.launch.py',
                         IfCondition(LaunchConfiguration('use_mission'))),
            ])
        ]
    )
