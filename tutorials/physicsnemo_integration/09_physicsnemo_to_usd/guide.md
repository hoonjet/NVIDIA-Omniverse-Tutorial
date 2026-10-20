# Tutorial 09: PhysicsNeMo to USD

> **Category:** PhysicsNeMo Integration · **Script:** `09_physicsnemo_to_usd.py`

## Overview

Bridges **NVIDIA PhysicsNeMo** (formerly Modulus) simulation data with USD.
Generates synthetic Darcy-flow field data, then converts it into a USD scene
with colored point clouds and a height field — the foundation for visualizing
physics simulation results in Omniverse.

## Prerequisites

- Complete the **USD Basics** and **Kit API** tutorial sets (01–08) first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```
- `numpy` installed (auto-detects PhysicsNeMo; falls back to synthetic data if
  PhysicsNeMo is unavailable):
  ```batch
  pip install numpy
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\physicsnemo_integration\09_physicsnemo_to_usd\09_physicsnemo_to_usd.py
```

## What It Does

1. **Generates Simulation Data** — creates a synthetic Darcy-flow pressure field
   on a 2D grid and saves it to `physicsnemo_data\darcy_flow.json`.
2. **Converts Data to USD** — maps each grid point to a colored point cloud
   prim, with color encoding pressure magnitude.
3. **Creates a Height Field** — builds a mesh whose height follows the field
   magnitude for a 3D view of the data.
4. **Exports for Visualization** — writes a USD stage ready to view in Omniverse.

## Key API / Concepts

```python
import numpy as np
from pxr import Usd, UsdGeom, Vt

# Map field values -> per-point colors
colors = Vt.Vec3fArray([color_for(v) for v in field_values])
points = Vt.Vec3fArray([...])              # grid positions
instancer = UsdGeom.Points.Define(stage, "/World/DarcyField")
instancer.CreatePointsAttr().Set(points)
instancer.CreateDisplayColorAttr().Set(colors)
```

| Concept | Meaning |
|---------|---------|
| **PhysicsNeMo** | NVIDIA's physics-ML training framework |
| **Darcy flow** | Pressure-driven flow through porous media |
| **Point cloud** | Set of points with per-point color/size attributes |
| **Height field** | A mesh displaced vertically by a scalar field |

## Output

```
tutorials\physicsnemo_integration\09_physicsnemo_to_usd\output\
├── 09_physicsnemo_to_usd.usda     # USD stage with colored points + height field
└── physicsnemo_data\
    └── darcy_flow.json            # Synthetic Darcy-flow field data (input/export)
```

## Notes

- **No PhysicsNeMo required:** The script auto-detects whether PhysicsNeMo is
  available and falls back to a synthetic generator — so it runs anywhere.
- **Safe to re-run:** Removes an existing `.usda` before creating a new one.
- The JSON data file can be inspected or regenerated independently.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: No module named 'numpy'` | numpy not installed | `pip install numpy` |
| Points render all one color | Color array length ≠ point count | Ensure one color per point |
| `RuntimeError: PhysicsNeMo not found` | (informational only) | The script falls back automatically; no action needed |

## Next Steps

Continue to **Tutorial 10: Simulation Visualization**.
