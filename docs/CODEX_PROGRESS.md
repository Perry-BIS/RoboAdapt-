# Codex progress log

## 2026-10-19 — P0/P1/P2 implementation and validation

### Platform and boundaries

- Read the full master plan. No external publication, lab server, Kaggle, or school
  GPU was used. Host GPU detected: NVIDIA RTX 4060 Laptop, 8188 MiB, driver 560.94.
- System `python` was 3.8.10; created `.venv` from available Python 3.12.14 and
  installed the pinned Windows dependencies. `pip check` reports no broken packages.
- RAM query through CIM/systeminfo was blocked by host policy; no RAM figure is
  claimed. Core physics is CPU-only and does not require CUDA.

### Implemented

- Original MuJoCo Cartesian X/Y/Z stage and physical two-finger gripper; free cube,
  table, goal, overview/wrist/top cameras; project scene hash `498e7b75553ad823`.
- Seeded Level-0 truth-plus-Gaussian-noise sensor, identical paired disturbances,
  open-loop controller, bounded re-observation/re-plan controller, physical lift
  and stable placement checks, and explicit failure reasons.
- Benchmark, plotting, demo recording, video export, Level-1 RGB detector/evaluator,
  configs, packaging, CLI help, license/notice, README, report, limitations,
  resume/PS material, release notes draft, and demo script.

### Errors found and repaired

- MuJoCo initially rejected zero-inertia moving slide bodies; added explicit
  inertials and re-ran load/tests.
- The bundled Python venv initially lacked pip; ran its own `ensurepip` then kept
  all dependencies isolated in `.venv`.
- First top-camera orientation rendered black; corrected camera axes. First orange
  threshold failed under renderer lighting; calibrated channel-difference masking
  from actual pixels. Parked the gripper outside the randomized object region to
  prevent top-view occlusion, then invalidated and re-ran all formal results.
- Initial success plot labels overlapped; replaced it with four noise-level facets
  and added the required timing/step-cost plot.

### Actual commands and outcomes

- `.venv\Scripts\python.exe -m pytest -q` → **11 passed** (0.91 s final check).
- `.venv\Scripts\python.exe scripts\smoke_test.py` → **10/10** adaptive placement
  successes with 4 cm target displacement.
- Formal benchmark → **320/320 episodes completed**. Open loop: 83/160 (51.9%);
  re-observe/re-plan: 127/160 (79.4%). Exact paired McNemar p=1.65e-7. Every
  final CSV row records source snapshot `b4910be` and scene hash `498e7b75553ad823`.
- Plot regeneration → `success_rate.png`, `endpoint_error.png`,
  `failure_categories.png`, `timing_steps.png`, plus summary CSVs.
- Real renderer capture → 246-frame GIF (941,820 bytes) and MP4 (264,688 bytes).
- RGB evaluation → 20/20 detections; mean error 0.411 mm, max 0.754 mm in the
  simple calibrated scene. This is separate from the Level-0 formal benchmark.

### Current status and remaining authorization boundary

- P0 complete: installable project, contact grasp/place, tests, raw data, figures,
  report, and demo media.
- P1 complete: fair paired controller comparison with real logs and statistics.
- P2 lightweight scope complete: classical RGB centroid observation and evaluation.
- Repository is locally Git-ready. External GitHub creation/push, release, PR,
  website publication, or third-party compute use remains intentionally unperformed
  until the user explicitly authorizes it.
