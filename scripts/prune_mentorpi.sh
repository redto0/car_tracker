#!/usr/bin/env bash
# Ignore the MentorPi packages we do not use.
#
# Hiwonder ship a 17-package monorepo; we want the driver layer and nothing else.
# The rest pull heavy Python dependencies (torch via yolov5_ros2, LLM clients via
# large_models) and duplicate our own slam/navigation stack.
#
# Drops both marker files on purpose: colcon honours COLCON_IGNORE, rosdep's
# crawler honours AMENT_IGNORE. Only dropping one leaves the other tool walking
# into packages we deliberately excluded.
#
# Idempotent. Run from the workspace root after every `vcs import`.
#
#   ./src/car_tracker/scripts/prune_mentorpi.sh [path-to-MentorPi]

set -euo pipefail

MP="${1:-src/MentorPi}"
KEEP="driver peripherals interfaces simulations"

if [ ! -d "$MP" ]; then
    echo "error: $MP not found. Run from the workspace root, after vcs import." >&2
    exit 1
fi

for d in "$MP"/*/; do
    name=$(basename "$d")
    case " $KEEP " in
        *" $name "*)
            rm -f "$d/COLCON_IGNORE" "$d/AMENT_IGNORE"
            printf '  keep    %s\n' "$name"
            ;;
        *)
            touch "$d/COLCON_IGNORE" "$d/AMENT_IGNORE"
            printf '  ignore  %s\n' "$name"
            ;;
    esac
done
