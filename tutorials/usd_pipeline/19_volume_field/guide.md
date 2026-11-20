# Tutorial 19: Volume Fields - UsdVol Structure + Voxel Visualization

## Overview

Simulations produce 3D scalar/vector fields (temperature, pressure,
density). USD's `UsdVol` framework models them as:

- **`UsdVol.Volume`** - the renderable volume prim (schema type `Volume`).
  It does not store voxels; it references field data through a named
  relationship per field (`field:temperature = </.../temperatureField>`).
- **`UsdVol.OpenVDBAsset`** - a field prim pointing at an OpenVDB grid via
  `filePath` (the .vdb asset), `fieldIndex` (integer grid index inside the
  file) and `fieldDataType` (e.g. `float`).

Because `pyopenvdb` is NOT installed in this environment, the tutorial does
not write a real .vdb file. Instead it:

1. Authors the complete UsdVol structure referencing `temperature.vdb`
   (the stage opens fine without the file - data is resolved at render time,
   so you can drop a real .vdb in later).
2. Builds a NATIVE USD visualization of the same field: a PointInstancer of
   cubes at the cell centers of a 4x4x4 temperature grid, thresholded,
   colored hot->cold, scaled by heat, and animated to rise over 2 frames.

## Files

- `19_volume_field.py` - the tutorial script
- `output/19_volume_field.usda` - volume + voxel instancer (~45 lines)

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\19_volume_field\19_volume_field.py
```

## Sample output

```
Field stats: min=0.000 max=0.812 mean=0.219
Grid 4x4x4 -> 32 visible voxels (threshold 0.05)
Voxel temperature range: 0.312 .. 0.812
volume prim typeName : Volume
fields: {'temperature': Sdf.Path('/World/HeatVolume/temperatureField')}
field filePath       : @temperature.vdb@
field fieldIndex     : 0
field fieldDataType  : float
voxel instances      : 32
animated positions   : t0[0]=(-1.50, -0.50, -0.50) -> t1[0]=(-1.50, -0.49, -0.50)
[OK] volume + voxel verification passed
```

## Key concepts

- **Volume -> field wiring** - `volume.CreateFieldRelationship("temperature",
  field.GetPath())` authors the named `field:temperature` relationship.
  `GetFieldPaths()` returns the composed targets.
- **fieldIndex is an integer** in this build - the grid index inside the
  .vdb file (not the grid name).
- **Per-instance primvars on a PointInstancer** - author
  `primvars:displayColor` on the instancer and set `elementSize` equal to
  the instance count; each instance then reads its own array entry.
  (Interpolation `"instance"` is not valid on the instancer itself.)
- **Time samples vs default** - `attr.Set(v)` writes the default; with time
  samples present, USD HOLDS the first sample for times before it. Author a
  sample at t=0 explicitly (as this tutorial does) for predictable playback.
- **Thresholding** - sparse volume viz: only cells above a threshold become
  instances, which is exactly how sparse VDB grids stay small.

## Exercises

1. Lower the threshold to 0.01 and watch the voxel count grow; raise it to
   0.7 and watch the field become sparse.
2. Add a second field (`pressureField`, a `Field3DAsset`) wired into the
   same Volume with relationship name `pressure`.
3. Write the temperature grid to a real .vdb using `pyopenvdb`
   (`pip install pyopenvdb`) and set the field's `filePath` to it.
4. Color-map upgrade: replace `temp_to_color` with a proper turbo/viridis
   ramp and re-run.
