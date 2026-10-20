# Limitations

- This is simulation-only; no physical robot has been tested.
- The required Level-0 pose observation is simulator truth plus synthetic noise,
  not learned or camera-based vision. The optional RGB module is evaluated
  separately and is not connected to the formal controller benchmark.
- The robot is a deliberately minimal Cartesian manipulator, not a Panda or other
  anthropomorphic arm, so conclusions concern feedback logic rather than arm IK.
- MuJoCo contact parameters and the simple cube geometry limit transferability.
- Statistical claims must be updated only after running the checked-in benchmark.
- The 4 cm displacement was selected after a small development probe because 3 cm
  remained inside the gripper's capture tolerance; formal confidence intervals do
  not account for that exploratory selection.
- Only 20 seeds were used per condition. Wilson intervals are consequently broad,
  especially near the extremes, and the aggregate rate weights all conditions
  equally rather than representing a deployment distribution.
- The same 20 seeds are reused across eight scenario conditions. The aggregate
  row-level McNemar p-value is post-hoc and treats those scenario pairs as
  independent; the seed-block bootstrap and sign-flip analysis are exploratory.
- All 110 failures in the stored benchmark are `grasp_missed`, and `success_grasp`
  equals `success_place` in every row. The data therefore do not separately
  establish robust goal placement under varied goal or transport disturbances.

