"""Gazebo Classic server and model spawn. See car_tracker_design/sim_integration.md.

Starts the simulator and spawns whatever is on /robot_description. It owns no
robot wiring of its own -- sim/description.launch.py declares that -- so this
file is only the simulator process and the spawn.

Topic surface
-------------
publishes   clock               rosgraph_msgs/Clock   every node runs on this
subscribes  robot_description   to spawn the model
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, GroupAction, SetEnvironmentVariable
from launch.conditions import IfCondition
from launch.substitutions import EnvironmentVariable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'


def generate_launch_description():
    namespace = LaunchConfiguration('namespace')
    world = LaunchConfiguration('world')
    use_gui = LaunchConfiguration('use_gui')
    x, y, yaw = (LaunchConfiguration('x'), LaunchConfiguration('y'),
                 LaunchConfiguration('yaw'))

    # The URDF references meshes as package://, which Gazebo's SDF conversion
    # rewrites to model:// and then resolves against GAZEBO_MODEL_PATH -- which
    # knows nothing about the ament index. Without this every mesh silently
    # fails to load, the robot spawns with no geometry at all, and Gazebo goes
    # looking for the model on the internet.
    model_path = SetEnvironmentVariable(
        'GAZEBO_MODEL_PATH',
        [PathJoinSubstitution([FindPackageShare('mentorpi_description'), '..']),
         ':', EnvironmentVariable('GAZEBO_MODEL_PATH', default_value='')])

    # Never reach for the online model database: the world uses only sun and
    # ground_plane, both shipped locally, and a lookup stalls startup.
    no_online_models = SetEnvironmentVariable('GAZEBO_MODEL_DATABASE_URI', '')

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
        arguments=['-entity', 'mentorpi', '-topic', 'robot_description',
                   '-x', x, '-y', y, '-z', '0.05', '-Y', yaw],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace the robot is spawned under.'),
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
            'x', default_value='1.0', description='Spawn x, default the hallway.'),
        DeclareLaunchArgument(
            'y', default_value='0.6', description='Spawn y, default mid-hallway.'),
        DeclareLaunchArgument(
            'yaw', default_value='0.0', description='Spawn yaw in radians.'),

        model_path,
        no_online_models,

        GroupAction([
            PushRosNamespace(namespace),
            gzserver,
            gzclient,
            spawn,
        ]),
    ])
