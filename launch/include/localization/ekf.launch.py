"""robot_localization EKFs. See car_tracker_design/nodes/ekf.md."""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')
_DEFAULT_PARAMS = PathJoinSubstitution([FindPackageShare(_PKG), 'config', 'ekf.yaml'])


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    # odom_raw, not odom: /odom is Hiwonder's own EKF output. Their controller
    # is launched with enable_odom:=false so this filter owns odom -> base_footprint.
    odom_topic = wiring['topics']['odom_raw']
    imu_topic = wiring['topics']['imu']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    use_map_ekf = LaunchConfiguration('use_map_ekf')

    sim_time = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the filters into.'),
        DeclareLaunchArgument(
            'params_file', default_value=_DEFAULT_PARAMS,
            description='robot_localization parameters (config/ekf.yaml).'),
        DeclareLaunchArgument(
            'use_map_ekf', default_value='false',
            description='Also run the global map-frame EKF. Requires '
                        'slam_toolbox transform_publish_period:=0.0, or the two '
                        'fight over map -> odom.'),
    ]

    # Local filter: odom -> base_footprint. Continuous, never jumps.
    ekf_odom = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_odom',
        output='screen',
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('odom_raw', odom_topic),
            ('imu', imu_topic),
            # robot_localization publishes its estimate on odometry/filtered by
            # default. Split the two filters' outputs so they are separable in
            # rviz and rosbag.
            ('odometry/filtered', 'odometry/filtered/local'),
            ('accel/filtered', 'accel/filtered/local'),
            ('set_pose', 'ekf_odom/set_pose'),
        ],
    )

    # Global filter: map -> base_footprint. Jumps on loop closure, which is correct;
    # never differentiate its output for velocity.
    ekf_map = Node(
        package='robot_localization',
        executable='ekf_node',
        name='ekf_map',
        output='screen',
        condition=IfCondition(use_map_ekf),
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('odom_raw', odom_topic),
            ('imu', imu_topic),
            # slam_toolbox publishes its map-frame estimate on /pose.
            ('slam_pose', 'pose'),
            ('odometry/filtered', 'odometry/filtered/global'),
            ('accel/filtered', 'accel/filtered/global'),
            ('set_pose', 'ekf_map/set_pose'),
        ],
    )

    return LaunchDescription(
        args + [
            GroupAction([
                PushRosNamespace(namespace),
                ekf_odom,
                ekf_map,
            ])
        ]
    )
