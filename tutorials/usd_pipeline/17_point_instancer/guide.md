# Tutorial 17: PointInstancer - 1000 Instanced Geometry Copies

## Overview

`UsdGeomPointInstancer` is USD's native crowd/scatter mechanism. Instead of
authoring 1000 sphere prims, you author:

- **one prototype** (a regular prim under the instancer's `prototypes` scope),
- a **`positions` point3f array** (one entry per instance),
- a **`protoIndices` int array** (which prototype each instance draws),
- plus optional `orientations`, `scales`, `velocities`, `angularVelocities`
  arrays of the same length.

The whole instance "crowd" is just three arrays. Renderers draw the prototype
once per instance with the implied transform; USD caches stay tiny.

## Files

- `17_point_instancer.py` - the tutorial script
- `output/17_point_instancer.usda` - ground + instancer (only ~33 lines!)

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\17_point_instancer\17_point_instancer.py
```

## What the script demonstrates

1. **Authoring** - `UsdGeom.PointInstancer.Define`, prototype creation under
   `.../Prototypes/SensorProto`, `GetPrototypesRel().AddTarget(...)`,
   `GetPositionsAttr().Set(...)`, `GetProtoIndicesAttr().Set(...)`.
2. **Scatter math** - 1000 sensor instances along an 8-turn helix
   (radius 6, height 40) with deterministic gaussian jitter (`random.Random(42)`).
3. **Verification on reload** - instance count, sampled instance→prototype
   mapping, instances-per-prototype histogram, and the world bounding box
   computed via `instancer.ComputeWorldBound(...)`.

### Sample output

```
positions   : 1000 entries
protoIndices: 1000 entries
prototypes  : ['/World/SensorField/Prototypes/SensorProto']
instance    0: proto=0 pos=(5.94, 0.00, -0.08)
instance  500: proto=0 pos=(6.56, 20.00, 0.40)
instance  999: proto=0 pos=(5.83, 39.96, 0.04)
instances per prototype: {0: 1000}
world bound min: (-7.16, -0.25, -7.45)
world bound max: (7.72, 40.21, 7.49)
[OK] all assertions passed
```

Note the bounding box spans the whole helix (height 0..40 plus sphere
radius) - computed over the instanced transforms, not just the prototype.

## Key concepts

- **Instancer arrays must stay length-locked** - `positions`, `protoIndices`,
  `scales`, `orientations`... all must have one entry per instance; USD
  composition checks this and viewers will drop the instancer if lengths
  disagree with `protoIndices`.
- **Prototypes are ordinary prims** - they can be Models, Meshes, even whole
  subtrees referenced in from an asset layer; anything under the `prototypes`
  scope grafted via the `prototypes` relationship.
- **Per-instance data** - add `scales`/`orientations` arrays for rotated or
  non-uniform instances, or `primvars:...` with `interpolation = "instance"`
  on the instancer for per-instance primvars.
- **Cost model** - memory is O(array length), not O(N prims); this stage
  with 1000 instances is ~33 lines of text.

## Exercises

1. Add a second prototype (a Cone) and alternate `protoIndices` between 0
   and 1; re-run and check the per-prototype histogram becomes `{0: 500, 1: 500}`.
2. Add a `scales` float3 array with a gaussian size distribution.
3. Add `orientations` (quath array) so each sensor points outward from the
   helix axis.
4. Animate: author `positions` time samples at frames 1..24 and scrub the
   stage - instancers animate by sampling the arrays, exactly like tutorials 03/04.
