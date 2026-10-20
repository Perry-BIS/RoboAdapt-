import numpy as np
from roboadapt.task import sample_task


def test_task_seed_reproducibility():
    a = sample_task(12, 0.03)
    b = sample_task(12, 0.03)
    assert np.array_equal(a.object_xy, b.object_xy)
    assert np.array_equal(a.displacement_xy, b.displacement_xy)
    assert np.isclose(np.linalg.norm(a.displacement_xy), 0.03)

