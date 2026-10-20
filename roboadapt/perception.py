"""Pose sensors for oracle and image-based manipulation experiments."""

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


def perturb_rgb_image(
    rgb: np.ndarray,
    *,
    rng: np.random.Generator,
    image_noise_std: float = 0.0,
    occlusion_fraction: float = 0.0,
) -> np.ndarray:
    """Apply deterministic image-domain perturbations without simulator truth.

    ``image_noise_std`` is per-channel Gaussian noise in 8-bit intensity units.
    ``occlusion_fraction`` covers that fraction of image width with a vertical
    dark occluder at a seeded random horizontal position. Neither operation reads
    object pose or segmentation labels.
    """
    if image_noise_std < 0:
        raise ValueError("image_noise_std must be non-negative")
    if not 0.0 <= occlusion_fraction < 1.0:
        raise ValueError("occlusion_fraction must be in [0, 1)")
    perturbed = np.asarray(rgb, dtype=np.uint8).copy()
    if image_noise_std > 0:
        noise = rng.normal(0.0, image_noise_std, size=perturbed.shape)
        perturbed = np.clip(perturbed.astype(float) + noise, 0, 255).astype(np.uint8)
    if occlusion_fraction > 0:
        width = perturbed.shape[1]
        occluder_width = max(1, int(round(width * occlusion_fraction)))
        left = int(rng.integers(0, width - occluder_width + 1))
        perturbed[:, left : left + occluder_width] = 0
    return perturbed


def rgb_centroid_pose_sensor(
    env,
    *,
    width: int = 320,
    height: int = 320,
    plane_z: float = 0.044,
    rng: np.random.Generator | None = None,
    image_noise_std: float = 0.0,
    occlusion_fraction: float = 0.0,
):
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
    if rng is None:
        rng = np.random.default_rng(0)
    rgb = perturb_rgb_image(
        rgb,
        rng=rng,
        image_noise_std=image_noise_std,
        occlusion_fraction=occlusion_fraction,
    )
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

