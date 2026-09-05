"""Full robot bringup, runs on the Pi. See car_tracker_design/launch/robot.launch.md."""

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
    include leaks into the next, and Nav2 gets handed ekf.yaml. That failure
    shows up as a critics error from controller_server, nowhere near the cause.
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
    slam_engine = LaunchConfiguration('slam_engine')

    use_description = LaunchConfiguration('use_description')
    use_base = LaunchConfiguration('use_base')
    use_lidar = LaunchConfiguration('use_lidar')
    use_camera = LaunchConfiguration('use_camera')
    use_laser_odom = LaunchConfiguration('use_laser_odom')
    use_ekf = LaunchConfiguration('use_ekf')
    use_slam = LaunchConfiguration('use_slam')
    use_nav = LaunchConfiguration('use_nav')
    use_teleop = LaunchConfiguration('use_teleop')
    use_mission = LaunchConfiguration('use_mission')

    # Every include takes these two. Anything else is passed explicitly below so
    # it is visible at the call site.
    common = {'use_sim_time': use_sim_time, 'namespace': namespace}

    description = _subsystem(
        'base', 'description.launch.py',
        common,
        condition=IfCondition(use_description),
    )

    base = _subsystem(
        'base', 'controller.launch.py',
        common,
        condition=IfCondition(use_base),
    )

    lidar = _subsystem(
        'sensors', 'lidar.launch.py',
        common,
        condition=IfCondition(use_lidar),
    )

    camera = _subsystem(
        'sensors', 'camera.launch.py',
        common,
        condition=IfCondition(use_camera),
    )

    laser_odom = _subsystem(
        'localization', 'laser_odom.launch.py',
        common,
        condition=IfCondition(use_laser_odom),
    )

    ekf = _subsystem(
        'localization', 'ekf.launch.py',
        common,
        condition=IfCondition(use_ekf),
    )

    slam = _subsystem(
        'slam', 'slam.launch.py',
        {**common, 'engine': slam_engine},
        condition=IfCondition(use_slam),
    )

    teleop = _subsystem(
        'teleop', 'teleop.launch.py',
        common,
        condition=IfCondition(use_teleop),
    )

    nav2 = _subsystem(
        'navigation', 'nav2.launch.py',
        common,
        condition=IfCondition(use_nav),
    )

    mission = _subsystem(
        'navigation', 'mission.launch.py',
        common,
        condition=IfCondition(use_mission),
    )

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware: '
                        'true with no clock publisher hangs every node silently.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace for the whole robot. Leave empty for a single robot.'),
        DeclareLaunchArgument(
            'use_description', default_value='true',
            description='robot_state_publisher and the URDF.'),
        DeclareLaunchArgument(
            'use_base', default_value='true',
            description='Vendor base driver: motors, servos, IMU. No encoders.'),
        DeclareLaunchArgument(
            'use_lidar', default_value='true',
            description='STL-19P lidar driver.'),
        DeclareLaunchArgument(
            'use_camera', default_value='true',
            description='Depth camera driver and the wire stream.'),
        DeclareLaunchArgument(
            'use_laser_odom', default_value='true',
            description='rf2o laser odometry. The board has no encoders, so this '
                        'publishes /odom_raw and is the EKF only translation '
                        'source. Needs use_lidar.'),
        DeclareLaunchArgument(
            'use_ekf', default_value='true',
            description='robot_localization odom EKF.'),
        DeclareLaunchArgument(
            'use_slam', default_value='true',
            description='slam_toolbox.'),
        DeclareLaunchArgument(
            'slam_engine', default_value='async',
            description="slam_toolbox engine: 'async' keeps every node, "
                        "'lifelong' prunes redundant ones as it runs. lifelong "
                        'needs ros-humble-slam-toolbox from apt.'),
        DeclareLaunchArgument(
            'use_nav', default_value='true',
            description='Nav2.'),
        DeclareLaunchArgument(
            'use_teleop', default_value='false',
            description='Xbox controller teleop. Publishes to the same /cmd_vel '
                        'as Nav2, so run it with use_nav:=false and '
                        'use_mission:=false.'),
        DeclareLaunchArgument(
            'use_mission', default_value='false',
            description='Mission manager. FALSE by default -- with it on the '
                        'robot starts picking its own goals as soon as the '
                        'stack is up.'),

        # Subsystems. Listed in dependency order: the URDF before anything that
        # needs a frame, sensors before the things that consume them, odometry
        # before slam, slam before Nav2. launch does not enforce ordering, so
        # this is documentation -- but comment a line out and everything below
        # it that depended on it will say so.
        description,
        base,
        lidar,
        camera,
        laser_odom,
        ekf,
        slam,
        teleop,
        nav2,
        mission,
    ])
