#!/usr/bin/env python3
"""Live health of the SLAM chain, link by link. See car_tracker_design/deployment.md.

    ros2 run car_tracker chain_check.py          # one pass
    ros2 run car_tracker chain_check.py --watch  # refresh until Ctrl-C

Each link names the topic, the rate it should carry, and the node that feeds it,
so a dead link points at one process rather than at "SLAM is broken".
"""
import argparse
import collections
import math
import os
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import (DurabilityPolicy, HistoryPolicy, QoSProfile,
                       ReliabilityPolicy, qos_profile_sensor_data)

from geometry_msgs.msg import PoseWithCovarianceStamped
from nav_msgs.msg import OccupancyGrid, Odometry
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import UInt16
from tf2_msgs.msg import TFMessage

# topic, type, qos, expected Hz (None = event driven), the node that feeds it
CHAIN = [
    ('/scan',      LaserScan, 'sensor',  10.0, 'LD19            lidar driver'),
    ('/odom_raw',  Odometry,  'default', 10.0, 'rf2o            laser odometry'),
    ('/imu',       Imu,       'default', 48.0, 'imu_filter      madgwick'),
    ('/odom',      Odometry,  'default', 30.0, 'ekf_odom        fused estimate'),
    ('/map',       OccupancyGrid, 'latched', None, 'slam_toolbox    map (only on movement)'),
    ('/pose',      PoseWithCovarianceStamped, 'default', None, 'slam_toolbox    map-frame pose'),
    ('/ros_robot_controller/battery', UInt16, 'default', None, 'ros_robot_ctl   pack voltage (not a chain link)'),
]

QOS = {
    'sensor': qos_profile_sensor_data,
    'default': QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                          history=HistoryPolicy.KEEP_LAST),
    'latched': QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                          history=HistoryPolicy.KEEP_LAST,
                          durability=DurabilityPolicy.TRANSIENT_LOCAL),
}

C_OK, C_BAD, C_WARN, C_DIM, C_OFF = (
    '\033[32m', '\033[31m', '\033[33m', '\033[2m', '\033[0m')


class ChainCheck(Node):
    def __init__(self):
        super().__init__('chain_check')
        self.counts = collections.Counter()
        self.tf = set()
        self.subs = []
        for topic, cls, qos, _, _ in CHAIN:
            self.subs.append(self.create_subscription(
                cls, topic, lambda m, t=topic: self.counts.update([t]), QOS[qos]))
        self.create_subscription(
            TFMessage, '/tf',
            lambda m: [self.tf.add((t.header.frame_id, t.child_frame_id))
                       for t in m.transforms],
            QOS['default'])

    def sample(self, seconds):
        self.counts.clear()
        self.tf.clear()
        t0 = time.time()
        while time.time() - t0 < seconds:
            rclpy.spin_once(self, timeout_sec=0.05)
        return time.time() - t0


def render(node, window):
    live = {n for n, _ in node.get_node_names_and_namespaces()}
    out = []
    out.append(f"{C_DIM}topic                            rate      expected  source{C_OFF}")
    broken = []
    for topic, _, _, want, who in CHAIN:
        hz = node.counts.get(topic, 0) / window
        if want is None:
            ok = hz > 0
            shown = f"{hz:6.2f}" if hz else "     -"
            exp = "on change"
            colour = C_OK if ok else C_DIM
        else:
            ok = hz >= want * 0.5
            shown = f"{hz:6.2f}" if hz else "     -"
            exp = f"~{want:g} Hz"
            colour = C_OK if ok else C_BAD
            if not ok and 'not a chain link' not in who:
                broken.append((topic, who))
        out.append(f"{colour}{topic:32s} {shown} Hz  {exp:9s} {who}{C_OFF}")

    out.append("")
    for parent, child in (('map', 'odom'), ('odom', 'base_footprint')):
        present = (parent, child) in node.tf
        colour = C_OK if present else C_BAD
        mark = 'live' if present else 'MISSING'
        out.append(f"{colour}tf  {parent:5s} -> {child:16s} {mark}{C_OFF}")

    out.append("")
    for name in ('LD19', 'rf2o_laser_odometry', 'ekf_odom', 'slam_toolbox',
                 'ros_robot_controller', 'imu_filter'):
        up = name in live
        out.append(f"{C_OK if up else C_BAD}node {name:24s} "
                   f"{'up' if up else 'DOWN'}{C_OFF}")

    if broken:
        out.append("")
        out.append(f"{C_WARN}first broken link: {broken[0][0]} "
                   f"({broken[0][1].split()[0]}){C_OFF}")
        out.append(f"{C_DIM}a dead link starves everything to its right; fix the "
                   f"leftmost one first.{C_OFF}")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--watch', action='store_true', help='refresh until Ctrl-C')
    ap.add_argument('--window', type=float, default=4.0, help='sample seconds')
    args = ap.parse_args()

    rclpy.init()
    node = ChainCheck()
    try:
        while True:
            window = node.sample(args.window)
            text = render(node, window)
            if args.watch:
                os.system('clear')
                print(f"{C_DIM}chain_check  {time.strftime('%H:%M:%S')}  "
                      f"{window:.1f}s window  Ctrl-C to stop{C_OFF}\n")
            print(text)
            if not args.watch:
                break
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
