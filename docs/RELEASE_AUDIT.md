# RoboAdapt release audit after independent review

**Audit date:** 2026-10-19 (America/Chicago)

**Scope:** local repository and Windows runtime; no remote publication performed

**Reviewed archive SHA-256:** `C4817E36BCB5CB5913A06CCFBBDE13795349DDE82E960E7841F0B7956F33ACAC`

## Decision

The P0/P1 release blockers identified by the independent archive review were
reproduced or checked against the live repository and fixed locally. The historical
320-row dataset is retained byte-for-byte. The current code is suitable as a
release candidate after the tag/version decision in “Unresolved caveats” is made.
No GitHub repository, release, PR, website, competition entry, or remote/shared GPU
operation was created.

## Before / after

| Finding | Before | After | Verification |
|---|---|---|---|
| XML hash | Raw-byte hash changed with CRLF/LF | Canonical newline-normalized SHA-256 prefix; XML forced LF | Unit tests and archive reconstruction |
| Data provenance | CSV says `b4910be`, original local tag at later commit | Confirmed reachable; no experiment-code diff to original tag | `git diff b4910be v1.0.0 -- roboadapt scripts configs` is empty |
| Intervention wording | Could be read as physical motion | Explicit scripted pre-action x/y `qpos` state displacement; not a push | Code docstring, README, method, report |
| Python support | Claimed 3.10–3.12 despite NumPy 2.3.5 | `>=3.11,<3.13`; local verification on 3.12.14 | Wheel metadata/build and local tests |
| Version | Package 0.1.0 vs project v1.0.0 | Package and `__version__` are 1.0.0 | Clean wheel import |
| XML packaging | No explicit package-data declaration | `roboadapt = ["assets/*.xml"]` | Non-editable clean wheel installation |
| Smoke gate | Passed with any success above zero | Requires 10/10 for declared sigma=0, 4 cm condition | Smoke output and unit test |
| Statistics | Aggregate/row-level only | CSV-generated shift strata, clustered bootstrap, exact seed sign flip | `results/final/analysis.json` |
| Wall timing | Report used stale rounded means | 0.0164009 s open; 0.0207873 s adaptive | Recomputed from exact CSV |
| Outcome scope | Placement wording too broad | Notes all 110 failures are grasp misses and outcomes coincide | CSV-generated diagnostics |
| Demo | Adaptive trial only | Matched seed-0 open/adaptive 4 cm comparison | GIF and MP4 inspected locally |

## Provenance checks

Commands:

```powershell
git log --oneline --decorate -n 12
git show --stat b4910be
git diff b4910be v1.0.0 -- roboadapt/ scripts/ configs/
git hash-object results/final/episodes.csv
git rev-parse 4f8d3b7:results/final/episodes.csv
```

Results:

- `b4910be` exists and precedes the original local `v1.0.0` tag.
- The scoped execution-code diff is empty. Later original commits changed final
  CSV timestamps/wall timing/provenance fields, derived summary CSVs, and progress
  documentation; they did not change scene/control/config execution code.
- Current and original-tag historical CSV Git blob IDs are identical:
  `5310622d0e11b8271300d82f09bd235fe32b58d9`.
- Every historical row continues to state source commit `b4910be` and normalized
  scene identifier `498e7b75553ad823`. Provenance was not rewritten.

## Statistical reproduction

Command:

```powershell
.\.venv\Scripts\python.exe scripts\analyze_results.py `
  --input results\final\episodes.csv --output results\final\analysis.json
```

Recomputed results:

- 320 episodes, 160 complete pairs, zero duplicate keys.
- Open loop 83/160 (51.875%); adaptive 127/160 (79.375%); difference +27.5 pp.
- Both success 69; both fail 19; adaptive-only 58; open-only 14.
- Naïve post-hoc row-level exact McNemar p=`1.6464300116e-7`.
- No shift: 62/80 (77.5%) vs 64/80 (80.0%).
- Scripted 4 cm shift: 21/80 (26.25%) vs 63/80 (78.75%).
- Seed-cluster bootstrap (200,000, RNG seed 20261019): [14.375, 40.0] pp.
- Exact exploratory seed-block sign-flip p=`0.0013198853`.
- All 110 failures are `grasp_missed`; grasp/place mismatch count is zero.

The same seeds are reused across eight scenarios. Row-level McNemar independence
is therefore a simplifying post-hoc assumption; the seed-block analyses are also
exploratory and were not preregistered.

## Test and build commands

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe scripts\run_benchmark.py `
  --config configs\smoke.yaml --output results\release_pair_sweep
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist
.\.wheeltest\Scripts\python.exe -m pip install --no-deps `
  .\dist\roboadapt-1.0.0-py3-none-any.whl
```

Final outcomes:

- Pytest: **16 passed** in 1.26 s.
- Strict smoke: **10/10 PASS**, required 10/10, model `498e7b75553ad823`.
- Representative paired sweep (seeds 0–4, sigma 0, scripted shift 4 cm): open
  loop 0/5; adaptive 5/5.
- Dependency check: no broken requirements.
- Non-editable wheel: PASS; version 1.0.0 imported from the clean environment;
  `roboadapt/assets/scene.xml` present, parsed as `mujoco`, and contained no CRLF.
- Wheel SHA-256:
  `FF72CDD084DED9EC252414776991FE020696F735CAE55CFE199F19114F96EBE3`.

The first wheel attempt failed because the managed sandbox's default `%TEMP%` was
not writable. After redirecting `TEMP/TMP` to `.wheeltemp`, build metadata exposed
that the development venv lacked its build dependency. Network installation first
failed under sandbox DNS, then an approved download installed setuptools/wheel.
The final build and clean installation passed. These failed attempts were
environment/tooling issues and are retained here for audit transparency.

## Full benchmark rerun decision

No full 320-episode rerun was performed. Release fixes do not alter MJCF physics,
controller targets/timing, task sampling, perception noise, perturbation magnitude,
or success metrics. They alter the asset identifier implementation, packaging,
analysis, smoke acceptance, documentation, and presentation media. Replacing the
historical CSV would reduce rather than improve provenance. Unit/integration tests,
strict smoke, and the representative paired sweep were rerun locally.

## Archive reconstruction

After committing the release fixes (`138b3a5`), a prefixed Git ZIP archive was
created from `HEAD`, extracted into an isolated directory, and the archived XML
was hashed directly:

```text
raw_hash        498e7b75553ad823
normalized_hash 498e7b75553ad823
contains_crlf   False
bytes           3434
```

This verifies that `.gitattributes` produces an LF asset whose raw and canonical
identifiers match the historical CSV on this Windows host. The first archive
attempt used invalid PowerShell syntax (`--output=(...)`) and failed before any
archive was created; the corrected `git archive ... -o <path> HEAD` command passed.

## Unresolved caveats and release recommendation

- Python 3.12.14 is locally tested. Python 3.11 is declared and dependency-compatible
  but was not independently executed on this machine.
- Git archive LF reconstruction passed locally. No actual Linux/macOS checkout was
  available in this audit; canonical hashing is nevertheless covered by an
  in-memory CRLF/LF invariance test.
- The existing local `v1.0.0` tag identifies the pre-fix audited snapshot. It has
  not been published. Do not silently rewrite it. Before external publication,
  choose either a new `v1.0.1` tag or explicitly approve replacement of the
  unpublished local tag and align package version accordingly.
- The experiment remains a simplified deterministic intervention benchmark, not
  a Panda/IK/RGB-closed-loop/RL/VLA or physical-robot validation.

**Recommendation:** local technical release checks pass. Hold external release
until the user chooses the tag strategy and explicitly authorizes publication.

## v1.0.1 final local verification

**Verification date:** 2026-10-20 (America/Chicago)

**Environment:** Windows, CPython 3.12.14. All commands were run locally; no
repository, tag, release, package, or other artifact was pushed or published.

The version and documentation corrections were committed as
`1bf6e0b7c97adbe26b190e8a72bff7b4a6da0052` before this audit record was
appended. That commit sets both package version sources to 1.0.1, identifies
v1.0.1 as the intended first public release, and describes the experiment as 320
simulated episodes in 160 matched pairs. The historical `v1.0.0` annotated tag
was not moved; its tag object remains `3b72284a5561aa472d356dc930d2925cfb58c28a`
and it dereferences to commit `4f8d3b761082750ac413f74e03226da26b9dc221`.

Commands:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts\smoke_test.py
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts\analyze_results.py `
  --input results\final\episodes.csv `
  --output .wheeltemp\analysis-v1.0.1.json
.\.venv\Scripts\python.exe -m pip wheel . --no-deps `
  --no-build-isolation --wheel-dir .wheeltemp\release-v1.0.1
.\.venv\Scripts\python.exe -m venv .wheeltemp\wheeltest-v101
.\.wheeltemp\wheeltest-v101\Scripts\python.exe -m pip install `
  .\.wheeltemp\release-v1.0.1\roboadapt-1.0.1-py3-none-any.whl
.\.wheeltemp\wheeltest-v101\Scripts\python.exe -m pip check
```

Results:

- Pytest: **16 passed** in 8.24 s.
- Strict smoke: **10/10 PASS**, required 10/10, model
  `498e7b75553ad823`.
- Development and fresh-Wheel environments: `pip check` reported no broken
  requirements.
- Independent temporary analysis: exact JSON-object match to
  `results/final/analysis.json`; the checked-in historical result files were not
  overwritten.
- Fresh non-editable Wheel installation: version and metadata both 1.0.1;
  `roboadapt` imported from the fresh environment's `site-packages`; packaged
  `roboadapt/assets/scene.xml` was present, contained no CRLF, and loaded with
  MuJoCo 3.3.7 (`nq=12`, `nv=11`).
- Wheel: `dist/roboadapt-1.0.1-py3-none-any.whl`, SHA-256
  `5F4BADE4689712AD474DD9BC8DA36E47818AEE05A6CC9F6E4E8E8C4F64A24E31`.
- Historical CSV: 70,329 bytes, SHA-256
  `3BEAF4F468C931D0F93338F59A67C6F380A042A7AD1C1AF92466084F92A57A33`.
- Scene XML: SHA-256
  `498E7B75553AD823C137A630EBD43DBF7B10923AD2EFB4925F45F216B849EE6E`;
  raw prefix remains `498e7b75553ad823`.
- `git diff f9a32a4` was empty for `control.py`, `task.py`, `perception.py`,
  `env.py`, `eval.py`, `assets/scene.xml`, and `configs/benchmark.yaml`; no robot
  physics, controller, task sampling, sensor, success-metric, or benchmark-config
  code changed in the v1.0.1 bookkeeping commit.

The fresh environment's first dependency installation attempt could not reach the
package index under sandboxed DNS. A permitted retry downloaded only the declared
runtime dependencies and completed successfully. This was a local environment
setup issue, not a code or package failure. The 320-episode benchmark was not
rerun and its historical CSV remains byte-for-byte unchanged.

## v1.1.0 independent-review fixes

**Review-fix date:** 2026-10-20 (America/Chicago)

The independent review verified the 360-row main CSV but found three publication
evidence issues. The following corrections preserve the original v1.0.1 and v1.1
experiment CSV bytes.

### Experiment-source traceability

The main v1.1 CSV records source commit `0ce598e`; the first review archive used
HEAD `d9e0a4471dadbe364bbac8d43917e632b28ea4f9`. The requested local comparison was:

```text
git diff 0ce598e..d9e0a44 -- roboadapt scripts configs
```

Its only changed path was the newly added
`scripts/build_vision_review_artifacts.py`. A separate
`git diff --quiet 0ce598e..d9e0a44 -- roboadapt configs` returned exit code 0.
Therefore no runtime package module, controller, perception implementation,
environment, task sampler, or experiment configuration changed between the
recorded experiment commit and the first review HEAD. The added script reads the
committed CSV and produces reviewer-facing tables; it cannot affect those episodes.

### Wheel-build identity

The hash `828809FBBFEA8D92C2387E56CDA7624D301A1FFC5C409AA2F004CF344DDFDB0D`
belongs to a superseded pre-review `1.1.0.dev0` build. The Wheel actually included
in the independently reviewed ZIP hashes to
`78915C5F7EB9CC794E4BC0EC69B52C985BAE6B26746E3D574182EB0FC3909BBB`.
Neither is the final `1.1.0` artifact. The final Wheel and archive hashes are
recorded in the final verification subsection below.

### Adaptive pilot evidence

The original ignored pilot output was recovered without altering its bytes and
preserved under `results/vision_adaptive_pilot/`, together with the exact config,
metadata, generated audit summary, and a dedicated analysis script. The 120 rows
contain 60 matched scenarios: fixed re-observe and adaptive each succeed 58/60,
with 58 both-success and 2 both-failure outcomes, no discordant outcomes, and
identical step counts within all both-success pairs.

The rows record base commit `2cada2c`. The vision implementation was uncommitted
when this earlier pilot ran, so Git cannot reconstruct its exact dirty source
snapshot. The result is retained transparently as exploratory evidence only, is
not included in the 360-episode main claim, and does not support adaptive superiority.

### Physics-step interpretation

The all-trial means are 2,259.89 steps for RGB open loop and 2,876.86 for RGB
re-observe (+27.3%). Many open-loop failures terminate before transport and
placement, so this is not pure computation or perception overhead. In the 67
matched scenarios where both methods succeed, re-observe adds exactly 50 steps
(`0.10 s` simulated time) in every pair.

### Final v1.1.0 verification

The release-evidence and version changes were first committed as `6c6a4a2`.
The Wheel was built with Python 3.12.14 and a fixed `SOURCE_DATE_EPOCH`, installed
non-editably with all pinned dependencies into a newly created virtual environment,
and validated from the repository's parent directory.

Actual verification results:

```text
Pytest: 22 passed in 1.58s
Strict smoke: 10/10 PASS; required=10/10; model=498e7b75553ad823
Development pip check: No broken requirements found.
Fresh-Wheel pip check: No broken requirements found.
WHEEL_IMPORT_MODEL_LOAD=PASS
version=1.1.0
model_hash=498e7b75553ad823
nq=12 nv=11
```

The fresh import path was inside
`.wheeltemp/wheeltest-v1.1.0-final/Lib/site-packages/roboadapt`, not the source
checkout. Both packaged `vision_analysis.py` and `assets/scene.xml` were present;
the scene loaded successfully in MuJoCo 3.3.7.

Final local candidate Wheel:

```text
roboadapt-1.1.0-py3-none-any.whl
SHA-256 2DB076906C991EAE374311ECBC023D5CE1803A432611CB0D97BE1D5DEDC81E9B
```

Historical evidence remained unchanged:

```text
results/final/episodes.csv
SHA-256 3BEAF4F468C931D0F93338F59A67C6F380A042A7AD1C1AF92466084F92A57A33

results/vision_v1.1/episodes.csv (Windows working-copy bytes)
SHA-256 F9A593AE042EA2852B50533B78783945566F1C601BAC751FA3433151B95E4135

roboadapt/assets/scene.xml
SHA-256 498E7B75553AD823C137A630EBD43DBF7B10923AD2EFB4925F45F216B849EE6E
```

No v1.1.0 tag was created because the user has not separately confirmed local tag
creation. No branch, tag, Wheel, archive, or GitHub Release was pushed or published.

## v1.1.0 final publication preparation

**Final preparation date:** 2026-10-22 (America/Chicago)

The final independent audit found one remaining manifest discrepancy. The reviewed
ZIP stored `results/vision_adaptive_pilot/config.yaml` with CRLF bytes and SHA-256
`2E653179D30D8D4623D2570299F12EEBA26AC9988A8EA0785A8EA61528E66571`;
the earlier manifest recorded the LF working-copy hash `D49A62...`. The YAML text
and settings were identical. Final manifests now use one explicit policy: SHA-256
is computed over the exact raw bytes in the staged publication package, after Git
archive extraction and before final compression. No source/config file is rewritten
to force a preferred newline style.

A dedicated `docs/RELEASE_NOTES_V1.1.0.md` was added. The v1.0.1 draft remains as
an explicitly archived historical file. The README quick start now selects Python
3.12, matching the locally accepted environment while retaining declared Python
3.11–3.12 support.

Real local Git history was checked directly. From experiment commit `0ce598e` to
release candidate `804816e`, `control.py`, `perception.py`, `eval.py`, `env.py`,
`task.py`, `vision_analysis.py`, and `configs/vision_benchmark.yaml` have no diff.
Within `roboadapt/`, the only change is `__init__.py` version metadata from
`1.1.0.dev0` to `1.1.0`; the other scoped additions are post-experiment analysis
and review scripts. Thus the release controller, vision path, environment, task
sampling, and benchmark configuration remain equivalent to the recorded experiment.

Final local acceptance on the release-notes commit `12908f4` produced:

```text
EXPERIMENT_RUNTIME_CONFIG_EQUIVALENCE=PASS
Pytest: 22 passed in 7.49s
Strict smoke: 10/10 PASS; required=10/10; model=498e7b75553ad823
Development pip check: No broken requirements found.
Fresh-Wheel pip check: No broken requirements found.
WHEEL_IMPORT_MODEL_LOAD=PASS
version=1.1.0
model_hash=498e7b75553ad823
nq=12 nv=11
```

The final Wheel was installed non-editably with declared dependencies into a newly
created Python 3.12 environment and imported from `site-packages` while the command
ran outside the repository. Packaged `vision_analysis.py` and `assets/scene.xml`
were present and the MuJoCo model loaded successfully.

```text
roboadapt-1.1.0-py3-none-any.whl
SHA-256 3C33FEB85812EC162B6EFED02D649843EF1930CEB4E5361C25148C19DDED9824
```

The Wheel differs from the preceding `2DB076...` candidate because the README,
which is embedded in Wheel metadata, was updated for the final Python 3.12 quick
start and release wording. Runtime package modules are otherwise unchanged.
