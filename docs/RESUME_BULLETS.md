# Resume and statement material

## Evidence-backed resume bullets

**RoboAdapt — Robust Manipulation under Pose Uncertainty | Python, MuJoCo**

- Built a reproducible MuJoCo contact-manipulation benchmark with randomized
  target poses, controlled sensing noise, post-planning disturbances, auditable
  success checks, and an optional calibrated RGB centroid sensor.
- Implemented paired open-loop and bounded re-observation controllers; completed
  320 seeded simulation trials and measured 51.9% versus 79.4% aggregate placement
  success (Wilson 95% CIs 44.2–59.5% and 72.5–84.9%).
- Produced Windows-ready scripts, 11 automated tests, raw CSV/metadata, four
  generated analysis figures, and a contact-physics GIF/MP4 demo; documented a
  25.3% step overhead and failure under severe pose noise.

Do not change “simulation” to “robot” or “vision-guided controller”: no physical
robot was tested, and the formal policy benchmark used truth plus synthetic noise.

## Personal-statement paragraph

I built RoboAdapt to turn a broad interest in robust manipulation into a falsifiable
simulation study. Rather than optimizing a polished demo, I implemented matched
open-loop and re-observation controllers, defined contact-based grasp and placement
criteria, and kept every episode in an auditable CSV. Across 320 paired MuJoCo
trials, the feedback strategy raised aggregate placement success from 51.9% to
79.4% under the chosen uncertainty matrix, while requiring 25.3% more simulation
steps; importantly, both approaches still degraded sharply at 4 cm pose noise.
This project taught me to treat negative regimes, experimental controls, and
reproducibility artifacts as central engineering results rather than footnotes.
