# Tutorial 10: Simulation Visualization

> **Category:** PhysicsNeMo Integration · **Script:** `10_simulation_visual.py`

## Overview

Extends Tutorial 09 by turning a **static** simulation field into a **time-varying
animated visualization**. Generates transient heat-diffusion data across multiple
timesteps, then writes it to a USD stage as animated color maps, height fields,
and vector fields.

> This tutorial was **verified** to run correctly from its reorganized location —
> output is written to the tutorial's own `output\` folder.

## Prerequisites

- Complete **Tutorials 01–09** first (especially 09).
- Activate the virtual environment:
  ```batch
  cd YOUR_DIRECTORY\omniverse_env
  Scripts\activate
  ```
- `numpy` installed: `pip install numpy`.

## How to Run

```batch
cd YOUR_DIRECTORY\omniverse_env
Scripts\activate
python tutorials\physicsnemo_integration\10_simulation_visual\10_simulation_visual.py
```

## What It Does

1. **Generates Transient Data** — simulates heat diffusion over a 2D grid across
   multiple timesteps (0–9).
2. **Animates a Color Map** — sets `displayColor` time samples so the grid's
   color shifts with temperature at each frame.
3. **Animates a Height Field** — displaces the mesh height per timestep.
4. **Adds a Vector Field** — represents flow direction with arrows/vectors.
5. **Configures the Timeline** — sets start/end time codes and frame rate so the
   animation plays in any USD viewer.

## Key API / Concepts

```python
# Time-sampled color/height for animation
for t in range(10):
    time_code = t * 12 + 1
    instancer.CreateDisplayColorAttr().Set(colors[t], time=time_code)
    mesh.GetHeightAttr().Set(heights[t], time=time_code)

stage.SetStartTimeCode(1)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(24.0)
```

| Concept | Meaning |
|---------|---------|
| **Transient data** | Field values that change over time |
| **Color map** | Mapping scalar values to a color gradient |
| **Vector field** | Arrows representing direction/magnitude at each point |
| **Time sampling** | Storing different attribute values per frame |

## Output

```
tutorials\physicsnemo_integration\10_simulation_visual\output\
└── 10_simulation_visual.usda   # Animated heat-diffusion visualization
```

## Notes

- **Safe to re-run:** Removes an existing `.usda` before creating a new one.
- Open the stage in a USD viewer and scrub the timeline to watch the heat
  diffuse and colors shift across frames.
- The script prints a verification table of grid-point values across timesteps.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Animation static in viewer | Timeline not set, or no time samples written | Confirm `stage.SetStartTimeCode`/`SetEndTimeCode` and per-frame `.Set(..., time=...)` |
| Colors don't vary with heat | Color array not recomputed per timestep | Generate a fresh color array for each `t` from the field |

