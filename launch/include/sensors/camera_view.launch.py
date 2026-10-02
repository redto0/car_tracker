"""Driver + live viewer, for looking at the camera. See car_tracker_design/nodes/camera.md."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import os

_ASCAMERA = 'ascamera'


def generate_launch_description():
    # Resolved eagerly: the SDK needs a real absolute path, and it opendir()s it
    # before any substitution context exists.
    confipath = os.path.join(get_package_share_directory(_ASCAMERA), 'configurationfiles')

    topic = LaunchConfiguration('topic')

    return LaunchDescription([
        DeclareLaunchArgument(
            'topic', default_value='/ascamera/rgb0/image',
            description='Which image to show. /ascamera/depth0/image_raw for depth.'),

        # Renamed, NOT namespaced. The vendor publishes private (~/) topics, so
        # they resolve under the node name: this gives /ascamera/rgb0/image.
        Node(
            package=_ASCAMERA,
            executable='ascamera_node',
            name=_ASCAMERA,
            output='screen',
            parameters=[{
                'confiPath': confipath,
                'rgb_width': 640,
                'rgb_height': 480,
                'depth_width': 640,
                'depth_height': 480,
                'fps': 15,
                'pub_tfTree': True,
                'usb_bus_no': -1,
                'usb_path': 'null',
            }],
        ),

        # The SDK streams on demand -- it idles until something subscribes, so the
        # viewer is what actually wakes the camera up.
        Node(
            package='rqt_image_view',
            executable='rqt_image_view',
            name='camera_view',
            output='screen',
            arguments=[topic],
        ),
    ])
