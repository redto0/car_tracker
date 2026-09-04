"""Did anything move, and did it reach the map?

    ros2 run car_tracker dynamic_probe.py [seconds]

Answers the question "are moving objects polluting the map" with a measurement
instead of an opinion. Measured 2026-09-04 with the robot stationary: layer 1
saw movement (4 beams/scan jumping >0.1 m, 58% of scans) while layer 2 stayed
flat (11 born, 11 died over 60 frames) -- slam_toolbox was already rejecting
transients at occupancy_threshold 0.1, so no tuning was warranted.

Note the LD19 emits variable-length scans, so only pairs of equal length are
compared; expect roughly a third of consecutive pairs to be skipped.


Layer 1: /scan   -- per-beam range change between consecutive scans.
Layer 2: /map    -- occupied cells appearing/disappearing.

Movement in layer 1 with none in layer 2 means SLAM is already rejecting
transients. Movement in both means they are polluting the map.
"""
import sys, time, math, statistics as st, rclpy
from rclpy.node import Node
from rclpy.qos import (QoSProfile, ReliabilityPolicy, DurabilityPolicy,
                       HistoryPolicy, qos_profile_sensor_data)
from sensor_msgs.msg import LaserScan
from nav_msgs.msg import OccupancyGrid

WINDOW = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
MOVE_M = 0.10   # a beam changing more than this is "something moved"

class N(Node):
    def __init__(self):
        super().__init__('dynamic_probe')
        self.prev_scan = None
        self.scans = 0
        self.moved_beams = []      # per-scan count of beams that jumped
        self.max_jump = 0.0
        self.prev_occ = None
        self.map_frames = 0
        self.born = 0
        self.died = 0
        self.create_subscription(LaserScan, '/scan', self.scan_cb,
                                 qos_profile_sensor_data)
        self.create_subscription(
            OccupancyGrid, '/map', self.map_cb,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                       history=HistoryPolicy.KEEP_LAST,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def scan_cb(self, m):
        cur = list(m.ranges)
        if self.prev_scan is not None and len(cur) == len(self.prev_scan):
            n = 0
            for a, b in zip(cur, self.prev_scan):
                if (math.isfinite(a) and math.isfinite(b)
                        and a > 0.01 and b > 0.01):
                    d = abs(a - b)
                    if d > MOVE_M:
                        n += 1
                        self.max_jump = max(self.max_jump, d)
            self.moved_beams.append(n)
        self.prev_scan = cur
        self.scans += 1

    def map_cb(self, m):
        res, ox, oy = m.info.resolution, m.info.origin.position.x, m.info.origin.position.y
        occ = {(round(ox + (i % m.info.width)*res, 2),
                round(oy + (i // m.info.width)*res, 2))
               for i, v in enumerate(m.data) if v > 50}
        if self.prev_occ is not None:
            self.born += len(occ - self.prev_occ)
            self.died += len(self.prev_occ - occ)
        self.prev_occ = occ
        self.map_frames += 1

rclpy.init(); n = N(); t0 = time.time()
while time.time() - t0 < WINDOW:
    rclpy.spin_once(n, timeout_sec=0.05)

print(f"window={time.time()-t0:.0f}s  scans={n.scans}  map_frames={n.map_frames}")
if n.moved_beams:
    tot = sum(n.moved_beams)
    busy = sum(1 for x in n.moved_beams if x > 3)
    print(f"LAYER 1  /scan")
    print(f"  beams jumping >{MOVE_M} m : {tot} total, "
          f"mean {st.mean(n.moved_beams):.1f}/scan, max {max(n.moved_beams)}/scan")
    print(f"  scans with >3 moving beams: {busy}/{len(n.moved_beams)} "
          f"({100.0*busy/len(n.moved_beams):.0f}%)")
    print(f"  largest single jump       : {n.max_jump:.2f} m")
    print(f"  VERDICT: {'MOVEMENT DETECTED' if busy > len(n.moved_beams)*0.05 else 'scene is static'}")
print(f"LAYER 2  /map")
print(f"  occupied cells born={n.born} died={n.died} over {n.map_frames} frames")
print(f"  VERDICT: {'transients ARE reaching the map' if (n.born+n.died) > 40 else 'map is stable'}")
n.destroy_node(); rclpy.shutdown()
