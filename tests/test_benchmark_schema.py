from pathlib import Path
from roboadapt.eval import SCHEMA, load_config, smoke_accepts, wilson_interval


def test_smoke_config_and_schema():
    config = load_config(Path("configs/smoke.yaml"))
    assert set(config["controllers"]) == {"open_loop", "reobserve_replan"}
    assert len(SCHEMA) == len(set(SCHEMA))


def test_wilson_interval_contains_observed_rate():
    lo, hi = wilson_interval(7, 10)
    assert lo < 0.7 < hi


def test_smoke_requires_declared_minimum():
    assert smoke_accepts(10, total=10, minimum=10)
    assert not smoke_accepts(1, total=10, minimum=10)

