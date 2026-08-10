"""
Full robot bringup. Runs on the PI.

Everything safety-critical lives here rather than on the desktop, on one rule:
if it stopping for 500 ms would crash the robot, it runs on the Pi. WiFi will
drop. The desktop only ever produces map-frame annotations, never control.

  ros2 launch car_tracker robot.launch.py

Every subsystem has an enable flag, so the build order in
car_tracker_design/architecture.md can be walked one step at a time:

  # step 3-4: TF and odometry only
  ros2 launch car_tracker robot.launch.py use_slam:=false use_nav:=false
  # step 5: add mapping
  ros2 launch car_tracker robot.launch.py use_nav:=false
  # step 6: add Nav2, drive from rviz
  ros2 launch car_tracker robot.launch.py

use_mission defaults to FALSE. With it true the robot starts choosing its own
goals the moment the stack comes up, which is not what you want while bringing
things up next to a desk.

BEFORE FIRST USE: disable Hiwonder's auto-started app stack, or two things will
publish /cmd_vel.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def _include(subdir, filename, condition=None, extra=None):
    """Include one file from the include/ tree, forwarding the common args."""
    launch_args = {
        'use_sim_time': LaunchConfiguration('use_sim_time'),
        'namespace': LaunchConfiguration('namespace'),
    }
    if extra:
        launch_args.update(extra)
    return IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution([FindPackageShare(_PKG), 'launch', 'include', subdir, filename])),
        launch_arguments=launch_args.items(),
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
                _include('navigation', 'nav2.launch.py',
                         IfCondition(LaunchConfiguration('use_nav'))),
                _include('navigation', 'mission.launch.py',
                         IfCondition(LaunchConfiguration('use_mission'))),
            ])
        ]
    )
