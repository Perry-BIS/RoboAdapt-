# RoboAdapt v1.0.1 — release notes draft (not published)

Intended first public release of the simulation-only RoboAdapt benchmark. The
local `v1.0.0` tag identifies an unpublished research snapshot; it remains intact
for provenance, while v1.0.1 carries the repaired asset hashing, packaging, tests,
analysis, and documentation intended for release.

## Included

- Original MuJoCo Cartesian gripper scene with contact-based pickup and placement.
- Paired open-loop and bounded re-observation/re-plan controllers.
- 320 simulated episodes organized into 160 matched pairs, raw CSV/metadata,
  Wilson confidence intervals, condition plots, and post-hoc paired analysis.
- Optional calibrated RGB centroid/localization demo evaluated on 20 seeded poses.
- Windows setup, 16 automated tests, GIF/MP4 demo, technical report, and limitations.
- Cross-platform normalized scene hashing, explicit wheel package data, strict
  10/10 smoke acceptance, deterministic paired/seed-block analysis, and a matched
  open-loop/adaptive comparison video.

## Main measured result

Aggregate placement success was 51.9% for open loop and 79.4% for adaptive control
under the checked-in matrix. The adaptive strategy added 25.3% physics steps and
remained unreliable at 4 cm pose noise. These are MuJoCo simulation results, not
physical-robot measurements.

Without scripted displacement the controllers scored 77.5% and 80.0%; under the
4 cm pre-action state displacement they scored 26.25% and 78.75%. The intervention
directly changes free-body state before action and is not a physical push. The
formal benchmark uses truth plus Gaussian noise rather than RGB-in-the-loop.

This file and the official release remain drafts pending explicit approval. No
GitHub release or external publication has been created.
