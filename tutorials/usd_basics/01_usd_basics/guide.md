# Tutorial 01: USD Basics

> **Category:** USD Basics · **Script:** `01_usd_basics.py`

## Overview

This is the entry point to USD (Universal Scene Description). It introduces the
three foundational building blocks of every USD scene — the **Stage**, **Prims**,
and **Attributes** — by creating a small scene with a cube, sphere, cylinder,
and camera, then reading the data back from disk.

## Prerequisites

- Activate the virtual environment first:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```
- `usd-core` installed (USD 26.3). Verify with:
  ```batch
  python -c "from pxr import Usd; print(Usd.GetVersion())"
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_basics\01_usd_basics\01_usd_basics.py
```

## What It Does

1. **Creates a USD Stage** — the root container for the scene.
2. **Creates Prims** — Cube, Sphere, Cylinder, and Camera objects.
3. **Sets Attributes** — size, radius, height, color, focal length.
4. **Demonstrates Attribute Operations** — read, modify, and list attributes.
5. **Saves and Reloads** — persists to disk and verifies the data round-trips.

## Key API Calls

```python
from pxr import Usd, UsdGeom

# Create a new stage
stage = Usd.Stage.CreateNew(filepath)

# Create a cube prim
cube = UsdGeom.Cube.Define(stage, "/World/Cube1")

# Set an attribute
cube.GetAttr("size").Set(2.0)

# Save to disk
stage.GetRootLayer().Save()
```

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **Stage** | The root container for a USD scene (like a "scene file") |
| **Prim** | A single object in the scene (cube, sphere, camera, etc.) |
| **Attribute** | A property of a prim (size, color, position, etc.) |
| **Schema** | A predefined type that defines what attributes a prim can have |

## Output

```
tutorials\usd_basics\01_usd_basics\output\
└── 01_usd_basics.usda   # Stage with cube, sphere, cylinder, camera
```

`.usda` files are ASCII text — open them in any text editor:
```batch
notepad tutorials\usd_basics\01_usd_basics\output\01_usd_basics.usda
```

## Notes

- **Re-running:** This script uses `Usd.Stage.CreateNew()`, which fails if the
  output file already exists. Delete the existing `.usda` before re-running:
  ```batch
  del tutorials\usd_basics\01_usd_basics\output\01_usd_basics.usda
  ```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ModuleNotFoundError: No module named 'pxr'` | Venv not active, or `usd-core` not installed | `Scripts\activate` then `pip install usd-core` |
| `FileExistsError` | Output `.usda` already exists | Delete the file (see Notes) before re-running |
| Prim not found after creating | Prim path doesn't start with `/` | Use `"/World/Cube1"`, not `"World/Cube1"` |

## Next Steps

Continue to **Tutorial 02: USD Geometry**.
