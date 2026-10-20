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
is applied before action as the controlled disturbance for both policies. The
intervention directly increments the cube free joint's x/y `qpos`, zeros its free-
body velocity, and settles for 0.15 simulated seconds. It is a scripted state
displacement that creates a stale target, not a collision-generated physical push.

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

The asset identifier normalizes CRLF and CR newlines to LF before hashing and
stores the first 16 SHA-256 hexadecimal characters. This produces the historical
`498e7b75553ad823` value for semantically identical Windows and Unix XML files;
`.gitattributes` additionally forces LF for packaged XML assets. The raw-byte hash
is available separately for archive diagnostics.

The checked-in run used Windows 11, Python 3.12.14, MuJoCo 3.3.7, and scene hash
`498e7b75553ad823`. Physics ran locally on CPU; no lab server or school GPU was
accessed. Wilson intervals quantify binomial uncertainty. An exact McNemar test is
reported for the aggregate paired outcomes, but it is post-hoc and the 4 cm
disturbance was chosen after a development probe.

The same 20 seeds are reused across all eight noise/displacement scenarios. Thus,
the 160 scenario pairs are not 160 independent seed clusters. We additionally
report exploratory seed-block sensitivity analyses generated by
`scripts/analyze_results.py`: a deterministic 200,000-resample clustered bootstrap
and an exact sign-flip distribution over the 20 aggregate per-seed scores.

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
simulation matrix, not a universal robotics performance claim. It is a naïve
post-hoc row-level calculation because it treats repeated scenario rows as
independent. The seed-cluster bootstrap gives a 95% percentile interval of +14.375
to +40.0 percentage points, and the exact exploratory seed-block sign-flip test
gives p=0.0013199. These analyses were not preregistered.

The condition breakdown is more informative than the aggregate. With exact poses
and no displacement, both policies were perfect. With a 4 cm displacement and no
pose noise, adaptive control was 20/20 while open loop was 1/20. At 2 cm noise,
adaptive control reached 17/20 in both displacement conditions. At 4 cm noise,
however, its rate fell to 7/20, only modestly above open loop. A second noisy
sample corrects stale target position but does not guarantee an accurate target.

When aggregated by intervention, the no-displacement results were 62/80 (77.5%)
for open loop and 64/80 (80.0%) for adaptive control, only a 2.5-point difference.
Under the scripted 4 cm shift, the corresponding rates were 21/80 (26.25%) and
63/80 (78.75%), a 52.5-point difference. The overall result is therefore driven
primarily by recovery from the prescribed stale target rather than by a general
solution to independent measurement noise.

The adaptive policy averaged 2,794 physics steps and 5.588 simulated seconds per
episode versus 2,231 steps and 4.461 seconds for open loop—25.3% more in both
measures. Mean measured headless wall time was 0.020787 versus 0.016401 seconds on the
development machine, but such small absolute timings are sensitive to OS load and
should not be treated as hardware-independent latency.

The optional fixed-camera RGB module was evaluated on 20 poses outside the formal
matrix. Its simple color centroid and known-plane back-projection produced 0.411
mm mean, 0.407 mm median, and 0.754 mm maximum error in this clean rendered scene.
These values demonstrate calibration consistency only; they do not establish
robust visual perception under clutter, lighting shifts, or occlusion.

All 110 unsuccessful episodes are labeled `grasp_missed`; no stored episode has a
different grasp and placement outcome. The experiment therefore demonstrates a
combined pick-and-place check dominated by initial grasp targeting. It does not
independently demonstrate robust placement under varied goals or transport-time
disturbances.

## 5. Limitations and conclusion

The robot is a minimal Cartesian mechanism, the object is a single cube, dynamics
and contact parameters are simulation-specific, and the sample size is 20 per
condition. The displacement magnitude was selected after exploratory testing, so
formal intervals do not cover that selection. Severe sensing noise remained a
dominant failure mode. The RGB evaluation uses known color and plane geometry and
is not part of the policy comparison.

Provenance inspection confirmed that the recorded experiment commit `b4910be` is
reachable. The diff from that commit to the original local `v1.0.0` tag contained
only historical CSV/metadata, derived summary CSVs, and progress documentation;
there were no changes under `roboadapt/`, `scripts/`, or `configs/`. The release-
fix work changes packaging, canonical hash calculation, analysis, acceptance
tests, documentation, and demo presentation, but does not alter scene physics,
controller motion, task sampling, or the historical CSV.

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
- Recomputed paired/cluster analysis: `results/final/analysis.json`
- RGB observations: `results/rgb/observations.csv`
- Matched comparison: `media/matched_displacement_comparison.gif` and `.mp4`
- Release verification commands and outcomes: `docs/RELEASE_AUDIT.md`
