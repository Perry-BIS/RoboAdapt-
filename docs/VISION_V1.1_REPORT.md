# RoboAdapt v1.1 vision-in-the-loop development report

**Status:** local v1.1.0 release candidate; not released

**Run date:** 2026-10-20 (America/Chicago)

## Research question

Does a second rendered-RGB observation before grasp execution recover from a
stale visual target more reliably than planning from one RGB image?

This study is separate from the published v1.0.1 truth-plus-noise benchmark. It
does not modify `results/final/` or the v1.0.1 tag and Release.

## Control inputs

- `oracle_state`: simulator cube x/y is used as an explicit upper reference.
- `rgb_open_loop`: one top-camera RGB image is segmented; the orange-pixel
  centroid is back-projected to a known horizontal cube-top plane. The resulting
  x/y estimate is the only object position used by the controller.
- `rgb_reobserve`: the same initial image pipeline is used, followed by a second
  image after the scripted displacement and before robot motion. The grasp target
  is replanned from that image.

The RGB controllers never use simulator object position to choose a target. Truth
is read only after image estimation to log localization error and evaluate lift,
placement, and endpoint error. Re-observation occurs while the gripper remains at
its camera-clear staging pose; an early prototype that observed from directly
above the target failed because the gripper occluded the cube.

## Experimental design

The checked-in `configs/vision_benchmark.yaml` specifies:

- 20 shared seeds;
- three controllers;
- no displacement or a scripted 4 cm pre-action free-body `qpos` displacement;
- clean RGB, Gaussian channel noise (standard deviation 12 intensity levels), or
  the same noise plus a seeded vertical occluder covering 10% of image width.

The 20 base seeds are reused across three visual conditions and two displacement
levels. This gives 360 episodes and 120 complete RGB open/re-observe pairs, but
only 20 independent random geometry seeds. The occluder
position and image noise are deterministic for a seed. The 4 cm intervention is
not a physical push. Conditions were selected during development, so inferential
statistics are exploratory.

## Results

| Controller | Successes | Rate | Mean physics steps |
|---|---:|---:|---:|
| Oracle state | 120/120 | 100.0% | 2,923.5 |
| RGB open loop | 67/120 | 55.8% | 2,259.9 |
| RGB re-observe | 118/120 | 98.3% | 2,876.9 |

RGB re-observation improved paired success by **42.5 percentage points**. Paired
outcomes were 67 both successful, 2 both failed, 51 re-observe-only successes,
and 0 open-loop-only successes. The post-hoc exact McNemar value is approximately
`8.88e-16`. Resampling whole seed blocks gives an exploratory 95% percentile
interval of **+35.0 to +49.2 percentage points**; the exploratory exact seed-block
sign-flip value is `7.63e-6`.

Mean final RGB localization error over valid RGB observations was 0.94 mm; the
median was 0.48 mm. Across all trials, re-observation used 27.3% more mean episode
physics steps than RGB open loop because successful trials proceed through transport
and placement while many open-loop displaced trials terminate after a missed grasp.
This is not a measurement of pure computation or RGB-inference cost. In the 67
strictly matched pairs where both controllers succeeded, re-observation added
exactly 50 physics steps (`dt=0.002 s`, or `0.10 s` simulated time) in every pair.
Wall time also includes rendering and segmentation and is platform-dependent.

At zero displacement, RGB open loop and re-observation were both 100% in clean and
noise-only conditions. At 4 cm displacement, open-loop success was 10% clean and
15% under each noisy condition, while re-observation was 100% clean/noise-only and
95% with noise plus occlusion. Two paired occlusion cases failed because the
initial detector found too few orange pixels.

## Adaptive pilot

An optional `rgb_adaptive` rule replans only when the second image has sufficient
confidence and its target shift exceeds 8 mm. The original 120-episode, 10-seed
pilot CSV, metadata, config, and audit summary are preserved in
`results/vision_adaptive_pilot/`. It matched fixed RGB re-observation exactly at
58/60 successes with the same mean physics steps and no discordant paired outcomes.
This experiment does not support an adaptive-policy improvement. Its rows record
base commit `2cada2c`: the vision implementation was in an uncommitted working tree
when the pilot ran, so its exact source snapshot cannot be reconstructed from Git.
The pilot is therefore explicitly exploratory and is not part of the 360-episode
main claim.

## Reproduction

```powershell
.\.venv\Scripts\python.exe scripts\run_vision_benchmark.py `
  --config configs\vision_benchmark.yaml --output results\vision_v1.1
.\.venv\Scripts\python.exe scripts\analyze_vision_results.py `
  --input results\vision_v1.1\episodes.csv `
  --output results\vision_v1.1\analysis.json
.\.venv\Scripts\python.exe scripts\plot_vision_results.py `
  --input results\vision_v1.1\episodes.csv `
  --output results\vision_v1.1\plots
```

Every row records source commit `0ce598e`. The Windows working copy uses CRLF
line endings (94,614 bytes), SHA-256
`F9A593AE042EA2852B50533B78783945566F1C601BAC751FA3433151B95E4135`.
The Git blob uses LF line endings (94,253 bytes), SHA-256
`2DAFBCA0ED763F37BD27B57899E96D483076B96A815E5A013370B94B08357A84`.
The rows and values are identical; only newline encoding differs.

## Limitations

This remains a simple simulation with a 3-DOF Cartesian gantry, one orange cube,
known camera intrinsics/extrinsics, known object-top height, fixed lighting, and
no physical robot. The Oracle ceiling is 100%, showing the task geometry is easy
when state is known. The detector is classical color segmentation rather than a
learned or generalizable perception model. Synthetic channel noise and a vertical
occluder are controlled stress tests, not substitutes for real camera variation.

## Local candidate verification

- Python 3.12.14: **22 tests passed**.
- Historical strict smoke: **10/10 PASS**.
- Development environment: `pip check` reported no broken requirements.
- Independent analysis rerun: exact JSON-object match.
- The independent-review ZIP contained the later `1.1.0.dev0` candidate Wheel with
  SHA-256 `78915C5F7EB9CC794E4BC0EC69B52C985BAE6B26746E3D574182EB0FC3909BBB`.
  The earlier `828809F...` value belonged to a superseded pre-review build and is
  not the reviewed or release artifact.
- Final non-editable Wheel install: version `1.1.0`, with `vision_analysis.py` and
  `scene.xml` present and model loading verified.
- Final local release-candidate Wheel SHA-256:
  `2DB076906C991EAE374311ECBC023D5CE1803A432611CB0D97BE1D5DEDC81E9B`.
- The v1.0.1 historical CSV remains unchanged with SHA-256
  `3BEAF4F468C931D0F93338F59A67C6F380A042A7AD1C1AF92466084F92A57A33`.

No v1.1 branch, tag, package, or Release has been pushed or published.
