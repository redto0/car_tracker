"""Nav2. See car_tracker_design/deployment/nav2.launch.md."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_CONTAINER = 'nav2_container'


def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    autostart = LaunchConfiguration('autostart')
    use_composition = LaunchConfiguration('use_composition')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the Nav2 stack into.'),
        DeclareLaunchArgument(
            'params_file',
            default_value=PathJoinSubstitution(
                [FindPackageShare(_PKG), 'config', 'nav2_params.yaml']),
            description='Nav2 parameters (config/nav2_params.yaml).'),
        DeclareLaunchArgument(
            'autostart', default_value='true',
            description='Transition the lifecycle nodes up automatically.'),
        DeclareLaunchArgument(
            'use_composition', default_value='True',
            description='Run the servers in one component container. Worth '
                        'keeping on for a Pi -- it avoids serializing costmaps '
                        'between processes. MUST be capitalized True/False: '
                        'navigation_launch.py feeds this to PythonExpression, '
                        "so lowercase 'true' raises NameError at launch."),
    ]

    # navigation_launch.py does NOT create the component container it loads into
    # -- bringup_launch.py normally does that. Including navigation_launch.py on
    # its own with composition on therefore starts nothing at all, silently. So
    # create the container here.
    container = Node(
        name=_CONTAINER,
        package='rclcpp_components',
        executable='component_container_isolated',
        output='screen',
        condition=IfCondition(use_composition),
        parameters=[params_file, {'autostart': autostart}],
    )

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare('nav2_bringup'), 'launch', 'navigation_launch.py'])),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'params_file': params_file,
            'autostart': autostart,
            'use_composition': use_composition,
            'container_name': _CONTAINER,
        }.items(),
    )

    return LaunchDescription(
        args + [
            GroupAction([
                PushRosNamespace(namespace),
                # Nav2's inputs and outputs, written out even though every one is
                # already conventional, so the stack's topic surface is readable
                # here rather than only inside nav2_bringup.
                SetRemap(src='cmd_vel', dst='cmd_vel'),
                SetRemap(src='odom', dst='odom'),
                SetRemap(src='scan', dst='scan'),
                SetRemap(src='map', dst='map'),
                container,
                nav2,
            ])
        ]
    )
