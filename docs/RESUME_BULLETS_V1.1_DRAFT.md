# Resume material for the v1.1 development candidate

Use only after independently checking the v1.1 branch and deciding whether to
publish it. Do not imply physical-robot or real-camera validation.

**RoboAdapt — Vision-in-the-Loop Manipulation in MuJoCo | Python, MuJoCo**

- Developed a rendered-RGB robotic manipulation pipeline integrating calibrated
  color-centroid localization, feedback control, and online grasp replanning in a
  contact-based MuJoCo Cartesian-gripper simulation.
- Evaluated Oracle state, RGB open-loop, and RGB re-observation control across 360
  simulated episodes (120 paired RGB scenarios); RGB re-observation improved
  placement success from 55.8% to 98.3% under the tested displacement and image
  perturbation matrix.
- Quantified localization error, image observations, physics-step overhead, seeded
  occlusion failures, and exploratory seed-block uncertainty; released auditable
  CSV, analysis code, plots, tests, and matched-control demonstration media.

The 55.8% and 98.3% figures are v1.1 development results, not the published
v1.0.1 truth-plus-noise benchmark. Keep the versions distinct.
