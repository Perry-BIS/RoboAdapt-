"""Pose sensors. Level 0 is explicitly truth plus synthetic noise."""

from __future__ import annotations

import numpy as np


def noisy_pose_sensor(true_xy: np.ndarray, sigma_m: float, rng: np.random.Generator) -> np.ndarray:
    """Return a noisy x/y observation without modifying the simulator state."""
    true_xy = np.asarray(true_xy, dtype=float)
    if true_xy.shape != (2,):
        raise ValueError("true_xy must have shape (2,)")
    if sigma_m < 0:
        raise ValueError("sigma_m must be non-negative")
    return true_xy + rng.normal(0.0, sigma_m, size=2)


def rgb_centroid_pose_sensor(env, *, width: int = 320, height: int = 320, plane_z: float = 0.044):
    """Detect the orange cube in a rendered RGB image and back-project its centroid.

    This Level-1 sensor uses a known camera calibration and known cube-top plane.
    It returns ``(xy, confidence, centroid_uv, rgb)``. Confidence is a simple
    normalized detected-area heuristic, not a learned probability.
    """
    import mujoco

    renderer = mujoco.Renderer(env.model, height=height, width=width)
    renderer.update_scene(env.data, camera="topdown")
    rgb = renderer.render().copy()
    renderer.close()
    red, green, blue = (rgb[..., i].astype(float) for i in range(3))
    # Use channel differences rather than raw ratios because the lit top face is
    # deliberately bright and partially desaturated by the renderer.
    mask = (red > 220) & ((red - green) > 40) & ((green - blue) > 30)
    rows, cols = np.nonzero(mask)
    if len(cols) < 12:
        raise RuntimeError("RGB cube detector found too few orange pixels")
    u, v = float(cols.mean()), float(rows.mean())

    cam_id = env.model.camera("topdown").id
    origin = env.data.cam_xpos[cam_id].copy()
    rotation = env.data.cam_xmat[cam_id].reshape(3, 3)
    f = 0.5 * height / np.tan(np.deg2rad(env.model.cam_fovy[cam_id]) / 2)
    ray_camera = np.array([(u - (width - 1) / 2) / f, -(v - (height - 1) / 2) / f, -1.0])
    ray_world = rotation @ ray_camera
    scale = (plane_z - origin[2]) / ray_world[2]
    point = origin + scale * ray_world
    confidence = float(min(1.0, len(cols) / 500.0))
    return point[:2], confidence, (u, v), rgb

