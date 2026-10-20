# Experiments

The benchmark config pairs both controllers across the same 20 seeds, four pose
noise levels (0, 1, 2, 4 cm), and two post-observation displacement levels (0 and
4 cm), for 320 episodes. The smoke config runs 10 paired episodes. The 4 cm
displacement is the upper bound proposed in the master plan; a preliminary 10-seed
probe was used to select it before the formal matrix, and is not a formal result.

The final run completed all 320 episodes on Windows 11 using Python 3.12.14,
MuJoCo 3.3.7, and NumPy 2.3.5. The scene hash was `498e7b75553ad823`.
No school/remote GPU was used; headless physics ran locally on CPU.

| sigma (m) | displacement (m) | open-loop | re-observe/re-plan |
|---:|---:|---:|---:|
| 0.00 | 0.00 | 20/20 (100%) | 20/20 (100%) |
| 0.00 | 0.04 | 1/20 (5%) | 20/20 (100%) |
| 0.01 | 0.00 | 20/20 (100%) | 20/20 (100%) |
| 0.01 | 0.04 | 7/20 (35%) | 19/20 (95%) |
| 0.02 | 0.00 | 16/20 (80%) | 17/20 (85%) |
| 0.02 | 0.04 | 8/20 (40%) | 17/20 (85%) |
| 0.04 | 0.00 | 6/20 (30%) | 7/20 (35%) |
| 0.04 | 0.04 | 5/20 (25%) | 7/20 (35%) |

Aggregate success was 83/160 for open loop and 127/160 for re-observe/re-plan.
Among 160 paired conditions, both failed 19 times, only open loop succeeded 14
times, only adaptive succeeded 58 times, and both succeeded 69 times. An exact
two-sided McNemar test on discordant pairs gives p=1.65e-7. This post-hoc test is
reported as descriptive evidence, not as a preregistered confirmatory analysis.

Stratifying by scripted displacement shows the mechanism of the result. With no
shift, open loop was 62/80 (77.5%) and adaptive was 64/80 (80.0%). With a 4 cm
pre-action state shift, they were 21/80 (26.25%) and 63/80 (78.75%). Because the
same 20 seeds are reused across eight scenario conditions, the row-level McNemar
calculation does not represent 160 independent seed clusters. A deterministic,
exploratory 200,000-resample seed-cluster bootstrap gives a rate-difference 95%
percentile interval of [14.375, 40.0] percentage points; an exact seed-block
sign-flip calculation gives p=0.0013199. Both are post-hoc sensitivity analyses.

All 110 failures are `grasp_missed`, and grasp/place success columns coincide for
all 320 rows. This matrix mainly tests initial target acquisition and does not
isolate placement robustness under goal or transport disturbances.

The optional RGB sensor was separately evaluated on 20 seeded object poses:
mean error 0.411 mm, median 0.407 mm, maximum 0.754 mm in the simple calibrated
scene. These numbers do not measure occlusion or domain robustness.

See `results/final/metadata.json`, `episodes.csv`, and `plots/summary.csv` for
runtime versions, all records, Wilson intervals, and condition-level values.
`scripts/analyze_results.py` regenerates `results/final/analysis.json` from the
exact CSV, including the paired and seed-block calculations.

