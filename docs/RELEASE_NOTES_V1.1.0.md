# RoboAdapt v1.1.0

RoboAdapt v1.1.0 adds a simulated RGB-in-the-loop manipulation benchmark focused
on recovery from stale target estimates. A fixed top-view MuJoCo camera supplies
rendered RGB images; classical orange-color segmentation, centroid extraction, and
calibrated ray/plane back-projection produce the planar grasp target. The feedback
controller makes a second observation and replans before grasp execution.

This is discrete pre-grasp re-observation, not continuous visual servoing.

## Main benchmark

- 360 MuJoCo episodes.
- 120 complete three-controller matched scenarios.
- 20 base geometry seeds reused across three image conditions and two displacement
  levels; 120 scenarios do not represent 120 independent geometry seeds.
- Oracle state: 120/120 successful placements (100%).
- RGB open loop: 67/120 (55.8%).
- RGB re-observe: 118/120 (98.3%).
- Paired improvement: +42.5 percentage points.
- Exploratory seed-cluster bootstrap interval: +35.0 to +49.2 percentage points.

The improvement is primarily stale-target recovery. Without scripted displacement,
both RGB methods achieved 59/60. After a scripted 4 cm pre-action `qpos` displacement,
RGB open loop achieved 8/60 and RGB re-observe achieved 59/60. The intervention is
a deterministic simulator-state change, not an external physical push.

## Episode-step tradeoff

Across all trials, RGB re-observe used 27.3% more mean episode physics steps than
RGB open loop (2,876.86 versus 2,259.89). This is not pure image-processing cost:
many failed open-loop episodes stop before transport and placement. In the 67
matched scenarios where both controllers succeeded, re-observation added exactly
50 physics steps, or 0.10 seconds of simulated time, per pair.

## Exploratory adaptive pilot

The preserved 120-row pilot contains 60 matched fixed-reobserve/adaptive scenarios.
Both methods achieved 58/60, with identical success outcomes and episode-step counts.
The adaptive rule changed `replan_count` in some pairs but showed no demonstrated
success or step advantage. Its rows were produced from an uncommitted development
worktree, so the exact source snapshot cannot be reconstructed from Git. The pilot
is retained as transparent exploratory evidence and is not part of the 360-episode
main claim.

## Reproducibility and compatibility

- Package version: `1.1.0`.
- Supported Python: 3.11–3.12; release acceptance was run on Python 3.12.14.
- MuJoCo: 3.3.7.
- Automated tests: 22/22 passed locally.
- Strict historical smoke: 10/10 passed locally.
- Main and adaptive analyses reproduce their checked-in JSON objects.
- Wheel installs non-editably in a clean Python 3.12 environment and includes
  `vision_analysis.py` and `assets/scene.xml`.

The historical v1.0.1 experiments and Release remain unchanged.

## Scope and limitations

This is a simulation-only 3-DOF Cartesian gantry experiment with one orange cube,
a fixed calibrated top camera, known object-top plane, fixed scene/lighting, and
specified synthetic pixel noise and occlusion. It does not validate a physical
robot, real camera, natural-scene recognition, unknown-camera robustness, continuous
visual servoing, inverse kinematics for a multi-joint arm, reinforcement learning,
VLA models, or real-world transfer.

## Release artifacts

Attach the verified `roboadapt-1.1.0-py3-none-any.whl` and publish the tag only after
the local release manifest has been checked against the exact raw bytes being
uploaded. SHA-256 values are artifact-specific and are recorded in the accompanying
release manifest.
