# Tutorial 14: Skeletal Animation

> **Category:** USD Advanced · **Script:** `14_skeletal_animation.py`

## Overview

Introduces **skinned character animation** in USD using the `UsdSkel` schema set.
Creates a simple skeleton with 5 joints, bind/rest poses, a keyframed animation
(arms raising from T-pose), a skinned mesh with joint influences, a blend shape
(morph target), and links everything via `BindingAPI`.

`UsdSkel` is USD's system for:
- **Skeletons** — joint hierarchies with bind/rest poses
- **Skinning** — deforming meshes based on joint transforms (Linear Blend Skinning)
- **Blend shapes** — morph targets (e.g. facial expressions)
- **Animation** — keyframed joint transforms over time

> **Note:** This tutorial authors animation *data* only. To *play* the animation,
> open the `.usda` in USDView or Omniverse USD Composer. On this PC the scene is
> verified by reading attributes and time samples back programmatically.

## Prerequisites

- Complete **Tutorial 12 (USD Lighting)** or the **USD Basics set (01–05)**.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_advanced\14_skeletal_animation\14_skeletal_animation.py
```

## What It Does

1. **Creates a SkelRoot** — `UsdSkel.Root` is a required container for all
   skinned prims (skeletons, skinned meshes must live under a SkelRoot).
2. **Defines a Skeleton** — 5 joints (`root`, `root/spine`, `root/spine/head`,
   `root/spine/arm_L`, `root/spine/arm_R`) with bind transforms (T-pose) and
   rest transforms.
3. **Creates an Animation** — `UsdSkel.Animation` with keyframed rotations:
   at t=0 the arms are in T-pose (identity), at t=24 the arms are raised 60°.
   Translations are constant; scales are (1,1,1).
4. **Creates a Skinned Mesh** — a simple mesh with 5 vertices, bound to the
   skeleton via `BindingAPI`. Each vertex has 2 joint influences (indices +
   weights) using classic linear blend skinning (LBS).
5. **Creates a Blend Shape** — `UsdSkel.BlendShape` with 5 point offsets (a
   "wave" deformation that shifts the top vertices sideways).
6. **Links Everything** — `BindingAPI` connects: mesh → skeleton (rel),
   mesh → animation source (rel), mesh → blend shape targets (rel + names).

## Key API Calls

```python
from pxr import UsdSkel, UsdGeom, Gf, Vt

# SkelRoot (required container)
root = UsdSkel.Root.Define(stage, "/World/Character")

# Skeleton: joints + bind/rest poses
skel = UsdSkel.Skeleton.Define(stage, "/World/Character/Skeleton")
skel.GetJointsAttr().Set(["root", "root/spine", "root/spine/head", ...])
skel.GetBindTransformsAttr().Set([Gf.Matrix4d(...), ...])

# Animation: keyframed joint transforms
anim = UsdSkel.Animation.Define(stage, "/World/Character/Anim")
anim.GetRotationsAttr().Set(quats_at_t0, time=0)
anim.GetRotationsAttr().Set(quats_at_t24, time=24)
anim.GetScalesAttr().Set(Vt.Vec3hArray([Gf.Vec3h(1,1,1)] * 5))

# Skinned mesh: joint indices + weights primvars
binding = UsdSkel.BindingAPI.Apply(mesh.GetPrim())
binding.CreateSkeletonRel().SetTargets([skeleton_path])
binding.CreateSkinningMethodAttr().Set("classicLinear")
binding.CreateJointIndicesPrimvar(False, 2).Set(indices_array)
binding.CreateJointWeightsPrimvar(False, 2).Set(weights_array)

# BlendShape: morph target
bs = UsdSkel.BlendShape.Define(stage, "/World/Blend/Wave")
bs.GetOffsetsAttr().Set([Gf.Vec3f(0,0,0), Gf.Vec3f(0.1,0,0), ...])

# Link animation + blend shapes
binding.CreateAnimationSourceRel().SetTargets([anim_path])
binding.CreateBlendShapeTargetsRel().SetTargets([bs_path])
binding.CreateBlendShapesAttr().Set(["wave"])
```

## Key Concepts

| Schema | Purpose | Key Attributes |
|--------|---------|----------------|
| **SkelRoot** | Required container for skinned prims | (none — just a namespace) |
| **Skeleton** | Joint hierarchy + bind/rest poses | `joints`, `bindTransforms`, `restTransforms` |
| **Animation** | Keyframed joint transforms | `joints`, `translations`, `rotations` (quat), `scales` (half3) |
| **BlendShape** | Morph target (point offsets) | `offsets`, `pointIndices` |
| **BindingAPI** | Links mesh to skeleton/animation | `skeleton` (rel), `animationSource` (rel), `jointIndices`, `jointWeights`, `skinningMethod` |

### Joint Hierarchy

Joints are encoded as path-like strings. Parent-child is determined by the `/`
separator:
```
root              # parent of all
root/spine        # child of root
root/spine/head   # child of spine
root/spine/arm_L  # sibling of head
```

### Skinning (Linear Blend Skin)

Each vertex has up to N joint influences (typically 4):
- **jointIndices**: which joints affect this vertex (indices into skeleton)
- **jointWeights**: how much each joint influences (must sum to 1.0)

When a joint moves, its influenced vertices move proportionally. The deformed
position = sum of (weight × jointTransform × bindInverseTransform × position).

### Blend Shapes

A BlendShape defines *offsets* (deltas) for each point. When the blend shape
weight goes from 0→1, the points move by the offsets. Multiple blend shapes can
be combined (e.g. smile + blink simultaneously).

## Output

```
tutorials\usd_advanced\14_skeletal_animation\output\
└── 14_skeletal_animation.usda   # Skinned character with skeleton + animation
```

## Notes

- **Safe to re-run:** The script removes an existing `.usda` before creating a
  new one, so it can be run repeatedly without manual cleanup.
- **Scales type:** `UsdSkel.Animation.scales` uses half-precision `half3[]`
  (`Vt.Vec3hArray` with `Gf.Vec3h` elements), not regular float arrays.
- **Rotations:** `UsdSkel` uses quaternions (`Gf.Quatf`) for rotations, not
  Euler angles. The quaternion is (w, x, y, z).
- **SkelRoot required:** All skinned meshes must be under a `UsdSkel.Root`.
  Without it, skinning won't evaluate in viewers.
- **No runtime skinning on this PC:** The scene contains all the data needed
  for skinning, but actual deformed mesh evaluation requires a viewer with
  UsdSkel support (USDView, Omniverse USD Composer).

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `AttributeError: 'module pxr.Gf' has no attribute 'Cos'` | Gf has no trig functions | Use Python's `math.cos`/`math.sin` |
| `AttributeError: 'module pxr.Gf' has no attribute 'Half'` | No Half type in Python | Use `Gf.Vec3h` for half-precision vectors |
| `Type mismatch for scales` | scales uses `half3[]` | Use `Vt.Vec3hArray([Gf.Vec3h(1,1,1)] * n)` |
| Skinning doesn't evaluate | No `UsdSkel.Root` parent | Wrap skinned prims in a `UsdSkel.Root` |
| Mesh not deforming | Missing joint indices/weights primvars | Use `CreateJointIndicesPrimvar`/`CreateJointWeightsPrimvar` |
| Animation not playing | Animation not linked to mesh | Call `binding.CreateAnimationSourceRel().SetTargets([anim_path])` |

## Summary

This completes the **USD Advanced tutorial set (12–14)**:
- **12: USD Lighting** — `UsdLux` (lights, filters, shadows)
- **13: USD Physics** — `UsdPhysics` (rigid bodies, collisions, joints)
- **14: Skeletal Animation** — `UsdSkel` (skeletons, skinning, blend shapes)

These cover the three major "domain" schema sets in USD beyond geometry and
materials, giving you a foundation for building complex, simulation-ready
scenes.

