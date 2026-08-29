"""MentorPi depth camera bringup. See car_tracker_design/nodes/camera.md."""

import os

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            SetEnvironmentVariable)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node, PushRosNamespace, SetRemap
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

_PKG = 'car_tracker'

# The two config paths resolve differently on purpose.
#
# The wiring file must be read EAGERLY, as a real filesystem path, because
# remaps and executable names are needed while the launch description is being
# built -- before any substitution context exists. get_package_share_directory
# returns a plain string; FindPackageShare would not resolve until later.
_DEFAULT_WIRING = os.path.join(get_package_share_directory(_PKG), 'config', 'camera_wiring.yaml')

# params_file is only consumed by nodes at execution time, so it stays a
# substitution and remains overridable from the command line.
_DEFAULT_PARAMS = PathJoinSubstitution([FindPackageShare(_PKG), 'config', 'camera_params.yaml'])


def generate_launch_description():
    # Wiring is read here, at launch-description build time, because remaps and
    # executable names must be resolved before any node exists. That rules out
    # LaunchConfiguration for them -- hence a plain YAML read.
    with open(_DEFAULT_WIRING) as f:
        wiring = yaml.safe_load(f)

    driver_cfg = wiring['driver']
    remaps = [SetRemap(src=k, dst=v) for k, v in wiring['remaps'].items()]
    pipe = wiring['pipeline']
    env = [SetEnvironmentVariable(k, str(v)) for k, v in wiring['env'].items()]

    use_sim_time = LaunchConfiguration('use_sim_time')
    namespace = LaunchConfiguration('namespace')
    params_file = LaunchConfiguration('params_file')
    launch_driver = LaunchConfiguration('launch_driver')
    publish_downscaled = LaunchConfiguration('publish_downscaled')

    # A LaunchConfiguration in a parameter dict evaluates to a STRING, so a bool
    # param needs an explicit value_type or the node is handed "false".
    sim_time = ParameterValue(use_sim_time, value_type=bool)

    args = [
        DeclareLaunchArgument(
            'use_sim_time', default_value='false',
            description='Use /clock instead of wall time. False on real hardware: '
                        'true with no clock publisher hangs every node silently.'),
        DeclareLaunchArgument(
            'namespace', default_value='',
            description='Namespace to push all camera nodes and topics into.'),
        DeclareLaunchArgument(
            'params_file', default_value=_DEFAULT_PARAMS,
            description='Runtime node parameters (config/camera_params.yaml).'),
        DeclareLaunchArgument(
            'launch_driver', default_value='true',
            description='Launch the vendor driver. False runs only the '
                        'resize/compress pipeline against an already-running one, '
                        'e.g. the driver inside the Hiwonder container.'),
        DeclareLaunchArgument(
            'publish_downscaled', default_value='true',
            description='Publish the downscaled + JPEG stream for the Pi->desktop link.'),
    ]

    # ascamera_node is launched directly rather than through a vendor launch file.
    # Both of theirs hardcode confiPath to a path that only exists on Hiwonder's SD
    # image, so including either dies with "cannot find config file" -- after the
    # node has already created its topics, which reads as a camera fault rather
    # than a packaging one. Resolving the path from the installed share dir here
    # is what makes this work on a machine that is not theirs.
    driver = Node(
        package=driver_cfg['package'],
        executable=driver_cfg['executable'],
        name=driver_cfg['name'],
        # NO name= override. The vendor publishes PRIVATE (~/) topics, so they
        # resolve under the NODE NAME: the default 'camera_publisher' yields
        # <ns>/camera_publisher/rgb0/image, which is what the remaps and
        # Hiwonder's own docs expect. Setting name= here silently renames every
        # topic, so no remap matches and the pipeline gets no input.
        output='screen',
        condition=IfCondition(launch_driver),
        parameters=[params_file, {
            'use_sim_time': sim_time,
            'confiPath': PathJoinSubstitution(
                [FindPackageShare(driver_cfg['package']), 'configurationfiles']),
        }],
    )

    # image_proc::ResizeNode subscribes image/image_raw + image/camera_info and
    # publishes resize/image_raw + resize/camera_info. All four remapped
    # explicitly, including the camera_info pair that is only carried along.
    resize = Node(
        package='image_proc',
        executable='resize_node',
        name='camera_resize',
        output='screen',
        condition=IfCondition(publish_downscaled),
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('image/image_raw', pipe['color_image']),
            ('image/camera_info', pipe['color_info']),
            ('resize/image_raw', pipe['downscaled_image']),
            ('resize/camera_info', pipe['downscaled_info']),
        ],
    )

    # republish takes in_transport/out_transport positionally and remaps on
    # 'in'/'out'. With out_transport=compressed it publishes <out>/compressed,
    # so 'out' is a base name, not the final topic.
    republish = Node(
        package='image_transport',
        executable='republish',
        name='camera_republish',
        output='screen',
        condition=IfCondition(publish_downscaled),
        arguments=['raw', 'compressed'],
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('in', pipe['downscaled_image']),
            ('out', pipe['downscaled_image']),
        ],
    )

    # Depth over the wire: compressedDepth is PNG-based and lossless, which JPEG
    # is not. Measured 52.6 Mbit/s raw -> ~2.3 Mbit/s. Kept separate from the RGB
    # republish because the transports differ.
    depth_republish = Node(
        package='image_transport',
        executable='republish',
        name='depth_republish',
        output='screen',
        condition=IfCondition(publish_downscaled),
        arguments=['raw', 'compressedDepth'],
        parameters=[params_file, {'use_sim_time': sim_time}],
        remappings=[
            ('in', pipe['depth_image']),
            ('out', pipe['depth_image']),
        ],
    )

    return LaunchDescription(
        args + env + [
            GroupAction([PushRosNamespace(namespace)] + remaps + [
                driver,
                resize,
                republish,
                depth_republish,
            ])
        ]
    )
