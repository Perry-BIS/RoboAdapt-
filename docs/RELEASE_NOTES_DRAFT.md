# RoboAdapt v1.0.0 — release notes draft (not published)

Initial reproducible release of the simulation-only RoboAdapt benchmark.

## Included

- Original MuJoCo Cartesian gripper scene with contact-based pickup and placement.
- Paired open-loop and bounded re-observation/re-plan controllers.
- 320-episode uncertainty benchmark, raw CSV/metadata, Wilson confidence intervals,
  condition plots, and post-hoc paired analysis.
- Optional calibrated RGB centroid/localization demo evaluated on 20 seeded poses.
- Windows setup, 11 automated tests, GIF/MP4 demo, technical report, and limitations.

## Main measured result

Aggregate placement success was 51.9% for open loop and 79.4% for adaptive control
under the checked-in matrix. The adaptive strategy added 25.3% physics steps and
remained unreliable at 4 cm pose noise. These are MuJoCo simulation results, not
physical-robot measurements.

This file is a draft. No GitHub release or external publication has been created.
