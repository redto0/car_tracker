"""RViz, desktop only. See car_tracker_design/nodes/rviz.md."""

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
            # Project config. slam_toolbox's default is Grid + TF only -- no Map
            # and no LaserScan display -- so it shows nothing of the SLAM output.
            default_value=PathJoinSubstitution(
                [FindPackageShare('car_tracker'), 'config', 'car_tracker.rviz']),
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
        # Identity, but recorded: these are the topics the loaded .rviz config
        # publishes from its tools. Confirmed against the config file itself.
        remappings=[
            ('initialpose', 'initialpose'),
            ('goal_pose', 'goal_pose'),
            ('clicked_point', 'clicked_point'),
        ],
    )

    return LaunchDescription(args + [rviz])
