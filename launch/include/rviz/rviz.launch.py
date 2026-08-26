"""RViz, desktop only. See docs/rviz.launch.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('use_rviz')
    rviz_config = LaunchConfiguration('rviz_config')

    sim_time = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'use_rviz', default_value='true',
            description='Set false to include this file without actually starting rviz.'),
        DeclareLaunchArgument(
            'rviz_config',
            # slam_toolbox ships a config with the map, scan and pose graph
            # already set up, which is the right starting view for steps 5-6 of
            # the build order. Swap for a project config once one exists.
            default_value=PathJoinSubstitution(
                [FindPackageShare('slam_toolbox'), 'config', 'slam_toolbox_default.rviz']),
            description='RViz config file.'),
    ]

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        condition=IfCondition(use_rviz),
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': sim_time}],
    )

    return LaunchDescription(args + [rviz])
