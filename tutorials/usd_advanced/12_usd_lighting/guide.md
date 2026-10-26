# Tutorial 12: USD Lighting

> **Category:** USD Advanced · **Script:** `12_usd_lighting.py`

## Overview

Introduces **lighting** in USD using the `UsdLux` schema set — the part of USD
that defines how scenes are illuminated. Creates a complete lighting-ready
scene with geometry, PBR materials, a camera, and four fundamental light types
(Distant, Dome, Rect, Sphere), plus a light filter and per-light shadow control.

> **Note:** This tutorial authors lighting *data* only. Rendering the lit scene
> visually requires a renderer (USDView, Omniverse USD Composer, or an RTX GPU).
> On this PC the scene is verified by inspecting the `.usda` text and reading
> attributes back programmatically — the same approach used in tutorials 01–11.

## Prerequisites

- Complete the **USD Basics Tutorial Set (01–05)** first — this tutorial builds
  on prims, geometry, transforms, and materials.
- Activate the virtual environment:
  ```batch
  cd YOUR_DIRECTORY\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd YOUR_DIRECTORY\omniverse_env
Scripts\activate
python tutorials\usd_advanced\12_usd_lighting\12_usd_lighting.py
```

## What It Does

1. **Builds Scene Geometry** — a floor plane, a cube, and a sphere.
2. **Creates PBR Materials** — binds `UsdPreviewSurface` materials so surfaces
   react to light (diffuse color, roughness, metallic).
3. **Adds a Camera** — a perspective camera positioned to view the scene.
4. **Creates 4 Light Types:**
   - **DistantLight** — parallel directional light (like the sun), with color
     temperature (5500K daylight)
   - **DomeLight** — environment/ambient light (sky tint, or HDRI texture)
   - **RectLight** — rectangular area light (soft studio panel), with width/height
   - **SphereLight** — point light with radius (glowing bulb), normalized
5. **Applies a Light Filter** — links a `LightFilter` prim to the RectLight via
   the `light:filters` relationship to modulate its output.
6. **Applies ShadowAPI** — enables shadow casting on the DistantLight.

## Key API Calls

```python
from pxr import UsdLux, UsdGeom, Gf

# DistantLight (directional, like the sun)
sun = UsdLux.DistantLight.Define(stage, "/World/Lights/Sun")
sun.CreateIntensityAttr().Set(2.0)
sun.CreateColorAttr().Set(Gf.Vec3f(1.0, 0.95, 0.85))
sun.CreateColorTemperatureAttr().Set(5500.0)

# DomeLight (environment / ambient)
dome = UsdLux.DomeLight.Define(stage, "/World/Lights/Sky")
dome.CreateColorAttr().Set(Gf.Vec3f(0.6, 0.75, 1.0))

# RectLight (area light with physical size)
rect = UsdLux.RectLight.Define(stage, "/World/Lights/Panel")
rect.CreateWidthAttr().Set(4.0)
rect.CreateHeightAttr().Set(2.0)

# SphereLight (point light with radius)
bulb = UsdLux.SphereLight.Define(stage, "/World/Lights/Bulb")
bulb.CreateRadiusAttr().Set(0.3)
bulb.CreateNormalizeAttr().Set(True)

# Light filter (modifies a light's output)
lf = UsdLux.LightFilter.Define(stage, "/World/Lights/Filter")
rect.CreateFiltersRel().AddTarget("/World/Lights/Filter")

# Shadow control per-light
UsdLux.ShadowAPI.Apply(sun.GetPrim()).CreateShadowEnableAttr().Set(True)
```

## Key Concepts

| Light Type | Physical Analogy | Key Attributes |
|------------|------------------|----------------|
| **DistantLight** | Sun (parallel rays, infinite distance) | `intensity`, `angle`, `colorTemperature` |
| **DomeLight** | Sky / HDRI environment | `intensity`, `color`, `texture:file` |
| **RectLight** | Studio softbox / light panel | `width`, `height`, `intensity` |
| **SphereLight** | Light bulb / point light | `radius`, `intensity`, `normalize` |

| Concept | Meaning |
|---------|---------|
| **Color Temperature** | Warmth/coolness in Kelvin (e.g. 5500K = daylight, 2700K = tungsten) |
| **Normalize** | Makes intensity independent of the light's physical size |
| **Light Filter** | A prim that modifies a light (gobo, tint, intensity falloff) |
| **ShadowAPI** | Per-light shadow control (enable, color, distance falloff) |

## Output

```
tutorials\usd_advanced\12_usd_lighting\output\
└── 12_usd_lighting.usda   # Scene with 4 lights, materials, camera, filter, shadows
```

Inspect the `.usda` to see how lights are authored:
```batch
notepad tutorials\usd_advanced\12_usd_lighting\output\12_usd_lighting.usda
```

## Notes

- **Safe to re-run:** The script removes an existing `.usda` before creating a
  new one, so it can be run repeatedly without manual cleanup.
- **No renderer required:** This PC cannot render the lit scene visually. The
  script verifies the lighting data by reading attributes back from the stage
  after saving. To *see* the lighting, open the `.usda` in USDView or Omniverse
  USD Composer on a machine with a renderer.
- **UsdGeom.Plane:** In USD 26.x, `Plane` uses `width`/`length` attributes (not
  `size`). The script handles this correctly.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `AttributeError: 'Plane' object has no attribute 'CreateSizeAttr'` | Plane uses `width`/`length`, not `size` | Use `CreateWidthAttr()` / `CreateLengthAttr()` |
| `AttributeError: 'Camera' object has no attribute 'SetPerspective'` | `Gf.Camera` API varies across USD versions | Author camera attributes directly (`focalLength`, `horizontalAperture`, etc.) |
| Light not visible in viewer | No renderer, or light intensity too low | Use USDView / USD Composer; increase `intensity` |
| Filter not affecting light | Filter not linked via `light:filters` rel | Call `light.CreateFiltersRel().AddTarget(filterPath)` |

## Next Steps

Continue to **Tutorial 13: USD Physics** (planned) to learn how to author
physics simulation data (rigid bodies, collisions, joints) on USD prims.
