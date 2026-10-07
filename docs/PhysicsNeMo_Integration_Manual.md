# PhysicsNeMo Integration Tutorial Set - Manual

> **Location:** `E:\omniverse_env\tutorials\`
> **Prerequisites:** Complete Tutorial Sets 1 (USD Basics) and 2 (Kit API) first
> **Dependency:** `numpy` (installed in the virtual environment)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tutorial 09: PhysicsNeMo to USD](#2-tutorial-09-physicsnemo-to-usd)
3. [Tutorial 10: Simulation Visualization](#3-tutorial-10-simulation-visualization)
4. [Tutorial 11: Digital Twin Pipeline](#4-tutorial-11-digital-twin-pipeline)
5. [Integration with Real PhysicsNeMo](#5-integration-with-real-physicsnemo)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Overview

This tutorial set bridges the user's existing **PhysicsNeMo** knowledge (built in `E:\physicsnemo_env`) with **Omniverse USD**. It demonstrates how to convert PhysicsNeMo simulation results into 3D USD scenes for visualization.

### What You Will Learn

| Tutorial | Topic | Key Skills |
|----------|-------|------------|
| 09 | PhysicsNeMo to USD | Scalar field → point cloud, height field, colormap |
| 10 | Simulation Visualization | Animated color maps, height fields, vector fields |
| 11 | Digital Twin Pipeline | End-to-end: geometry → simulation → visualization |

### The Complete Pipeline

```
PhysicsNeMo Model (E:\physicsnemo_env)
        │
        ▼
Simulation Output (numpy arrays)
        │
        ▼
USD Conversion (this tutorial set)
        │
        ▼
3D Visualization (USD scene)
        │
        ▼
Omniverse (with RTX GPU)
```

---

## 2. Tutorial 09: PhysicsNeMo to USD

**File:** `09_physicsnemo_to_usd.py`
**Output:** `tutorials/output/09_physicsnemo_to_usd.usda` + `tutorials/output/physicsnemo_data/darcy_flow.json`

### What It Does

1. **Generates Synthetic Darcy Flow Data** - Mimics PhysicsNeMo model output:
   - 2D pressure field (15×15 grid)
   - 2D velocity field (vx, vy)
   - Computed from analytical solution of Darcy's equation

2. **Creates Colored Point Cloud** - Each grid point becomes a colored sphere:
   - Color mapped via jet colormap (blue=cold → red=hot)
   - Scalar value stored as custom attribute

3. **Creates 3D Height Field** - Each grid point becomes a cylinder:
   - Height proportional to scalar value
   - Color mapped via jet colormap

4. **Stores Simulation Metadata** - Parameters saved as USD attributes

5. **Exports Data as JSON** - For use with external tools

### Key API: Scalar Field to USD

```python
# For each grid point, create a colored sphere
sphere = UsdGeom.Sphere.Define(stage, f"/World/Field/P_{i}_{j}")
sphere.GetRadiusAttr().Set(0.15)
sphere.GetDisplayColorAttr().Set([scalar_to_color(value, vmin, vmax)])
UsdGeom.Xformable(sphere).AddTranslateOp().Set(Gf.Vec3d(x, y, z))
sphere.GetPrim().CreateAttribute("data:pressure", Sdf.ValueTypeNames.Float).Set(float(value))
```

### Colormap

The jet colormap maps scalar values to colors:

```
Value:   min ───────► 25% ───────► 50% ───────► 75% ───────► max
Color:   Blue ──────► Cyan ──────► Green ─────► Yellow ────► Red
```

---

## 3. Tutorial 10: Simulation Visualization

**File:** `10_simulation_visual.py`
**Output:** `tutorials/output/10_simulation_visual.usda`

### What It Does

1. **Generates Transient Data** - Time-varying heat diffusion simulation:
   - 10×10 grid, 10 timesteps
   - Hot spot in center that diffuses and cools over time
   - Circular velocity field around the hot spot

2. **Creates Animated Color Map** - Spheres change color over time:
   - Each sphere has color time samples at each timestep
   - Timeline: frames 1 to 109 at 24 FPS

3. **Creates Animated Height Field** - Cylinders change height and color:
   - Height, color, and Y-position all animated
   - Shows temperature evolution as a 3D surface

4. **Creates Velocity Vector Field** - Arrows showing flow direction:
   - Thin cylinders oriented along velocity direction
   - Colored by velocity magnitude

5. **Verifies Animation** - Reads back animated values at specific frames

### Key API: Animated Color Map

```python
# Set color at each timestep (time sample)
for t in range(num_timesteps):
    frame = start_frame + t * fps
    color = scalar_to_color(temperature[t, i, j], vmin, vmax)
    color_attr.Set([color], frame)  # Time sample
```

### Key API: Animated Height Field

```python
# Animate height, color, AND position simultaneously
for t in range(num_timesteps):
    frame = start_frame + t * fps
    height_attr.Set(height, frame)           # Animate height
    color_attr.Set([color], frame)            # Animate color
    translate_op.Set(Gf.Vec3d(x, h/2, z), frame)  # Animate position
```

---

## 4. Tutorial 11: Digital Twin Pipeline

**File:** `11_digital_twin.py`
**Output:** `tutorials/output/11_digital_twin.usda` + `tutorials/output/digital_twin_report.txt`

### What It Does

This is the **capstone tutorial** that combines all previous concepts into a complete digital twin pipeline:

1. **Creates Physical Geometry** - Heat exchanger with:
   - Cylindrical shell (outer container)
   - Inlet pipe (cold fluid, blue)
   - Outlet pipe (hot fluid, red)
   - 3×3 tube bundle (brass-colored)

2. **Runs Heat Transfer Simulation** - 20 timesteps:
   - Cold fluid enters at 20°C
   - Hot fluid exits at up to 80°C
   - Temperature gradient along shell height
   - Exponential approach to steady state

3. **Animates with Simulation Results**:
   - 10 sensor spheres along shell height (color changes with temperature)
   - 9 tube cylinders (color changes with temperature)
   - Timeline: frames 1 to 115

4. **Stores Digital Twin Metadata** - System info, model info, parameters

5. **Generates Summary Report** - Text file with temperature profile over time

### Digital Twin Pipeline

```
Step 1: Create USD Stage
   │
Step 2: Create Heat Exchanger Geometry (shell, pipes, tubes)
   │
Step 3: Run Heat Transfer Simulation (20 timesteps)
   │
Step 4: Animate Geometry with Simulation Results
   │      - 10 sensors: color animated by temperature
   │      - 9 tubes: color animated by temperature
   │
Step 5: Store Digital Twin Metadata
   │
Step 6: Generate Summary Report
```

### Key Concept: Digital Twin

A digital twin is a virtual model that mirrors a physical system. In this tutorial:

| Physical System | Digital Twin (USD) |
|----------------|-------------------|
| Heat exchanger | Cylinders + pipes in USD |
| Temperature sensors | Colored spheres (animated) |
| Temperature readings | Time-sampled color attributes |
| System parameters | USD metadata attributes |
| Operating data | Simulation results (numpy arrays) |

---

## 5. Integration with Real PhysicsNeMo

To use real PhysicsNeMo model output instead of synthetic data:

### Step 1: Run PhysicsNeMo Inference

```python
# In E:\physicsnemo_env (activate that environment first)
# Run your trained model to get predictions
import torch
from physicsnemo.models import FNO

# Load trained model
model = FNO(...)
model.load_state_dict(torch.load("model.pth"))
model.eval()

# Run inference
with torch.no_grad():
    predictions = model(input_data)
    # predictions is a numpy/tensor array of shape (nx, ny)
```

### Step 2: Convert to USD

```python
# In E:\omniverse_env (activate this environment)
# Import the conversion functions from Tutorial 09
import sys
sys.path.insert(0, "E:/omniverse_env/tutorials")
from tutorial_09_physicsnemo_to_usd import scalar_field_to_usd_points, scalar_to_color

# Convert PhysicsNeMo output to USD
data = {
    "x": x_coords,        # From PhysicsNeMo
    "y": y_coords,        # From PhysicsNeMo
    "pressure": predictions,  # From PhysicsNeMo model
}

scalar_field_to_usd_points(data, stage, field_name="pressure")
```

### Step 3: Cross-Environment Data Exchange

Since `physicsnemo_env` (Python 3.10) and `omniverse_env` (Python 3.8) are separate environments, exchange data via files:

```
E:\physicsnemo_env\          (Python 3.10, PyTorch, PhysicsNeMo)
    │
    │  Save model output as .npy or .json
    ▼
E:\omniverse_env\            (Python 3.8, USD)
    │
    │  Load .npy/.json and convert to USD
    ▼
E:\omniverse_env\tutorials\output\*.usda
```

```python
# In physicsnemo_env: Save model output
import numpy as np
np.save("E:/omniverse_env/tutorials/output/physicsnemo_data/predictions.npy", predictions)

# In omniverse_env: Load and convert
import numpy as np
predictions = np.load("E:/omniverse_env/tutorials/output/physicsnemo_data/predictions.npy")
```

---

## 6. Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'numpy'`

**Solution:**
```batch
cd E:\omniverse_env
Scripts\activate
pip install numpy
```

### Problem: Animation not playing in USD viewer

**Cause:** The timeline must be set on the stage, and the viewer must support time-sampled attributes.

**Solution:**
```python
# Ensure timeline is set
stage.SetStartTimeCode(1)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(24.0)
```

### Problem: Too many prims (performance)

**Cause:** Creating individual sphere prims for large grids is slow.

**Solution:** For large datasets, use `UsdGeom.Points` instead of individual spheres:
```python
# Instead of many spheres, use a single Points prim
points = UsdGeom.Points.Define(stage, "/World/PointCloud")
points.GetPointsAttr().Set(positions)  # Array of positions
points.GetWidthsAttr().Set(widths)     # Array of point sizes
# Note: Per-point colors require primvars
```

---

## Summary

This tutorial set demonstrates the complete pipeline from PhysicsNeMo simulation to USD visualization:

1. **Tutorial 09**: Static conversion of simulation data to USD
2. **Tutorial 10**: Animated visualization of transient simulations
3. **Tutorial 11**: Complete digital twin pipeline with geometry + simulation + animation

The key insight is that **USD serves as the bridge** between physics simulation (PhysicsNeMo) and 3D visualization (Omniverse). By converting numpy arrays to USD prims with time-sampled attributes, any simulation result can be visualized in 3D.
