"""rf2o laser odometry. See car_tracker_design/nodes/ekf.md.

Topic surface
-------------
subscribes  scan          sensor_msgs/LaserScan   from the lidar driver
publishes   odom_raw      nav_msgs/Odometry       ekf_odom's odom0

Publishes no TF. ekf_odom owns odom -> base_footprint; two broadcasters on one
transform is the failure this launch exists to avoid.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    scan_topic = wiring['topics']['scan']
    odom_topic = wiring['topics']['odom_raw']
    frames = wiring['frames']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    freq = LaunchConfiguration('freq')

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push the node into.'),
        DeclareLaunchArgument(
            'freq', default_value='10.0',
            description='Estimation rate. Match the lidar: the LD19 scans at 10 Hz '
                        'and asking for more just reprocesses the same scan.'),
    ]

    laser_odom = Node(
        package='rf2o_laser_odometry',
        executable='rf2o_laser_odometry_node',
        name='rf2o_laser_odometry',
        output='screen',
        parameters=[{
            'laser_scan_topic': scan_topic,
            'odom_topic': odom_topic,
            # Upstream defaults this to True, which would fight ekf_odom.
            'publish_tf': False,
            'base_frame_id': frames['base'],
            'odom_frame_id': frames['odom'],
            'init_pose_from_topic': '',
            'freq': ParameterValue(freq, value_type=float),
            'use_sim_time': ParameterValue(use_sim_time, value_type=bool),
        }],
    )

    return LaunchDescription(
        args + [GroupAction([PushRosNamespace(namespace), laser_odom])]
    )
