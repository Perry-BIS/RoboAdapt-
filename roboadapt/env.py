"""MuJoCo environment for a contact-based Cartesian pick-and-place task."""

from __future__ import annotations

from pathlib import Path
import hashlib
import numpy as np
import mujoco


class RoboAdaptEnv:
    dt = 0.002
    goal_xy = np.array([0.18, 0.14], dtype=float)
    open_grip = 0.0
    close_grip = 0.036

    def __init__(self) -> None:
        self.model_path = Path(__file__).parent / "assets" / "scene.xml"
        self.model = mujoco.MjModel.from_xml_path(str(self.model_path))
        self.data = mujoco.MjData(self.model)
        self._cube_joint = self.model.joint("cube_free").qposadr[0]
        self._cube_body = self.model.body("cube").id
        self._steps = 0

    @property
    def model_hash(self) -> str:
        return hashlib.sha256(self.model_path.read_bytes()).hexdigest()[:16]

    @property
    def steps(self) -> int:
        return self._steps

    @property
    def cube_position(self) -> np.ndarray:
        return self.data.xpos[self._cube_body].copy()

    def reset(self, object_xy: np.ndarray) -> np.ndarray:
        mujoco.mj_resetData(self.model, self.data)
        # Park away from the randomized object region so the optional top camera
        # has an unoccluded initial observation.
        self.data.qpos[0:5] = [0.20, -0.20, 0.26, self.open_grip, self.open_grip]
        adr = self._cube_joint
        self.data.qpos[adr : adr + 7] = [float(object_xy[0]), float(object_xy[1]), 0.023, 1, 0, 0, 0]
        self.data.ctrl[:] = [0.20, -0.20, 0.26, self.open_grip, self.open_grip]
        self._steps = 0
        mujoco.mj_forward(self.model, self.data)
        self.step_for(0.25)
        return self.cube_position

    def displace_cube(self, delta_xy: np.ndarray) -> None:
        adr = self._cube_joint
        self.data.qpos[adr : adr + 2] += np.asarray(delta_xy, dtype=float)
        self.data.qvel[self.model.joint("cube_free").dofadr[0] :][:6] = 0
        mujoco.mj_forward(self.model, self.data)
        self.step_for(0.15)

    def step_for(self, seconds: float, frames: list[np.ndarray] | None = None, renderer=None, camera="overview") -> None:
        count = max(1, int(round(seconds / self.dt)))
        stride = max(1, int(round(1 / (30 * self.dt))))
        for i in range(count):
            mujoco.mj_step(self.model, self.data)
            self._steps += 1
            if frames is not None and renderer is not None and i % stride == 0:
                renderer.update_scene(self.data, camera=camera)
                frames.append(renderer.render().copy())

    def command(self, xyz: np.ndarray | None = None, grip: float | None = None) -> None:
        if xyz is not None:
            self.data.ctrl[:3] = np.asarray(xyz, dtype=float)
        if grip is not None:
            self.data.ctrl[3:] = float(grip)

    def move_to(self, xyz: np.ndarray, duration: float = 0.6, *, frames=None, renderer=None) -> None:
        start = self.data.ctrl[:3].copy()
        target = np.asarray(xyz, dtype=float)
        segments = max(2, int(duration / 0.04))
        for alpha in np.linspace(0.0, 1.0, segments):
            self.command(start * (1 - alpha) + target * alpha)
            self.step_for(duration / segments, frames, renderer)
        self.command(target)
        self.step_for(0.12, frames, renderer)

    def set_grip(self, closed: bool, duration: float = 0.5, *, frames=None, renderer=None) -> None:
        self.command(grip=self.close_grip if closed else self.open_grip)
        self.step_for(duration, frames, renderer)

    def render_frame(self, width: int = 640, height: int = 480) -> np.ndarray:
        renderer = mujoco.Renderer(self.model, height=height, width=width)
        renderer.update_scene(self.data, camera="overview")
        image = renderer.render().copy()
        renderer.close()
        return image

