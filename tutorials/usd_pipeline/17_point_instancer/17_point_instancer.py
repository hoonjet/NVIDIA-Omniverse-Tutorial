#!/usr/bin/env python
"""
================================================================================
Tutorial 17: PointInstancer - 1000 Instanced Geometry Copies for Free
================================================================================

Drawing 1000 separate sphere prims means 1000 prims, 1000 xform specs and
1000 boundable leaves - expensive for viewers and slow for caches.
`UsdGeom.PointInstancer` solves this with TWO lists plus ONE prototype:

  - prototypes: regular prims stored once under the instancer (`prototypes`)
  - protoIndices: per-instance index into the prototype list
  - positions:    per-instance location (point3f array)

The renderer draws one prototype mesh N times with different transforms.
USD represents the whole crowd as three arrays - the instancer is the only
"instancing" construct USD has natively at this level.

This tutorial scatters 1000 sensor instances along a helix with a gaussian
radius spread, then re-opens the stage and verifies composition:
  - instance count from the arrays
  - which prototype each sampled instance uses
  - the instancer's world bounding box (union over all instances)

Covered APIs:
  UsdGeom.PointInstancer.Define / CreatePrototypes / CreateProtoIndices /
  CreatePositions / ComputeLocalBound / ComputeWorldBound

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/17_point_instancer/17_point_instancer.py
================================================================================
"""

import math
import os
import random

from pxr import Usd, UsdGeom, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
USDA_PATH = os.path.join(OUTPUT_DIR, "17_point_instancer.usda")

NUM_INSTANCES = 1000          # instances scattered along the helix
HELIX_TURNS = 8.0             # vertical loops of the helix
HELIX_HEIGHT = 40.0           # total helix height in world units
HELIX_RADIUS = 6.0            # helix radius
SCATTER_RADIUS = 0.9          # gaussian jitter radius around the ideal point


# ==============================================================================
# Part 1: Build the instancer stage
# ==============================================================================

def build_stage():
    """Author one PointInstancer with a sphere prototype and 1000 instances."""
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)   # cm, the Omniverse default

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Ground plane for visual reference.
    ground = UsdGeom.Cube.Define(stage, "/World/Ground")
    ground.GetSizeAttr().Set(60.0)
    ground.AddTranslateOp().Set(Gf.Vec3d(0.0, -1.0, 0.0))

    # --- The instancer ---------------------------------------------------
    # Defining it also creates the empty `prototypes` scope child, the
    # `protoIndices` int array and the `positions` point3f array.
    instancer = UsdGeom.PointInstancer.Define(stage, "/World/SensorField")

    # One prototype: a small sphere "sensor". Prototypes are ordinary prims
    # authored UNDER the instancer (usually under its `prototypes` scope).
    sphere = UsdGeom.Sphere.Define(
        stage, "/World/SensorField/Prototypes/SensorProto")
    sphere.GetRadiusAttr().Set(0.25)

    # Point the instancer at the prototype list.
    instancer.GetPrototypesRel().AddTarget(sphere.GetPath())

    # --- Per-instance data -------------------------------------------------
    rng = random.Random(42)   # deterministic scatter for reproducible runs

    positions = []
    for i in range(NUM_INSTANCES):
        angle = 2.0 * math.pi * HELIX_TURNS * i / NUM_INSTANCES
        height = HELIX_HEIGHT * i / NUM_INSTANCES
        jitter = rng.gauss(0.0, SCATTER_RADIUS / 2.0)
        jitter2 = rng.gauss(0.0, SCATTER_RADIUS / 2.0)
        positions.append(Gf.Vec3f(
            HELIX_RADIUS * math.cos(angle) + jitter,
            height,
            HELIX_RADIUS * math.sin(angle) + jitter2))

    instancer.GetPositionsAttr().Set(positions)
    # Every instance uses prototype 0 (the only one we authored).
    instancer.GetProtoIndicesAttr().Set([0] * NUM_INSTANCES)

    stage.GetRootLayer().Save()
    print("  [+] Built instancer with %d instances (1 prototype)" % NUM_INSTANCES)
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage


# ==============================================================================
# Part 2: Reopen the stage and verify the composed instancer
# ==============================================================================

def verify_stage():
    """Reload from disk and validate instance data + bounds."""
    print("\n--- Step 2: Reloading and verifying ---")
    stage = Usd.Stage.Open(USDA_PATH)

    instancer = UsdGeom.PointInstancer(stage.GetPrimAtPath("/World/SensorField"))
    positions = instancer.GetPositionsAttr().Get()
    proto_indices = instancer.GetProtoIndicesAttr().Get()
    prototypes = instancer.GetPrototypesRel().GetTargets()

    print("    positions   : %d entries" % len(positions))
    print("    protoIndices: %d entries" % len(proto_indices))
    print("    prototypes  : %s" % [str(t) for t in prototypes])

    # Instance identity checks on a few samples.
    for i in (0, len(positions) // 2, len(positions) - 1):
        p = positions[i]
        print("    instance %4d: proto=%d pos=(%.2f, %.2f, %.2f)"
              % (i, proto_indices[i], p[0], p[1], p[2]))

    # Count instances per prototype (trivial here with one prototype, but
    # this is the loop a real pipeline runs to build per-prototype caches).
    per_proto = {}
    for idx in proto_indices:
        per_proto[idx] = per_proto.get(idx, 0) + 1
    print("    instances per prototype: %s" % per_proto)

    # Bounding box: computed over the instanced transforms, NOT just the
    # prototype. This is what viewers use for framing / culling.
    box = instancer.ComputeWorldBound(Usd.TimeCode.Default(),
                                      purpose1=UsdGeom.Tokens.default_,
                                      purpose2=UsdGeom.Tokens.render)
    rng_val = box.ComputeAlignedRange()
    lo = rng_val.GetMin()
    hi = rng_val.GetMax()
    print("    world bound min: (%.2f, %.2f, %.2f)" % (lo[0], lo[1], lo[2]))
    print("    world bound max: (%.2f, %.2f, %.2f)" % (hi[0], hi[1], hi[2]))

    # Sanity assertions - the tutorial fails loudly if composition breaks.
    assert len(positions) == NUM_INSTANCES
    assert len(proto_indices) == NUM_INSTANCES
    assert all(i == 0 for i in proto_indices)
    assert hi[1] <= HELIX_HEIGHT + 2.0 and lo[1] >= -2.0
    print("    [OK] all assertions passed")


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 17: PointInstancer - 1000 Instanced Geometry Copies")
    print("=" * 80)

    print("\n--- Step 1: Building instancer stage ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 17 complete!")
    print("USD output: %s" % USDA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()

