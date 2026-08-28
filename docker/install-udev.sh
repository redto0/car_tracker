#!/usr/bin/env bash
# Installs the udev rules ON THE PI HOST. Docs: car_tracker_design/deployment.md
set -euo pipefail

RULES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/udev/99-car-tracker.rules"
[ -f "$RULES" ] || { echo "missing: $RULES" >&2; exit 1; }

sudo cp "$RULES" /etc/udev/rules.d/99-car-tracker.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "installed. replug the lidar and controller, then check:"
echo "  ls -l /dev/rrc /dev/ldlidar"
