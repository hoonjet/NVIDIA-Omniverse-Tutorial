# Tutorial 03: USD Materials

> **Category:** USD Basics · **Script:** `03_usd_materials.py`

## Overview

Introduces **PBR (Physically Based Rendering) materials** in USD. Creates
materials with realistic shading properties and binds them to geometry prims,
demonstrating the material-binding workflow used throughout Omniverse.

## Prerequisites

- Complete **Tutorials 01–02** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_basics\03_usd_materials\03_usd_materials.py
```

## What It Does

1. **Creates PBR Materials** — defines materials with diffuse color, roughness,
   metallic, and other shading properties.
2. **Binds Materials to Prims** — associates each material with geometry.
3. **Demonstrates Material Binding Strength** — shows how binding precedence works.
4. **Creates Multiple Material Variations** — different looks for the same shape.

## Key API Calls

```python
from pxr import UsdShade, Sdf

# Create a material prim
material = UsdShade.Material.Define(stage, "/World/Materials/RedMat")

# Create a PBR shader and connect it to the material
shader = UsdShade.Shader.Define(stage, "/World/Materials/RedMat/PBRShader")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(Gf.Vec3f(1, 0, 0))

# Bind the material to a prim
UsdShade.MaterialBindingAPI(prim).Bind(material)
```

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **UsdShade.Material** | A container for one or more shaders |
| **UsdPreviewSurface** | USD's standard PBR shader |
| **Material Binding** | Linking a material to a geometry prim |
| **MaterialBindingAPI** | The API used to apply materials |

## Output

```
tutorials\usd_basics\03_usd_materials\output\
└── 03_usd_materials.usda   # PBR materials and material bindings
```

## Notes

- **Re-running:** Uses `Usd.Stage.CreateNew()` — delete the existing
  `.usda` before re-running:
  ```batch
  del tutorials\usd_basics\03_usd_materials\output\03_usd_materials.usda
  ```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Material not visible on geometry | Binding not applied, or wrong strength | Use `MaterialBindingAPI(prim).Bind(material)` |
| Shader input ignored | Wrong input name or type | Match `Sdf.ValueTypeNames` to the input (e.g. `Color3f` for color) |

## Next Steps

Continue to **Tutorial 04: USD Animation**.
