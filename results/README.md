# Results

Generated benchmark directories contain `episodes.csv`, `metadata.json`, and plots.
Every chart must be regenerated from an episode CSV; no result is hard-coded.

- `final/` is the immutable v1.0.1 truth-plus-noise benchmark.
- `rgb/` is the earlier standalone RGB localization evaluation.
- `vision_v1.1/` is the independent 360-episode rendered-RGB closed-loop
  benchmark. It does not overwrite or merge with `final/`.

