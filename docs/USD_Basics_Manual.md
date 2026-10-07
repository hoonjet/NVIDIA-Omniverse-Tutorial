# USD Basics Tutorial Set - Manual

> **Location:** `E:\omniverse_env\tutorials\`
> **Prerequisites:** Activate the virtual environment first (see Virtual Environment Usage Guide)
> **USD Version:** 26.3 (installed via `usd-core` pip package)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Environment Setup](#2-environment-setup)
3. [Tutorial 01: USD Basics](#3-tutorial-01-usd-basics)
4. [Tutorial 02: USD Geometry](#4-tutorial-02-usd-geometry)
5. [Tutorial 03: USD Materials](#5-tutorial-03-usd-materials)
6. [Tutorial 04: USD Animation](#6-tutorial-04-usd-animation)
7. [Tutorial 05: USD Scene Assembly](#7-tutorial-05-usd-scene-assembly)
8. [Output Files](#8-output-files)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Overview

This tutorial set covers the fundamentals of **USD (Universal Scene Description)**, the core technology behind NVIDIA Omniverse. USD is an open-source 3D scene description framework developed by Pixar and adopted by NVIDIA as the foundation of Omniverse.

### What You Will Learn

| Tutorial | Topic | Key Skills |
|----------|-------|------------|
| 01 | USD Basics | Stage, Prim, Attribute creation |
| 02 | USD Geometry | Shape creation, Transformations |
| 03 | USD Materials | PBR shaders, Material binding |
| 04 | USD Animation | Time samples, Keyframe animation |
| 05 | Scene Assembly | References, Variants, Instancing |

### Key USD Concepts

- **Stage**: The root container for a USD scene (like a "scene file")
- **Prim**: A single object in the scene (cube, sphere, camera, etc.)
- **Attribute**: A property of a prim (size, color, position, etc.)
- **Schema**: A predefined type that defines what attributes a prim can have
- **Reference**: A link to another USD file, enabling scene composition
- **Variant**: An alternative configuration for a prim (e.g., different materials)
- **Instance**: A shared copy of a prim, reducing memory usage

---

## 2. Environment Setup

### Activating the Virtual Environment

```batch
:: Open Command Prompt (cmd)
cd E:\omniverse_env
Scripts\activate
```

After activation, your prompt should show `(omniverse_env)`:
```
(omniverse_env) E:\omniverse_env>
```

### Verifying the Environment

```batch
python --version          :: Should show Python 3.8.x
python -c "from pxr import Usd; print(Usd.GetVersion())"  :: Should show (0, 26, 3)
```

### Running a Tutorial

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\01_usd_basics.py
```

---

## 3. Tutorial 01: USD Basics

**File:** `01_usd_basics.py`
**Output:** `tutorials/output/01_usd_basics.usda`

### What It Does

1. **Creates a USD Stage** - The root container for the scene
2. **Creates Prims** - Cube, Sphere, Cylinder, and Camera objects
3. **Sets Attributes** - Size, radius, height, color, focal length
4. **Demonstrates Attribute Operations** - Read, modify, and list attributes
5. **Saves and Reloads** - Persists to disk and verifies data

### Key API Calls

```python
# Create a new stage
stage = Usd.Stage.CreateNew(filepath)

# Create a cube prim
cube = UsdGeom.Cube.Define(stage, "/World/Cube1")

# Set an attribute
cube.GetAttr("size").Set(2.0)

# Save to disk
stage.GetRootLayer().Save()
```

### Expected Output

```
================================================================================
Tutorial 01: USD Basics - Stage, Prim, and Attribute
================================================================================

--- Step 1: Creating Stage ---
[OK] Stage created: ...01_usd_basics.usda

--- Step 2: Creating Prims ---
  [+] Created Cube at /World/Cube1, size=2.0, color=red
  [+] Created Sphere at /World/Sphere1, radius=1.5, color=green
  ...
```

---

## 4. Tutorial 02: USD Geometry

**File:** `02_usd_geometry.py`
**Output:** `tutorials/output/02_usd_geometry.usda`

### What It Does

1. **Creates 6 Geometry Types** - Cube, Sphere, Cylinder, Cone, Plane, Capsule
2. **Applies Transforms** - Translate, Rotate, Scale using XformOps
3. **Uses XformCommonAPI** - Simplified transform interface
4. **Reads Back Transforms** - Extracts translation from the matrix

### Key API Calls

```python
# Add a translate operation
xformable.AddTranslateOp().Set(Gf.Vec3d(5.0, 0.0, 0.0))

# Add a rotate operation (around Z axis)
xformable.AddRotateZOp().Set(45.0)

# Add a scale operation
xformable.AddScaleOp().Set(Gf.Vec3f(2.0, 2.0, 0.5))

# Read the local transformation matrix
matrix = xformable.GetLocalTransformation()
translation = matrix.ExtractTranslation()
```

### Transform Operation Order

USD composes transform operations in the order they are added. The order matters:

```
Translate -> Rotate -> Scale  ≠  Scale -> Rotate -> Translate
```

---

## 5. Tutorial 03: USD Materials

**File:** `03_usd_materials.py`
**Output:** `tutorials/output/03_usd_materials.usda`

### What It Does

1. **Sets Display Colors** - Simple per-prim coloring (no lighting)
2. **Creates PBR Materials** - UsdPreviewSurface with albedo, roughness, metalness
3. **Creates Material Variants** - Red Metal, Blue Plastic, Gold Metal, Matte White
4. **Binds Materials** - Associates materials with geometry prims
5. **Inspects Bindings** - Reads back material and shader properties

### PBR Properties

| Property | Range | Description |
|----------|-------|-------------|
| `diffuseColor` | (R, G, B) in [0, 1] | Base color (albedo) |
| `roughness` | 0.0 - 1.0 | Surface roughness (0=mirror, 1=diffuse) |
| `metallic` | 0.0 - 1.0 | Metalness (0=dielectric, 1=metal) |

### Key API Calls

```python
# Create a material
material = UsdShade.Material.Define(stage, "/World/Materials/MyMat")

# Create a PBR shader
shader = UsdShade.Shader.Define(stage, "/World/Materials/MyMat/Shader")
shader.CreateIdAttr("UsdPreviewSurface")
shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set((0.8, 0.1, 0.1))
shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(0.3)
shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(0.8)

# Connect shader to material surface output
material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")

# Bind material to geometry
UsdShade.MaterialBindingAPI.Apply(prim).Bind(material)
```

---

## 6. Tutorial 04: USD Animation

**File:** `04_usd_animation.py`
**Output:** `tutorials/output/04_usd_animation.usda`

### What It Does

1. **Sets Up Timeline** - 120 frames at 24 FPS
2. **Animates Translation** - Sphere moving in a circular path
3. **Animates Rotation** - Cube spinning 360 degrees on Y axis
4. **Animates Scale** - Sphere pulsing between 0.5x and 2.0x
5. **Animates Color** - Cube cycling through colors
6. **Reads Animated Values** - Queries interpolated values at specific frames

### Key API Calls

```python
# Set up timeline
stage.SetStartTimeCode(1)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(24.0)

# Set a time sample (keyframe) on a transform op
translate_op.Set(Gf.Vec3d(x, y, z), frame_number)

# Read the value at a specific time
value = translate_op.Get(frame_number)
```

### Time Sample Interpolation

USD automatically interpolates between time samples using linear interpolation:

```
Frame 1:   position = (5.0, 0.0, 0.0)    [keyframe]
Frame 15:  position = (3.5, 0.0, 3.5)    [interpolated]
Frame 30:  position = (-5.0, 0.0, 0.0)   [keyframe]
```

---

## 7. Tutorial 05: USD Scene Assembly

**File:** `05_usd_assembly.py`
**Output:** `tutorials/output/05_usd_assembly.usda` + asset files in `tutorials/output/assets/`

### What It Does

1. **Creates Asset Files** - Separate USD files for table, chair, lamp
2. **Assembles with References** - Composes assets into a room scene
3. **Creates Variants** - Color variant set (Red, Green, Blue) on a cube
4. **Demonstrates Instancing** - 3x3 grid of instanced columns
5. **Inspects Scene Structure** - Prints the prim tree with annotations

### Key API Calls

```python
# Add a reference to an external USD file
prim.GetReferences().AddReference("path/to/asset.usda")

# Create a variant set
variant_set = prim.GetVariantSets().AddVariantSet("Color")
variant_set.AddVariant("Red")
variant_set.SetVariantSelection("Red")

# Edit within a variant context
with variant_set.GetVariantEditContext():
    cube.GetDisplayColorAttr().Set([(1.0, 0.0, 0.0)])

# Mark a prim as instanceable (for instancing)
prim.SetInstanceable(True)
```

### References vs. Payloads

| Feature | Reference | Payload |
|---------|----------|---------|
| Loading | Immediate | Deferred (lazy) |
| Use case | Small assets | Large assets |
| Memory | Always loaded | Only when needed |

---

## 8. Output Files

After running all tutorials, the following files are generated:

```
E:\omniverse_env\tutorials\output\
├── 01_usd_basics.usda              # Basic stage with cube, sphere, cylinder, camera
├── 02_usd_geometry.usda            # 6 geometry types with transforms
├── 03_usd_materials.usda           # PBR materials and material bindings
├── 04_usd_animation.usda          # Animated objects (translation, rotation, scale, color)
├── 05_usd_assembly.usda           # Assembled room scene with references and variants
└── assets\
    ├── table.usda                  # Table asset (referenced by main scene)
    ├── chair.usda                  # Chair asset (referenced by main scene)
    └── lamp.usda                   # Lamp asset (referenced by main scene)
```

### Viewing .usda Files

`.usda` files are in ASCII text format. You can open them in any text editor:

```batch
notepad E:\omniverse_env\tutorials\output\01_usd_basics.usda
```

---

## 9. Troubleshooting

### Problem: `ModuleNotFoundError: No module named 'pxr'`

**Cause:** The virtual environment is not activated, or `usd-core` is not installed.

**Solution:**
```batch
cd E:\omniverse_env
Scripts\activate
pip install usd-core
```

### Problem: `FileExistsError` when creating a stage

**Cause:** The USD file already exists. `Usd.Stage.CreateNew()` fails if the file exists.

**Solution:** Delete the existing file or use `Usd.Stage.CreateNew()` with `overwrite=True`:
```python
# Delete existing file first
if os.path.exists(filepath):
    os.remove(filepath)
stage = Usd.Stage.CreateNew(filepath)
```

### Problem: Prim not found after creating

**Cause:** The prim path may be incorrect, or the prim was not properly defined.

**Solution:** Check the prim path format:
```python
# Correct: starts with "/", hierarchical
prim = stage.GetPrimAtPath("/World/Cube1")

# Incorrect: does not start with "/"
prim = stage.GetPrimAtPath("World/Cube1")  # Will fail
```

### Problem: Transform not applied

**Cause:** Transform operations must be added in the correct order, and the Xformable interface must be used.

**Solution:**
```python
# Wrap the prim with Xformable
xformable = UsdGeom.Xformable(prim)

# Add operations in order
xformable.AddTranslateOp().Set(Gf.Vec3d(1.0, 0.0, 0.0))
xformable.AddRotateYOp().Set(45.0)
xformable.AddScaleOp().Set(Gf.Vec3f(2.0, 2.0, 2.0))
```

---

## Next Steps

After completing this tutorial set, proceed to:
- **Tutorial Set 2: Omniverse Kit API** (tutorials 06-08)
- **Tutorial Set 3: PhysicsNeMo Integration** (tutorials 09-11)
