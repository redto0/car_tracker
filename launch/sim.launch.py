"""Gazebo Classic bringup. See car_tracker_design/sim_integration.md.

Starts the simulator and spawns the robot. It does NOT start the stack — run
robot.launch.py alongside it, with the hardware drivers switched off:

    ros2 launch car_tracker sim.launch.py
    ros2 launch car_tracker robot.launch.py \\
        use_sim_time:=true use_base:=false use_lidar:=false use_camera:=false

Kept separate so the thing under test is the same launch file that runs on the
robot, with no simulator-aware branches in it.
"""

from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, ExecuteProcess, GroupAction,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.substitutions import (Command, LaunchConfiguration,
                                  PathJoinSubstitution)
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def generate_launch_description():
    # Launch arguments
    namespace = LaunchConfiguration('namespace')
    world = LaunchConfiguration('world')
    use_gui = LaunchConfiguration('use_gui')
    x, y, yaw = (LaunchConfiguration('x'), LaunchConfiguration('y'),
                 LaunchConfiguration('yaw'))

    # MACHINE_TYPE selects mecanum vs ackermann inside the vendor xacro, exactly
    # as it does on the robot. Set here so the sim never depends on the shell.
    machine_type = SetEnvironmentVariable('MACHINE_TYPE', 'MentorPi_Mecanum')

    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([FindPackageShare(_PKG), 'urdf', 'mentorpi_sim.xacro']),
        ]),
        value_type=str,
    )

    # The simulated robot's description: the vendor URDF plus gazebo tags.
    # robot.launch.py publishes the hardware one, so this runs under its own
    # node name to avoid two robot_state_publishers on the same name.
    sim_description = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='sim_robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description, 'use_sim_time': True}],
        remappings=[('robot_description', 'sim/robot_description')],
    )

    # gzserver carries the ROS plugins; gzclient is the GUI and is off by
    # default because headless is what regression runs want.
    gzserver = ExecuteProcess(
        cmd=['gzserver', '--verbose',
             '-s', 'libgazebo_ros_init.so',
             '-s', 'libgazebo_ros_factory.so',
             world],
        output='screen',
    )

    gzclient = ExecuteProcess(
        cmd=['gzclient'],
        output='screen',
        condition=IfCondition(use_gui),
    )

    spawn = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        name='spawn_mentorpi',
        output='screen',
        arguments=[
            '-entity', 'mentorpi',
            '-topic', 'sim/robot_description',
            '-x', x, '-y', y, '-z', '0.05',
            '-Y', yaw,
        ],
    )

    return LaunchDescription([
        # Launch arguments
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace for the simulated robot. Must match the stack.'),
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [FindPackageShare(_PKG), 'worlds', 'apartment.world']),
            description='World file. Defaults to the 10.7 x 4.6 m apartment.'),
        DeclareLaunchArgument(
            'use_gui', default_value='false',
            description='Run gzclient. False by default: headless is what '
                        'regression runs want, and the GUI is the expensive half.'),
        DeclareLaunchArgument(
            'x', default_value='1.0',
            description='Spawn x. Default puts the robot in the hallway.'),
        DeclareLaunchArgument(
            'y', default_value='0.6',
            description='Spawn y. Default is the middle of the hallway.'),
        DeclareLaunchArgument(
            'yaw', default_value='0.0',
            description='Spawn yaw, radians. 0 faces along the hallway.'),

        machine_type,

        # Subsystems
        GroupAction([
            PushRosNamespace(namespace),
            sim_description,
            gzserver,
            gzclient,
            spawn,
        ]),
    ])
