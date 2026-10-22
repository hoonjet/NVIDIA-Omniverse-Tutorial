# Tutorial 11: Digital Twin

> **Category:** PhysicsNeMo Integration · **Script:** `11_digital_twin.py`

## Overview

The capstone tutorial — combines geometry, simulation, and visualization into a
complete **digital twin** pipeline. Builds a 3D asset, attaches physics-simulation
data, animates it over time, and writes a human-readable summary report.

## Prerequisites

- Complete **all prior tutorials (01–10)** — this one combines their concepts.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```
- `numpy` installed: `pip install numpy`.

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\physicsnemo_integration\11_digital_twin\11_digital_twin.py
```

## What It Does

1. **Builds a 3D Asset** — creates geometry for the digital twin (e.g. a machine
   or device represented with prims, materials, and transforms).
2. **Attaches Simulation Data** — binds physics-simulation results (temperature,
   pressure, velocity) as time-sampled attributes on the geometry.
3. **Animates Over Time** — writes per-frame values so the twin reflects the
   simulation evolving.
4. **Generates a Report** — writes `digital_twin_report.txt` summarizing the
   twin's contents, simulation parameters, and key metrics.

## Key API / Concepts

```python
# Geometry + simulation data combined
asset_prim = UsdGeom.Mesh.Define(stage, "/World/DigitalTwin/Device")
asset_prim.CreatePointsAttr().Set(...)
asset_prim.CreateFaceVertexIndicesAttr().Set(...)

# Time-sampled simulation attributes
device.CreateAttribute("sim:temperature", Sdf.ValueTypeNames.Float).Set(85.0, time=1)
device.CreateAttribute("sim:temperature", Sdf.ValueTypeNames.Float).Set(92.0, time=24)

# Write a human-readable report
with open(report_path, "w") as f:
    f.write("Digital Twin Report\n")
    f.write(f"Simulation timesteps: {n_steps}\n")
    f.write(f"Peak temperature: {peak} C\n")
```

| Concept | Meaning |
|---------|---------|
| **Digital Twin** | A virtual replica of a physical asset with live data |
| **Time-sampled attributes** | Per-frame values reflecting simulation state |
| **Report** | A human-readable summary of the twin |

## Output

```
tutorials\physicsnemo_integration\11_digital_twin\output\
├── 11_digital_twin.usda        # The complete digital twin scene
└── digital_twin_report.txt     # Human-readable summary report
```

Open the report:
```batch
notepad tutorials\physicsnemo_integration\11_digital_twin\output\digital_twin_report.txt
```

## Notes

- **Self-contained:** The script generates all geometry and simulation data
  internally — no external inputs required.
- **Safe to re-run:** Removes existing `.usda` (and overwrites the report)
  before recreating.
- This is the final tutorial. Together with 09 and 10 it forms a complete
  PhysicsNeMo → USD → Omniverse visualization workflow.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Report file missing | Script exited before writing | Check stdout for the error; ensure `output_dir` was created |
| Twin shows no animation | Time-sampled attributes not bound to geometry prims | Attach `sim:*` attributes to the device prim, with `time=` values |

## Full Tutorial Path Complete

Congratulations — you've finished all 11 tutorials across USD Basics, Kit API,
and PhysicsNeMo Integration. See the root `README.md` for the full index.
