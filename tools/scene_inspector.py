"""
Scene Inspector
===============

A dependency-free tool that loads any USD stage (.usda) and prints a formatted
tree showing all prims, their types, schemas, and key attributes.

No matplotlib or any extra packages required - just USD (pxr).

Usage:
    cd E:\\omniverse_env
    Scripts\\activate
    python tools\\scene_inspector.py <path-to-usda-file>

Example:
    python tools\\scene_inspector.py tutorials\\usd_basics\\01_usd_basics\\output\\01_usd_basics.usda
"""

import sys
import os

try:
    from pxr import Usd, UsdGeom, UsdLux, UsdPhysics, UsdSkel, UsdShade
except ImportError:
    print("ERROR: Cannot import pxr. Activate the venv first:")
    print("  cd E:\\omniverse_env")
    print("  Scripts\\activate")
    sys.exit(1)


def get_prim_summary(prim):
    """Extract a human-readable summary of a prim's key attributes."""
    info = []

    if prim.IsA(UsdGeom.Cube):
        size = UsdGeom.Cube(prim).GetSizeAttr().Get()
        info.append(f"size={size}")
    elif prim.IsA(UsdGeom.Sphere):
        radius = UsdGeom.Sphere(prim).GetRadiusAttr().Get()
        info.append(f"radius={radius}")
    elif prim.IsA(UsdGeom.Plane):
        w = UsdGeom.Plane(prim).GetWidthAttr().Get()
        l = UsdGeom.Plane(prim).GetLengthAttr().Get()
        info.append(f"{w}x{l}")
    elif prim.IsA(UsdGeom.Cylinder):
        r = UsdGeom.Cylinder(prim).GetRadiusAttr().Get()
        h = UsdGeom.Cylinder(prim).GetHeightAttr().Get()
        info.append(f"r={r}, h={h}")
    elif prim.IsA(UsdGeom.Mesh):
        pts = UsdGeom.Mesh(prim).GetPointsAttr().Get()
        info.append(f"{len(pts) if pts else 0} verts")
    elif prim.IsA(UsdGeom.Camera):
        fl = UsdGeom.Camera(prim).GetFocalLengthAttr().Get()
        info.append(f"focal={fl}mm")

    if UsdLux.DistantLight(prim):
        info.append(f"intensity={UsdLux.DistantLight(prim).GetIntensityAttr().Get()}")
    elif UsdLux.DomeLight(prim):
        info.append(f"intensity={UsdLux.DomeLight(prim).GetIntensityAttr().Get()}")
    elif UsdLux.RectLight(prim):
        rl = UsdLux.RectLight(prim)
        info.append(f"intensity={rl.GetIntensityAttr().Get()}, "
                     f"{rl.GetWidthAttr().Get()}x{rl.GetHeightAttr().Get()}")
    elif UsdLux.SphereLight(prim):
        sl = UsdLux.SphereLight(prim)
        info.append(f"intensity={sl.GetIntensityAttr().Get()}, "
                     f"radius={sl.GetRadiusAttr().Get()}")

    if UsdPhysics.RigidBodyAPI(prim):
        info.append("RigidBody")
    if UsdPhysics.CollisionAPI(prim):
        info.append("Collision")
    if UsdPhysics.Scene(prim):
        g = UsdPhysics.Scene(prim).GetGravityMagnitudeAttr().Get()
        info.append(f"gravity={g}")

    if UsdSkel.Skeleton(prim):
        joints = UsdSkel.Skeleton(prim).GetJointsAttr().Get()
        info.append(f"{len(joints)} joints")
    elif UsdSkel.Animation(prim):
        rot_attr = UsdSkel.Animation(prim).GetRotationsAttr()
        times = rot_attr.GetTimeSamples()
        info.append(f"{len(times)} keyframes")

    return ", ".join(info) if info else ""


def print_tree(stage):
    """Print the stage's prim hierarchy as a tree."""
    root = stage.GetPseudoRoot()

    def recurse(prim, indent=0):
        prefix = "  " * indent
        name = prim.GetName() if prim.GetName() else "/"
        type_name = prim.GetTypeName()

        badges = []
        if prim.IsA(UsdGeom.Xform):
            badges.append("Xform")
        if prim.IsA(UsdGeom.Mesh):
            badges.append("Mesh")
        if UsdLux.DistantLight(prim) or UsdLux.DomeLight(prim) or \
           UsdLux.RectLight(prim) or UsdLux.SphereLight(prim):
            badges.append("Light")
        if UsdPhysics.Scene(prim):
            badges.append("PhysicsScene")
        if UsdSkel.Root(prim):
            badges.append("SkelRoot")
        if UsdSkel.Skeleton(prim):
            badges.append("Skeleton")
        if UsdSkel.Animation(prim):
            badges.append("Animation")
        if UsdSkel.BlendShape(prim):
            badges.append("BlendShape")
        if UsdPhysics.FixedJoint(prim) or UsdPhysics.RevoluteJoint(prim):
            badges.append("Joint")

        badge_str = f" [{', '.join(badges)}]" if badges else ""
        if type_name and not badges:
            badge_str = f" [{type_name}]"

        summary = get_prim_summary(prim)
        summary_str = f"  ({summary})" if summary else ""

        print(f"{prefix}{'  ' if indent > 0 else ''}{name}{badge_str}{summary_str}")

        for child in prim.GetChildren():
            recurse(child, indent + 1)

    recurse(root)


def main():
    if len(sys.argv) < 2:
        print("Usage: python tools\\scene_inspector.py <path-to-usda-file>")
        print()
        print("Available .usda files:")
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for root, dirs, files in os.walk(os.path.join(base, "tutorials")):
            for f in files:
                if f.endswith(".usda"):
                    rel = os.path.relpath(os.path.join(root, f), base)
                    print(f"  {rel}")
        sys.exit(1)

    usda_path = sys.argv[1]
    if not os.path.exists(usda_path):
        print(f"ERROR: File not found: {usda_path}")
        sys.exit(1)

    stage = Usd.Stage.Open(usda_path)
    if not stage:
        print(f"ERROR: Could not open stage: {usda_path}")
        sys.exit(1)

    print("=" * 70)
    print(f"Scene Inspector: {usda_path}")
    print("=" * 70)
    print()

    up_axis = UsdGeom.GetStageUpAxis(stage)
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    start_code = stage.GetStartTimeCode()
    end_code = stage.GetEndTimeCode()
    print(f"Up Axis: {up_axis}")
    print(f"Meters Per Unit: {mpu}")
    print(f"Time Range: [{start_code}, {end_code}]")
    print()

    prim_count = sum(1 for _ in stage.Traverse())
    print(f"Total prims: {prim_count}")
    print()
    print("-" * 70)
    print("Prim Hierarchy:")
    print("-" * 70)
    print()

    print_tree(stage)

    print()
    print("=" * 70)
    print("Inspection complete.")
    print("=" * 70)


if __name__ == "__main__":
    main()
