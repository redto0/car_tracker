# camera.launch.py

## Summary

MentorPi depth camera bringup. Runs on the **Pi**.

Wraps Hiwonder's `peripherals/depth_camera.launch.py`, normalizes its topic names, and
produces a downscaled JPEG stream for the Pi→desktop link.

## Pipeline

```
vendor depth_camera -> /camera/color/image_raw
                       /camera/color/image_raw/compressed   (vendor JPEG)
                       /camera/color/camera_info
                       /camera/depth/image_rect_raw
                       /camera/depth/camera_info
      |
      v  resize_node                640x480 -> 480x360
/camera/color/downscaled/image_raw
      |
      v  republish raw -> compressed
/camera/color/downscaled/image_raw/compressed    <- the Pi->desktop wire topic
```

## Publishes

Normalized from the vendor names in `config/camera_wiring.yaml`. The desktop subscribes to
`/camera/color/downscaled/image_raw/compressed`.

## Arguments

- `use_sim_time` (`false`)
- `namespace` (`''`)
- `params_file` (`config/camera_params.yaml`)
- `launch_driver` (`true`) - false runs only the resize/compress pipeline against an
  already-running driver.
- `publish_downscaled` (`true`)

## Notes

**The `ascamera` package is not public.** It lives in a separate
`third_party_ros2/third_party_ws` on Hiwonder's SD image, referenced by absolute path. It
is the one driver that still has to be recovered from the image or from Angstrong.

**Vendor naming breaks `image_transport`.** They publish `.../image_compressed` instead of
the conventional `.../image_raw/compressed`, which defeats automatic compressed-topic
discovery. The remap in `camera_wiring.yaml` is what makes it work downstream.

**Resolution.** Hiwonder configure `ascamera_node` at 640×480 @ 15 fps, not the 1920×1080
the product page advertises. Raw at that rate is still ~110 Mbit/s, so the JPEG step is
what matters; the resize is a secondary saving. 480×360 keeps 4:3 — 640×360 would stretch
the image and quietly bias a texture-based terrain classifier.
