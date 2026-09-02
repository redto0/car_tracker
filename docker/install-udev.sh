#!/usr/bin/env bash
# Installs the udev rules ON THE PI HOST. Docs: car_tracker_design/deployment.md
set -euo pipefail

RULES="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/udev/99-car-tracker.rules"
[ -f "$RULES" ] || { echo "missing: $RULES" >&2; exit 1; }

sudo cp "$RULES" /etc/udev/rules.d/99-car-tracker.rules
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=tty --subsystem-match=video --subsystem-match=input
sudo udevadm settle

# trigger re-runs the rules against devices that are already plugged in, so the
# symlinks appear without a replug. A missing one means that device is absent,
# not that the rule is wrong -- warn, do not fail.
echo
missing=()
for link in rrc imu ldlidar; do
  if [ -e "/dev/$link" ]; then
    printf '  ok       /dev/%-8s -> %s\n' "$link" "$(readlink -f "/dev/$link")"
  else
    printf '  MISSING  /dev/%s\n' "$link"
    missing+=("$link")
  fi
done

if [ ${#missing[@]} -gt 0 ]; then
  echo
  echo "not created: ${missing[*]}"
  echo "replug the device, then check what the bus actually shows:"
  echo "  lsusb; ls -l /dev/serial/by-id/"
fi

# /dev/imu is the same node as /dev/rrc by design: the IMU is on the controller
# board, not a separate USB device.
