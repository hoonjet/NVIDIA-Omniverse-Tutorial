#!/usr/bin/env python
"""
================================================================================
Tutorial 19: Volume Fields - UsdVol Structure + Voxel Field Visualization
================================================================================

Simulations produce 3D scalar/vector fields (temperature, pressure, density).
In USD, `UsdVol` defines the volume framework:

    UsdVol.Volume        - the renderable volume prim (schema type "Volume")
    UsdVol.OpenVDBAsset  - a field child pointing at an OpenVDB grid via
                           `filePath` + `fieldIndex` + `fieldDataType`

A Volume prim does NOT store voxels itself - it references field data
(usually a `.vdb` file). This tutorial authors the full UsdVol structure
pointing at `temperature.vdb`, and - because the `pyopenvdb` module is not
installed in this environment - also builds a NATIVE USD voxel visualization:
a PointInstancer of small cubes placed at the cell centers of a 4x4x4
temperature grid, colored hot->cold via per-instance primvars
(interpolation = "instance").

That way the stage is fully inspectable (the .vdb file can be dropped in
later by any VDB-capable tool), and you learn:
  - UsdVol.Volume / OpenVDBAsset authoring and the `fields` relationship
  - PointInstancer per-instance primvars (displayColor, instance interpolation)
  - grid thresholding into a sparse voxel scatter

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/19_volume_field/19_volume_field.py
================================================================================
"""

import os

from pxr import Usd, UsdGeom, UsdVol, Sdf, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
USDA_PATH = os.path.join(OUTPUT_DIR, "19_volume_field.usda")

GRID_N = 4                  # 4x4x4 cells
CELL_SIZE = 1.0             # world size of one voxel cell
TEMP_THRESHOLD = 0.05       # voxels with temp above this become visible cubes
VDB_FILE_NAME = "temperature.vdb"   # referenced by the OpenVDBAsset field


# ==============================================================================
# Part 1: The simulated temperature field (pure math - no solver needed)
# ==============================================================================

def sample_temperature(i, j, k, n):
    """A deterministic hot plume: hottest in the middle of the slab."""
    nx = (i + 0.5) / n - 0.5
    ny = (j + 0.5) / n - 0.5
    nz = (k + 0.5) / n - 0.5
    r2 = nx * nx + ny * ny + nz * nz
    return max(0.0, min(1.0, 1.0 - 4.0 * r2))


def temperature_grid():
    """Return {(i, j, k): temperature} for the full grid."""
    return {(i, j, k): sample_temperature(i, j, k, GRID_N)
            for i in range(GRID_N)
            for j in range(GRID_N)
            for k in range(GRID_N)}


def temp_to_color(t):
    """Map [0, 1] -> blue (cold) to red (hot)."""
    return Gf.Vec3f(t, 0.15 + 0.1 * (1.0 - t), 1.0 - t)


# ==============================================================================
# Part 2: Author the UsdVol structure + voxel visualization
# ==============================================================================

def build_stage():
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(1)   # two frames: hot voxels rise over time

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- UsdVol.Volume: the renderable volume prim ---------------------------
    volume = UsdVol.Volume.Define(stage, "/World/HeatVolume")

    # --- UsdVol.OpenVDBAsset: a field child pointing at a VDB grid -----------
    # filePath is authored but the file itself is NOT required to open this
    # stage (it is data referenced at render time). Drop a real .vdb in later.
    field = UsdVol.OpenVDBAsset.Define(stage, "/World/HeatVolume/temperatureField")
    field.GetFilePathAttr().Set(VDB_FILE_NAME)
    field.GetFieldDataTypeAttr().Set("float")
    # 'fieldIndex' names the grid inside the vdb file ("temperature").
    # fieldIndex is the integer index of the grid inside the vdb file.
    field.GetFieldIndexAttr().Set(0)

    # Wire the volume -> fields relationship.
    volume.CreateFieldRelationship("temperature", field.GetPath())

    # --- Voxel visualization: PointInstancer of colored cubes ----------------
    grid = temperature_grid()
    visible = [(i, j, k, t) for (i, j, k), t in grid.items()
               if t > TEMP_THRESHOLD]
    visible.sort(key=lambda v: (v[0], v[1], v[2]))

    instancer = UsdGeom.PointInstancer.Define(stage, "/World/VoxelViz")
    cube = UsdGeom.Cube.Define(stage, "/World/VoxelViz/Prototypes/VoxelProto")
    cube.GetSizeAttr().Set(CELL_SIZE * 0.95)

    instancer.GetPrototypesRel().AddTarget(cube.GetPath())
    instancer.GetProtoIndicesAttr().Set([0] * len(visible))

    origin = -0.5 * GRID_N * CELL_SIZE
    positions = []
    colors = []
    scales = []
    for (i, j, k, t) in visible:
        positions.append(Gf.Vec3f(
            origin + (i + 0.5) * CELL_SIZE,
            origin + (j + 0.5) * CELL_SIZE,
            origin + (k + 0.5) * CELL_SIZE))
        colors.append(temp_to_color(t))
        # hotter voxels puff up slightly: scale 0.6 .. 1.0
        s = 0.6 + 0.4 * t
        scales.append(Gf.Vec3f(s, s, s))

    instancer.GetPositionsAttr().Set(positions, Usd.TimeCode(0))
    instancer.GetScalesAttr().Set(scales)

    # Per-instance color: a primvar with interpolation "instance" carries one
    # value per instance (elementSize = instance count).
    pv_api = UsdGeom.PrimvarsAPI(instancer.GetPrim())
    colors_pv = pv_api.CreatePrimvar(
        "displayColor", Sdf.ValueTypeNames.Color3fArray)
    colors_pv.Set(colors)
    # elementSize = instance count makes this primvar PER-INSTANCE.
    colors_pv.SetElementSize(len(colors))

    # --- Animate: hot voxels rise (+y offset at frame 1) ---------------------
    rising = [Gf.Vec3f(p[0], p[1] + 0.35 * (n + 1) / len(positions), p[2])
              for n, p in enumerate(positions)]
    instancer.GetPositionsAttr().Set(rising, Usd.TimeCode(1))

    stage.GetRootLayer().Save()
    temps = [t for (_, _, _, t) in visible]
    print("  [+] Grid %dx%dx%d -> %d visible voxels (threshold %.2f)"
          % (GRID_N, GRID_N, GRID_N, len(visible), TEMP_THRESHOLD))
    print("  [+] Voxel temperature range: %.3f .. %.3f"
          % (min(temps), max(temps)))
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage


# ==============================================================================
# Part 3: Reload and verify the volume + voxel composition
# ==============================================================================

def verify_stage():
    """Reopen the stage and check the UsdVol wiring + instancer data."""
    print("\n--- Step 3: Reloading and verifying ---")
    stage = Usd.Stage.Open(USDA_PATH)

    volume_prim = stage.GetPrimAtPath("/World/HeatVolume")
    print("    volume prim typeName : %s" % volume_prim.GetTypeName())
    print("    Is UsdVol.Volume     : %s"
          % UsdVol.Volume(volume_prim).GetFieldPaths())

    field_prim = stage.GetPrimAtPath("/World/HeatVolume/temperatureField")
    field = UsdVol.OpenVDBAsset(field_prim)
    print("    field filePath       : %s" % field.GetFilePathAttr().Get())
    print("    field fieldIndex     : %s" % field.GetFieldIndexAttr().Get())
    print("    field fieldDataType  : %s" % field.GetFieldDataTypeAttr().Get())

    instancer = UsdGeom.PointInstancer(stage.GetPrimAtPath("/World/VoxelViz"))
    positions = instancer.GetPositionsAttr().Get(Usd.TimeCode(0))
    positions_1 = instancer.GetPositionsAttr().Get(Usd.TimeCode(1))
    colors = instancer.GetPrim().GetAttribute("primvars:displayColor").Get()

    print("    voxel instances      : %d" % len(positions))
    print("    animated positions   : t0[0]=(%.2f, %.2f, %.2f) -> t1[0]=(%.2f, %.2f, %.2f)"
          % (positions[0][0], positions[0][1], positions[0][2],
             positions_1[0][0], positions_1[0][1], positions_1[0][2]))
    print("    per-instance colors  : %d values, first=%s" % (len(colors), colors[0]))

    # Assertions: count, volume wiring, animation delta.
    assert len(positions) == len(colors)
    assert len(UsdVol.Volume(volume_prim).GetFieldPaths()) == 1
    assert positions_1[0][1] > positions[0][1]
    print("    [OK] volume + voxel verification passed")


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 19: Volume Fields - UsdVol Structure + Voxel Visualization")
    print("=" * 80)

    print("\n--- Step 1: Computing the temperature field ---")
    grid = temperature_grid()
    temps = sorted(grid.values())
    print("  [+] Field stats: min=%.3f max=%.3f mean=%.3f"
          % (temps[0], temps[-1], sum(temps) / len(temps)))

    print("\n--- Step 2: Building volume stage ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 19 complete!")
    print("USD output: %s" % USDA_PATH)
    print("(The OpenVDBAsset references %s - drop a real .vdb there to render.)"
          % VDB_FILE_NAME)
    print("=" * 80)


if __name__ == "__main__":
    main()


