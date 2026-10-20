# Method

RoboAdapt uses an original MuJoCo scene: a position-controlled Cartesian X/Y/Z
stage with two independently actuated opposing fingers. The cube is a free rigid
body. Grasping and transport rely on MuJoCo contact and friction; the code never
welds the cube to the gripper or rewrites cube pose to claim success.

The Level-0 sensor returns simulator truth plus seeded Gaussian x/y noise. It is
not an RGB vision model. `open_loop` observes once before an optional displacement.
`reobserve_replan` makes the same first observation, observes again before descent,
and changes its target at most once when the difference exceeds 8 mm.

The displacement is a controlled, scripted state intervention: after the first
observation and before action, `env.displace_cube()` directly increments the free
joint's x/y `qpos`, clears free-body velocity, calls forward dynamics, and allows
0.15 simulated seconds to settle. It is not a collision-generated push. No cube
state is rewritten during grasping, lifting, transport, release, or evaluation.

The robot is a simulated 3-axis Cartesian gantry gripper. The benchmark does not
contain an articulated Panda arm, inverse kinematics, RGB-in-the-loop control,
reinforcement learning, or a vision-language-action model.

Paired comparisons share the initial object pose, displacement, seed, motion
limits, task logic, and success checks. A grasp succeeds only if the free cube is
lifted above 75 mm. Placement additionally requires release within 50 mm of the
goal center at a settled height no greater than 55 mm.

## Optional Level-1 RGB observation

A fixed 320×320 top camera renders the scene. A deterministic orange channel-
difference mask yields the cube centroid; a calibrated pinhole ray intersects the
known 44 mm cube-top plane to recover x/y. This is classical color segmentation
with a known plane, not learned perception. It is evaluated independently and is
not used by the formal controller benchmark, so the two evidence levels remain
separate.

