# MIT License
#
# Copyright (c) 2021 Intelligent Systems Club
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""MentorPi depth camera bringup. See docs/camera.launch.md."""

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

    # Vendor driver. Hiwonder ships a launch file, not a bare node, so this is an
    # include and the remaps go through SetRemap in the GroupAction below --
    # remappings= cannot be passed to an IncludeLaunchDescription.
    driver = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            PathJoinSubstitution(
                [FindPackageShare(driver_cfg['package']), 'launch', driver_cfg['launch_file']])),
        condition=IfCondition(launch_driver),
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

    return LaunchDescription(
        args + env + [
            GroupAction([PushRosNamespace(namespace)] + remaps + [
                driver,
                resize,
                republish,
            ])
        ]
    )
