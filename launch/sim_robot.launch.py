"""Whole robot, simulated. See car_tracker_design/sim_integration.md.

The counterpart to robot.launch.py, and deliberately a separate file rather than
a set of flags on that one. Compare the two subsystem lists at the bottom of
each and the difference is the point: there is no base driver, no lidar driver
and no camera driver here, because Gazebo provides those. You read that off the
list instead of inferring it from use_base:=false use_lidar:=false.

Everything from laser_odom down is the SAME include the robot runs, with the
same config. That is what makes this a test of the stack rather than a test of
a simulator-specific arrangement of it.

    ros2 launch car_tracker sim_robot.launch.py
    ros2 launch car_tracker sim_robot.launch.py use_gui:=true use_nav:=false
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def _subsystem(subdir, filename, launch_arguments, condition=None):
    """One file from launch/include/, wrapped in its own scope.

    scoped=True is load-bearing, not tidiness: without it params_file set by one
    include leaks into the next, and Nav2 gets handed ekf.yaml. That surfaces as
    controller_server failing to load its DWB critics, nowhere near the cause.
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
    namespace = LaunchConfiguration('namespace')
    slam_engine = LaunchConfiguration('slam_engine')
    sim_camera = LaunchConfiguration('sim_camera')

    use_slam = LaunchConfiguration('use_slam')
    use_nav = LaunchConfiguration('use_nav')
    use_teleop = LaunchConfiguration('use_teleop')
    use_mission = LaunchConfiguration('use_mission')

    # use_sim_time is not an argument here. It is always true: the simulator
    # publishes /clock and every node must be on it. Making it settable would
    # only allow one wrong value.
    common = {'use_sim_time': 'true', 'namespace': namespace}

    gazebo = _subsystem(
        'sim', 'gazebo.launch.py',
        {'namespace': namespace,
         'world': LaunchConfiguration('world'),
         'use_gui': LaunchConfiguration('use_gui'),
         'x': LaunchConfiguration('x'),
         'y': LaunchConfiguration('y'),
         'yaw': LaunchConfiguration('yaw')},
    )

    description = _subsystem(
        'sim', 'description.launch.py',
        {**common, 'sim_camera': sim_camera},
    )

    imu = _subsystem('sensors', 'imu.launch.py', common)
    laser_odom = _subsystem('localization', 'laser_odom.launch.py', common)
    ekf = _subsystem('localization', 'ekf.launch.py', common)

    slam = _subsystem(
        'slam', 'slam.launch.py',
        {**common, 'engine': slam_engine},
        condition=IfCondition(use_slam),
    )

    teleop = _subsystem(
        'teleop', 'teleop.launch.py', common,
        condition=IfCondition(use_teleop),
    )

    nav2 = _subsystem(
        'navigation', 'nav2.launch.py', common,
        condition=IfCondition(use_nav),
    )

    mission = _subsystem(
        'navigation', 'mission.launch.py', common,
        condition=IfCondition(use_mission),
    )

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace for the whole robot. Leave empty for one robot.'),
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [FindPackageShare(_PKG), 'worlds', 'apartment.world']),
            description='World file. Defaults to the 10.7 x 4.6 m apartment.'),
        DeclareLaunchArgument(
            'use_gui', default_value='false',
            description='Run gzclient. False by default: the GUI is the '
                        'expensive half and headless is what regression wants.'),
        DeclareLaunchArgument(
            'sim_camera', default_value='false',
            description='Simulate the camera. OFF by default: gzserver renders '
                        'it even headless. Perception is validated on real '
                        'floors, not in sim.'),
        DeclareLaunchArgument('x', default_value='1.0',
                              description='Spawn x, default the hallway.'),
        DeclareLaunchArgument('y', default_value='0.6',
                              description='Spawn y, default mid-hallway.'),
        DeclareLaunchArgument('yaw', default_value='0.0',
                              description='Spawn yaw in radians.'),
        DeclareLaunchArgument(
            'use_slam', default_value='true', description='slam_toolbox.'),
        DeclareLaunchArgument(
            'slam_engine', default_value='async',
            description="'async' keeps every node, 'lifelong' prunes redundant "
                        'ones. lifelong needs ros-humble-slam-toolbox from apt.'),
        DeclareLaunchArgument(
            'use_nav', default_value='true', description='Nav2.'),
        DeclareLaunchArgument(
            'use_teleop', default_value='false',
            description='Gamepad teleop. Publishes to the same /cmd_vel as '
                        'Nav2, so run it with use_nav:=false.'),
        DeclareLaunchArgument(
            'use_mission', default_value='false',
            description='Mission manager. FALSE by default -- with it on the '
                        'robot picks its own goals as soon as the stack is up.'),

        # Subsystems, in dependency order.
        #
        # Against robot.launch.py, what is MISSING is the information: no
        # base/controller (planar_move drives the robot), no sensors/lidar (the
        # ray sensor publishes /scan), no sensors/camera. Everything below the
        # first two entries is byte-identical to the hardware bringup.
        gazebo,
        description,
        imu,
        laser_odom,
        ekf,
        slam,
        teleop,
        nav2,
        mission,
    ])
