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
