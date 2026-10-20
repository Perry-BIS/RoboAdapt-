# One-minute demo script

**0–10 s:** “RoboAdapt tests a simple question: if an object moves after a grasp is
planned, can one re-observation reduce failure? This is a MuJoCo-only project.”

**10–25 s:** Show the GIF. “The cube is a free rigid body. The gripper closes through
contact, lifts it, moves to the green target, and releases—there is no weld or pose
teleport during the grasp.”

**25–40 s:** Show `success_rate.png`. “I ran 320 simulated episodes organized into
160 matched pairs over 20 seeds, four pose-noise levels, and two displacement
levels. Open loop placed 83 of 160; bounded re-observation placed 127 of 160. The
gain is strongest when the target moves.”

**40–50 s:** Point to the 4 cm-noise panels. “Feedback is not magic: at severe pose
noise both methods fall to 25–35%, which the report treats as a real limitation.”

**50–60 s:** Show the RGB detection image. “A separate calibrated color-centroid
sensor localizes the cube in this clean scene. Code, 16 tests, raw CSV, plots, model
hash, and demo media make every claim reproducible.”
