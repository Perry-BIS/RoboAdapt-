# Resume material for the v1.1 development candidate

Use only after independently checking the v1.1 branch and deciding whether to
publish it. Do not imply physical-robot or real-camera validation.

**RoboAdapt — RGB Re-Observation for Robotic Manipulation | Python, MuJoCo**

- Developed a simulated top-view RGB manipulation pipeline integrating calibrated
  color-centroid localization and a second pre-grasp observation/replanning step in
  a contact-based MuJoCo 3-DOF Cartesian-gripper simulation.
- Evaluated Oracle state, RGB open-loop, and RGB re-observation control across 360
  simulated episodes (120 paired RGB scenarios); RGB re-observation improved
  placement success from 55.8% to 98.3% under the tested displacement and image
  perturbation matrix.
- Quantified localization error, image observations, seeded occlusion failures, and
  exploratory seed-block uncertainty; prepared auditable CSV, analysis code, plots,
  tests, and matched-control demonstration media for public release.

The 55.8% and 98.3% figures are v1.1 development results, not the published
v1.0.1 truth-plus-noise benchmark. Keep the versions distinct.

Do not replace “prepared” with “published” until the v1.1.0 Release is publicly
accessible. Do not describe this as continuous visual servoing, physical-robot
validation, natural-scene generalization, inverse kinematics, RL, or VLA work.
