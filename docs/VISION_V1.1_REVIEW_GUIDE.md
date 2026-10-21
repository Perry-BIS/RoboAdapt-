# RoboAdapt v1.1.0 independent-review guide

This guide separates verified implementation facts from the interpretation of the
benchmark. It is intended to accompany, not replace, direct source inspection.

## P0: RGB control data flow

The RGB controllers derive their planar control target from a MuJoCo-rendered image:

1. `roboadapt/perception.py:48-96` renders the named `topdown` camera, applies the
   configured image perturbation, thresholds orange pixels, computes their centroid,
   and back-projects the centroid to a known horizontal plane.
2. `roboadapt/control.py:191-220` assigns that returned estimate to `target` for every
   non-oracle controller. `truth_initial` is used only to calculate localization error.
3. `roboadapt/control.py:238-261` repeats the image measurement for re-observe and
   adaptive control. The simulator position read after the measurement is used only
   for the recorded localization error.
4. `roboadapt/control.py:263-268` sends the final `target` into the Cartesian motion
   commands. The oracle branch is explicitly separate at `roboadapt/control.py:188-190`
   and `230-237`.

The sensor must receive the environment object to ask MuJoCo to render a camera image;
it does not read `env.cube_position`. This is source-level separation, not process-level
isolation. Simulator truth remains available in the episode function for metrics and
success evaluation, so reviewers should inspect the cited lines directly.

## P0: pairing

`roboadapt/eval.py:145-209` loops over vision condition, displacement, and seed, calls
the deterministic `sample_task(seed, displacement_m)` once for that scenario, then
runs each configured controller on that same sample. Pair keys are `seed`,
`vision_condition`, and `displacement_m`. `review_artifacts/pairing_map.csv` exposes
all 120 samples and controller outcomes; `pairing_audit.json` checks uniqueness,
three-controller completeness, and recorded target sources.

For RGB open-loop and RGB re-observe, the per-episode image RNG is initialized from
the same seed. Their first perturbed image therefore uses the same random sequence;
re-observe consumes an additional image perturbation draw.

## P1: scope and limitations

The reported 98.3% result is limited to the committed benchmark configuration:

- one orange cube and fixed color thresholds;
- a fixed calibrated top-down camera and known cube-top plane (`z = 0.044 m`);
- fixed scene geometry, lighting, and background;
- Gaussian pixel noise and one synthetic vertical occluder at the configured levels;
- MuJoCo simulation only, with no real-camera or real-robot validation.

It must not be presented as evidence of natural-scene robustness, general object
recognition, cross-camera generalization, or real-robot performance. The v1.0.1 and
v1.1.0 rates also must not be treated as a controlled cross-version comparison.

## Adaptive versus fixed re-observe

Both variants take a second image and incur the same dwell step. Fixed re-observe
always adopts a successful second estimate. Adaptive adopts it only when estimated
shift exceeds 8 mm and confidence is at least 0.35. Therefore the current adaptive
implementation can change the plan-update decision, but it cannot save an observation
or the associated simulation steps. The exploratory pilot produced no success or step
advantage, so adaptive is not part of the 360-episode main claim.

## Review artifacts

- `pairing_map.csv`: scenario geometry and per-controller episode values.
- `pairing_audit.json`: completeness, duplication, source-commit, and target-source audit.
- `stratified_metrics.csv`: success, localization, observation, replanning, failure, and
  physics-step summaries by controller, vision condition, and displacement.
- `VERIFICATION.md`: commands and actual release-candidate verification outputs.
- `SHA256SUMS.txt`: content hashes for high-value evidence and the candidate Wheel.
