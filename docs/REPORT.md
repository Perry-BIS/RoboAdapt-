# RoboAdapt: Robust Manipulation under Pose Uncertainty in MuJoCo

## Abstract

Robotic manipulation policies can fail when an object moves after planning or a
pose estimate is inaccurate. This work builds a fully local MuJoCo benchmark to
test one narrow question: does one bounded re-observation and re-planning step
improve contact-based pick and place over an otherwise matched open-loop policy?
The benchmark uses an original Cartesian manipulator, a free rigid cube, seeded
Gaussian pose error, and paired post-observation displacements. Across 320 real
simulation episodes, open loop completed 83/160 placements (51.9%, Wilson 95% CI
44.2–59.5%) and re-observe/re-plan completed 127/160 (79.4%, 72.5–84.9%). The
advantage was concentrated in displaced-object conditions; at 4 cm pose noise,
both policies remained unreliable. The adaptive policy required 25.3% more
physics steps. All episode records, plots, tests, model hash, and demo media are
included. Results are simulation-only and make no real-robot claim.

## 1. Introduction

A one-shot manipulation controller assumes that its target remains valid between
perception and contact. That assumption breaks under latency, accidental target
motion, or pose-estimation error. A practical alternative is to observe again near
the pre-grasp state and update only when the discrepancy is meaningful. The
intervention is small enough to audit: both controllers can share the same scene,
seeds, motion limits, and success criteria, with observation policy as the sole
intended difference.

RoboAdapt therefore emphasizes reproducibility over robot-model complexity. It
does not train a policy, use a vision-language-action model, or claim transfer to
hardware. The formal experiment uses simulator truth plus controlled noise. An
optional classical RGB centroid module is evaluated separately so that camera
evidence is not conflated with the controller comparison.

## 2. Environment and control

The original MJCF scene contains a three-axis Cartesian stage, two opposing
position-controlled fingers, a 42 mm cube with a free joint, a planar table, and a
marked circular goal. Finger-cube contact, friction, gravity, and release are
resolved by MuJoCo. There is no weld constraint, object attachment shortcut, or
pose rewrite during pickup and transport. An external post-planning displacement
is applied before action as the controlled disturbance for both policies.

At reset, the object is uniformly sampled within a reachable 18×18 cm region.
Both policies receive the same seeded first observation. `open_loop` uses it for
the full grasp. `reobserve_replan` moves to a high pre-grasp waypoint, samples a
second noisy observation, and changes its target at most once if the discrepancy
exceeds 8 mm. A cooldown is unnecessary because only one re-plan is allowed.
Both then descend, close the fingers, lift, move to the goal, lower, release, and
withdraw with identical motion timing.

A grasp is counted only when the free cube is above 75 mm after lift. Placement
requires a successful grasp, release within 50 mm of the goal center, and settled
height no greater than 55 mm. Failures in this experiment were all classified as
`grasp_missed`; the controller never received placement credit merely for a
rendered overlap.

## 3. Experimental design

The matrix crosses 20 seeds, pose noise sigma in {0, 0.01, 0.02, 0.04} m,
post-observation displacement in {0, 0.04} m, and two controllers, totaling 320
episodes. Paired rows share seed, initial pose, displacement direction and length,
and initial noisy observation. Each record stores controller, condition, outcomes,
steps, simulated and wall time, observation/re-plan counts, endpoint error,
failure reason, software revision field, and the SHA-256-derived scene hash.

The checked-in run used Windows 11, Python 3.12.14, MuJoCo 3.3.7, and scene hash
`498e7b75553ad823`. Physics ran locally on CPU; no lab server or school GPU was
accessed. Wilson intervals quantify binomial uncertainty. An exact McNemar test is
reported for the aggregate paired outcomes, but it is post-hoc and the 4 cm
disturbance was chosen after a development probe.

## 4. Results

| Pose noise | Displacement | Open loop | Re-observe/re-plan |
|---:|---:|---:|---:|
| 0 cm | 0 cm | 100% | 100% |
| 0 cm | 4 cm | 5% | 100% |
| 1 cm | 0 cm | 100% | 100% |
| 1 cm | 4 cm | 35% | 95% |
| 2 cm | 0 cm | 80% | 85% |
| 2 cm | 4 cm | 40% | 85% |
| 4 cm | 0 cm | 30% | 35% |
| 4 cm | 4 cm | 25% | 35% |

Aggregate success increased by 27.5 percentage points, from 51.9% to 79.4%.
Among 160 paired cases, adaptive-only success occurred 58 times and open-loop-only
success occurred 14 times; 69 pairs both succeeded and 19 both failed. The exact
two-sided McNemar p-value is 1.65×10^-7. This supports a difference in this fixed
simulation matrix, not a universal robotics performance claim.

The condition breakdown is more informative than the aggregate. With exact poses
and no displacement, both policies were perfect. With a 4 cm displacement and no
pose noise, adaptive control was 20/20 while open loop was 1/20. At 2 cm noise,
adaptive control reached 17/20 in both displacement conditions. At 4 cm noise,
however, its rate fell to 7/20, only modestly above open loop. A second noisy
sample corrects stale target position but does not guarantee an accurate target.

The adaptive policy averaged 2,794 physics steps and 5.588 simulated seconds per
episode versus 2,231 steps and 4.461 seconds for open loop—25.3% more in both
measures. Mean measured headless wall time was 0.0212 versus 0.0169 seconds on the
development machine, but such small absolute timings are sensitive to OS load and
should not be treated as hardware-independent latency.

The optional fixed-camera RGB module was evaluated on 20 poses outside the formal
matrix. Its simple color centroid and known-plane back-projection produced 0.411
mm mean, 0.407 mm median, and 0.754 mm maximum error in this clean rendered scene.
These values demonstrate calibration consistency only; they do not establish
robust visual perception under clutter, lighting shifts, or occlusion.

## 5. Limitations and conclusion

The robot is a minimal Cartesian mechanism, the object is a single cube, dynamics
and contact parameters are simulation-specific, and the sample size is 20 per
condition. The displacement magnitude was selected after exploratory testing, so
formal intervals do not cover that selection. Severe sensing noise remained a
dominant failure mode. The RGB evaluation uses known color and plane geometry and
is not part of the policy comparison.

Within these limits, the experiment answers its scoped question: a single bounded
re-observation step substantially reduced failures caused by a stale target in
this paired MuJoCo benchmark, at the cost of about one quarter more trajectory
steps. It did not solve large independent measurement error. Future work should
pre-register conditions, test occlusion-aware RGB-D estimation, add varied object
geometry, and validate the controller on an articulated arm before any physical-
robot conclusion.

## Reproduction artifacts

- Raw data: `results/final/episodes.csv`
- Environment metadata: `results/final/metadata.json`
- Generated summaries and figures: `results/final/plots/`
- RGB observations: `results/rgb/observations.csv`
- Contact-physics demo: `media/demo_reobserve_replan_seed0.gif` and `.mp4`
- Tests: `python -m pytest -q` (11 passed in the final local run)
