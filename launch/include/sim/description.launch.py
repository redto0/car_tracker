"""Simulated robot description. See car_tracker_design/sim_integration.md.

The vendor URDF plus Gazebo tags, published on the same /robot_description the
hardware uses. Runs INSTEAD of base/description.launch.py, never alongside it.

Topic surface
-------------
publishes   robot_description   std_msgs/String        latched
publishes   joint_states        sensor_msgs/JointState

The simulated sensors' topic surface, which the Gazebo plugins produce once
this description is spawned:

    subscribes  cmd_vel                        -> planar_move
    publishes   scan                           <- ray sensor
    publishes   ros_robot_controller/imu_raw   <- imu sensor
    publishes   sim/ground_truth               <- p3d, MEASUREMENT ONLY
    publishes   camera/color/image_raw         <- camera, only with sim_camera

Those names are passed into the xacro from robot_wiring.yaml below rather than
hardcoded in the XML, so this file is the one place the simulated robot's
wiring is declared.
"""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, GroupAction, SetEnvironmentVariable
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'
_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'robot_wiring.yaml')

# The raw IMU, not the filtered one: imu_calib and imu_filter then run exactly
# as they do on hardware instead of being short-circuited. Not in
# robot_wiring.yaml because it is the vendor driver's own private name.
_IMU_RAW = 'ros_robot_controller/imu_raw'
_GROUND_TRUTH = 'sim/ground_truth'


def generate_launch_description():
    with open(_WIRING) as f:
        wiring = yaml.safe_load(f)

    topics = wiring['topics']
    frames = wiring['frames']

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    sim_camera = LaunchConfiguration('sim_camera')

    # MACHINE_TYPE is what the vendor xacro dispatches mecanum vs ackermann on.
    env = [SetEnvironmentVariable(k, str(v)) for k, v in wiring['env'].items()]

    robot_description = ParameterValue(
        Command([
            'xacro ',
            PathJoinSubstitution([FindPackageShare(_PKG), 'urdf', 'mentorpi_sim.xacro']),
            # Every simulated topic and frame, declared here rather than in XML.
            ' sim_camera:=', sim_camera,
            ' cmd_vel_topic:=', topics['cmd_vel'],
            ' scan_topic:=', topics['scan'],
            ' imu_raw_topic:=', _IMU_RAW,
            ' ground_truth_topic:=', _GROUND_TRUTH,
            ' camera_namespace:=/camera',
            ' camera_name:=color',
            ' base_frame:=', frames['base'],
            ' odom_frame:=', frames['odom'],
            ' lidar_frame:=', frames['lidar'],
            ' imu_frame:=', frames['imu'],
            ' camera_frame:=depth_cam',
        ]),
        value_type=str,
    )

    state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': ParameterValue(use_sim_time, value_type=bool)}],
        remappings=[
            ('robot_description', 'robot_description'),
            ('joint_states', 'joint_states'),
        ],
    )

    # Gazebo drives the wheel joints, so unlike the hardware description this
    # needs no joint_state_publisher: the gazebo_ros_joint_state_publisher in
    # the model reports them.
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                'use_sim_time', default_value='true',
                description='True here: the simulator owns the clock.'),
            DeclareLaunchArgument(
                'namespace', default_value='',
                description='Namespace to push the description into.'),
            DeclareLaunchArgument(
                'sim_camera', default_value='false',
                description='Simulate the camera. OFF by default: gzserver '
                            'renders it even headless and it costs real-time '
                            'factor. Perception is not validated in sim.'),
        ] + env + [
            GroupAction([
                PushRosNamespace(namespace),
                state_publisher,
            ])
        ]
    )
