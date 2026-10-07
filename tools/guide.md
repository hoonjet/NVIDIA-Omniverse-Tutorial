# USD Visualization Tools

This directory contains two tools for inspecting and visually verifying USD tutorial output files.

## 1. `scene_inspector.py` — Text-Based Scene Tree

**No extra dependencies required** (uses only USD/pxr).

Prints a formatted tree of all prims in a `.usda` file, showing their types, schemas, and key attributes.

### Usage

```bash
cd E:\omniverse_env
Scripts\activate
python tools\scene_inspector.py <path-to-usda-file>
```

### Example

```bash
python tools\scene_inspector.py tutorials\usd_advanced\12_usd_lighting\output\12_usd_lighting.usda
```

Output:
```
======================================================================
Scene Inspector: 12_usd_lighting.usda
======================================================================

Up Axis: Y
Meters Per Unit: 1.0
Time Range: [0.0, 0.0]

Total prims: 20

----------------------------------------------------------------------
Prim Hierarchy:
----------------------------------------------------------------------

/
    World [Xform]
      Floor [Plane]  (20.0x20.0)
      Cube [Cube]  (size=2.0)
      Sphere [Sphere]  (radius=1.2)
      Camera [Camera]  (focal=50.0mm)
      Lights
        SunLight [Light]  (intensity=2.0)
        SkyLight [Light]  (intensity=1.0)
        ...
```

Run without arguments to see all available `.usda` files:
```bash
python tools\scene_inspector.py
```

---

## 2. `visualize.py` — 3D Scene Visualizer

**Requires matplotlib** (`pip install matplotlib`).

Renders a 3D visualization of any USD stage using matplotlib, showing:
- **Geometry**: Cubes, spheres, planes, cylinders, meshes (wireframe + scatter)
- **Lights**: Distant (star), Dome (sphere wireframe), Rect (rectangle), Sphere (small sphere)
- **Camera**: Triangle marker
- **Skeleton**: Joint points connected by bones
- **Physics**: Joints (diamond markers with dashed connections), collision indicators

### Usage

```bash
cd E:\omniverse_env
Scripts\activate

# Interactive 3D window (rotate with mouse, zoom with scroll):
python tools\visualize.py <path-to-usda-file>

# Save PNG without opening a window:
python tools\visualize.py <path-to-usda-file> --save --no-show

# Visualize ALL tutorials at once:
python tools\visualize.py --all --save --no-show
```

### Examples

```bash
# View lighting tutorial interactively:
python tools\visualize.py tutorials\usd_advanced\12_usd_lighting\output\12_usd_lighting.usda

# Save physics tutorial as PNG:
python tools\visualize.py tutorials\usd_advanced\13_usd_physics\output\13_usd_physics.usda --save --no-show

# Generate PNGs for all tutorials:
python tools\visualize.py --all --save --no-show
```

### Output

- **Interactive mode**: Opens a matplotlib 3D window. Use mouse to rotate, scroll to zoom.
- **Save mode**: Saves a `{filename}_viz.png` file in the same directory as the `.usda` file.

### Color Legend

| Color  | Object Type       |
|--------|-------------------|
| Blue   | Cube              |
| Orange | Sphere            |
| Green  | Plane, Camera     |
| Purple | Cylinder, Physics Joint |
| Yellow | Distant Light     |
| Amber  | Dome/Sphere Light |
| Red    | Rect Light, Skeleton Joints |
| Teal   | Camera            |

---

## 3. `verify_all_tutorials.py` — Programmatic Verification

**No extra dependencies required** (uses only USD/pxr).

Runs 193 automated checks across all 14 tutorial output files. Each check loads
the `.usda` file into a USD Stage and inspects the scene graph to verify prims,
schemas, attributes, relationships, time-sampled animation, material bindings,
physics APIs, and skeletal animation data.

### Usage

```powershell
cd E:\omniverse_env
.\Scripts\activate
python tools\verify_all_tutorials.py
```

### What it verifies

| Category | Examples |
|----------|----------|
| Prim existence | `/World/Cube1`, `/World/AnimatedSphere`, etc. |
| Schema types | `IsA(UsdGeom.Cube)`, `IsA(UsdLux.DistantLight)`, `IsA(UsdSkel.Root)` |
| Attribute values | `size=5.0`, `radius=1.5`, `intensity=2.0`, `mass=1.0` |
| Material bindings | Sphere → RedMetal (via `MaterialBindingAPI`) |
| Time-sampled animation | Position at frame 1 vs 60, rotation 0°→360° |
| References | `prim.HasAuthoredReferences()` |
| Variants | Color variant set with Red/Green/Blue |
| Instancing | `prim.IsInstanceable()` for 9 columns |
| Physics | Gravity, RigidBodyAPI, CollisionAPI, joints, materials |
| Skeletal | Skeleton joints, skinning, blendshapes, quaternion keyframes |

### Output

```
SUMMARY: 193 passed, 0 failed, 193 total
All 14 tutorials verified successfully!
```

Exits with code 0 on success, code 1 if any check fails.

---

## 4. `verification_report.md` — Detailed Verification Report

A human-readable report documenting each tutorial's:
- Conceptual purpose and key USD concepts demonstrated
- Verified output prims and attribute values
- Pass/fail status for every check

See `tools/verification_report.md` for the full report.
