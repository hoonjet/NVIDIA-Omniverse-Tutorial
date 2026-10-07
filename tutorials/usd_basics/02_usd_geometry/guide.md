# Tutorial 02: USD Geometry

> **Category:** USD Basics · **Script:** `02_usd_geometry.py`

## Overview

Builds on Tutorial 01 by creating multiple geometry types and applying
**transformations** (translate, rotate, scale) using the `UsdGeom.Xformable`
interface. Demonstrates the correct order of transform operations.

## Prerequisites

- Complete **Tutorial 01: USD Basics** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_basics\02_usd_geometry\02_usd_geometry.py
```

## What It Does

1. **Creates 6 Geometry Types** — cube, sphere, cylinder, cone, capsule, plane.
2. **Applies Transformations** — translate, rotate, and scale on each shape.
3. **Demonstrates Transform Order** — shows why operation order matters.
4. **Arranges Shapes in a Grid** — each shape placed at a distinct location.

## Key API Calls

```python
from pxr import UsdGeom, Gf

# Wrap the prim with Xformable to enable transforms
xformable = UsdGeom.Xformable(prim)

# Add operations IN ORDER (order matters!)
xformable.AddTranslateOp().Set(Gf.Vec3d(1.0, 0.0, 0.0))
xformable.AddRotateYOp().Set(45.0)
xformable.AddScaleOp().Set(Gf.Vec3f(2.0, 2.0, 2.0))
```

## Key Concepts

- **Xformable** — the interface that lets a prim carry transform operations.
- **Transform Order** — USD applies ops in the order they are added
  (translate → rotate → scale is the common convention).
- **Gf.Vec3d / Gf.Vec3f** — USD's vector types for double/float precision.

## Output

```
tutorials\usd_basics\02_usd_geometry\output\
└── 02_usd_geometry.usda   # 6 geometry types with transforms
```

## Notes

- **Re-running:** Uses `Usd.Stage.CreateNew()` — delete the existing
  `.usda` before re-running:
  ```batch
  del tutorials\usd_basics\02_usd_geometry\output\02_usd_geometry.usda
  ```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Transform not applied | Did not wrap prim with `UsdGeom.Xformable` | Use `xformable = UsdGeom.Xformable(prim)` then add ops |
| Wrong visual result | Transform ops added in wrong order | Add translate → rotate → scale in sequence |

## Next Steps

Continue to **Tutorial 03: USD Materials**.
