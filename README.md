# RoboAdapt

**Robust pick-and-place control with a simulated 3-DOF Cartesian gantry gripper.**
This is a MuJoCo-only research project. It has not been tested on a physical robot, and
its Level-0 perception input is simulator pose plus controlled synthetic noise—not
an RGB vision system.

The benchmark compares a one-observation `open_loop` policy with a bounded
`reobserve_replan` policy under paired seeds and post-observation object motion.
The original minimal robot is a 3-DOF Cartesian stage with two actuated fingers.
The 4 cm intervention directly changes the free cube's x/y state after observation
and before action to create a stale target; it is not a physical push. During
grasp and transport, the cube moves only through simulated contact.

## Windows quick start

Python 3.11–3.12 is declared; the release audit was executed locally on Python
3.12.14. In PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install .
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe -m pytest -q
```

If `py` is unavailable, create the environment with an explicit Python 3.11–3.12
executable. CUDA and a discrete GPU are not required for physics evaluation.

## Demo and evaluation

```powershell
.\.venv\Scripts\python.exe scripts\run_demo.py --seed 0 --controller open_loop
.\.venv\Scripts\python.exe scripts\run_demo.py --seed 0 --controller reobserve_replan --record
.\.venv\Scripts\python.exe scripts\run_benchmark.py --config configs\smoke.yaml --output results\smoke
.\.venv\Scripts\python.exe scripts\run_benchmark.py --config configs\benchmark.yaml --output results\final
.\.venv\Scripts\python.exe scripts\plot_results.py --input results\final\episodes.csv --output results\final\plots
.\.venv\Scripts\python.exe scripts\analyze_results.py --input results\final\episodes.csv --output results\final\analysis.json
.\.venv\Scripts\python.exe scripts\compare_demo.py --seed 0 --displacement 0.04
.\.venv\Scripts\python.exe scripts\rgb_sensor_demo.py --seed 0 --output media\rgb_detection.png
.\.venv\Scripts\python.exe scripts\evaluate_rgb_sensor.py --seeds 20 --output results\rgb\observations.csv
```

`run_demo.py --record` uses the real MuJoCo renderer and writes a GIF. Headless
physics tests and benchmarks do not create an OpenGL context.

The optional RGB demo uses a fixed calibrated top camera, orange-color centroid,
and known-plane back-projection. It is classical geometric vision, not a learned
detector; the formal controller benchmark remains Level 0 (truth plus noise).
It is not RGB-in-the-loop, inverse kinematics, reinforcement learning, VLA, or a
Panda-arm experiment.

## Evidence and scope

- Success means the free cube is lifted above a threshold, transported, released,
  and settled inside the goal. No weld/equality constraint or success-only bypass
  attaches it to the gripper.
- Each CSV row records condition, seed, controller, observation/replan counts,
  grasp/place outcomes, timing, error, failure reason, commit, and scene hash.
- `model_hash` is the first 16 hexadecimal characters of SHA-256 after normalizing
  text newlines to LF. `.gitattributes` also forces LF for XML assets, so Windows
  and Unix archives reconstruct the recorded `498e7b75553ad823` identifier.
- Figures are generated only from CSV data. See `docs/METHOD.md`,
  `docs/EXPERIMENTS.md`, and `docs/LIMITATIONS.md`.

License: MIT for project code/assets. MuJoCo is an Apache-2.0 dependency; see
`NOTICE.md`.

## Reproduced results

The checked-in final run contains 320 physics episodes (20 seeds × 4 noise
levels × 2 displacement levels × 2 controllers), all using scene hash
`498e7b75553ad823`. Aggregate place success was 83/160 (51.9%, Wilson 95% CI
44.2–59.5%) for open loop and 127/160 (79.4%, 72.5–84.9%) for re-observe/re-plan.
Without scripted displacement, results were 62/80 (77.5%) versus 64/80 (80.0%);
with 4 cm displacement they were 21/80 (26.25%) versus 63/80 (78.75%). The main
aggregate gain therefore reflects stale-target recovery. At 4 cm sensing noise,
condition rates were only 25–35%. Feedback corrected target
motion well, but it did not remove severe measurement noise.

![Success by condition](results/final/plots/success_rate.png)

The adaptive controller used about 25.3% more physics steps (2,794 vs 2,231 per
episode on average). See `results/final/episodes.csv`, `metadata.json`, and the
complete report for condition-level data and limitations.

![Matched 4 cm scripted displacement: open loop versus re-observe/re-plan](media/matched_displacement_comparison.gif)

The panels use the same seed and scripted 4 cm pre-action state displacement. The
left open-loop trial misses the grasp; the right re-observation trial succeeds.
