#!/usr/bin/env python
"""
================================================================================
Tutorial 20: Physics Articulation - A Servo-Driven Robot Arm
================================================================================

Loose joints between independent rigid bodies (tutorial 13) are fine for
props, but real robots are KINEMATIC TREES: bodies connected by joints in a
rigid hierarchy, simulated by a specialized articulation solver. In USD
Physics, an articulation is:

    Xform "Robot"  (UsdPhysics.ArticulationRootAPI)   <- tree root
      Base    (RigidBodyAPI, kinematic)               <- anchored base link
      Link1   (RigidBodyAPI + CollisionAPI + MassAPI) <- moving links
      Link2   (...)
      J1, J2  (RevoluteJoints under the root, body0/body1 rels, limits,
               DriveAPI with stiffness/damping/targetPosition = servos)

`ArticulationRootAPI` tells the solver (e.g. PhysX) to treat the subtree as
ONE articulated body: joints become internal constraints, drive targets act
as servo motors, and the whole tree advances in a single solver step.

This tutorial builds a 3-joint robot arm (base yaw, shoulder pitch, elbow
pitch), authors position drives, then re-opens the stage and verifies the
articulation wiring: root API, kinematic base, body links, joint limits and
drive targets.

Covered APIs:
  UsdPhysics.Scene / ArticulationRootAPI / RigidBodyAPI (kinematic) /
  CollisionAPI / CylinderCollisionAPI / MassAPI / RevoluteJoint / DriveAPI

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/20_physics_articulation/20_physics_articulation.py
================================================================================
"""

import os

from pxr import Usd, UsdPhysics, UsdGeom, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
USDA_PATH = os.path.join(OUTPUT_DIR, "20_physics_articulation.usda")


# ==============================================================================
# Part 1: Link builders
# ==============================================================================

def make_kinematic_base(stage, path):
    """The anchored root link of the articulation.

    A kinematic rigid body is NOT pushed by forces - it defines the fixed
    pose the rest of the articulation hangs from.
    """
    base = UsdGeom.Cube.Define(stage, path)
    base.GetSizeAttr().Set(1.0)
    base.AddTranslateOp().Set(Gf.Vec3d(0.0, 0.5, 0.0))
    prim = base.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.CollisionAPI.Apply(prim)
    rb = UsdPhysics.RigidBodyAPI(prim)
    rb.CreateKinematicEnabledAttr().Set(True)   # anchored, not dynamic
    print("  [Link] Base (kinematic rigid body): %s" % path)
    return prim


def make_arm_link(stage, path, shape, size, mass, offset):
    """A dynamic articulation link with collision + mass.

    shape: ('cube', s) or ('cylinder', (radius, height))
    offset: world-space translation for the link's rest pose.
    """
    if shape == "cube":
        geom = UsdGeom.Cube.Define(stage, path)
        geom.GetSizeAttr().Set(size)
    else:  # cylinder
        geom = UsdGeom.Cylinder.Define(stage, path)
        geom.GetRadiusAttr().Set(size[0])
        geom.GetHeightAttr().Set(size[1])
    geom.AddTranslateOp().Set(Gf.Vec3d(*offset))

    prim = geom.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.CollisionAPI.Apply(prim)
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    mass_api.CreateMassAttr().Set(mass)
    print("  [Link] %s: shape=%s mass=%.1f at (%.1f, %.1f, %.1f)"
          % (path.rsplit("/", 1)[-1], shape, mass, *offset))
    return prim


def make_revolute_joint(stage, path, body0, body1, local0, local1,
                        axis="Y", limits=(-90.0, 90.0), target=None,
                        stiffness=400.0, damping=20.0):
    """A hinge joint with limits + a POSITION servo drive.

    target: drive targetPosition in degrees. In articulations, DriveAPI with
    a targetPosition + stiffness acts as a servo motor pulling the joint
    toward the target angle - the standard way to pose robot joints.
    """
    joint = UsdPhysics.RevoluteJoint.Define(stage, path)
    joint.CreateBody0Rel().SetTargets([body0])
    joint.CreateBody1Rel().SetTargets([body1])
    joint.CreateAxisAttr().Set(axis)
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(*local0))
    joint.CreateLocalPos1Attr().Set(Gf.Vec3f(*local1))
    joint.CreateLowerLimitAttr().Set(limits[0])
    joint.CreateUpperLimitAttr().Set(limits[1])

    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "angular")
    drive.CreateTypeAttr().Set("angular")
    drive.CreateTargetPositionAttr().Set(target if target is not None else 0.0)
    drive.CreateStiffnessAttr().Set(stiffness)
    drive.CreateDampingAttr().Set(damping)
    drive.CreateMaxForceAttr().Set(500.0)

    print("  [Joint] %s: %s -> %s axis=%s limits=[%g, %g]deg drive(target=%g, k=%g)"
          % (path.rsplit("/", 1)[-1], body0.rsplit("/", 1)[-1],
             body1.rsplit("/", 1)[-1], axis, limits[0], limits[1],
             target if target is not None else 0.0, stiffness))
    return joint


# ==============================================================================
# Part 2: Build the articulation stage
# ==============================================================================

def build_stage():
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- Physics scene with downward gravity --------------------------------
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, -1.0, 0.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)   # cm/s^2 (stage unit = cm)

    # --- The articulation root ------------------------------------------------
    # Marking the subtree root with ArticulationRootAPI is what turns a pile
    # of joints into ONE rigid kinematic tree for the solver.
    arm_root = UsdGeom.Xform.Define(stage, "/World/RobotArm")
    UsdPhysics.ArticulationRootAPI.Apply(arm_root.GetPrim())
    print("  [Root] ArticulationRootAPI on /World/RobotArm")

    # --- Links (a simple 3-DOF arm standing on the base) ---------------------
    make_kinematic_base(stage, "/World/RobotArm/Base")

    make_arm_link(stage, "/World/RobotArm/Link1", "cylinder", (0.2, 3.0), 5.0,
                  (0.0, 2.0, 0.0))     # vertical column on the base
    make_arm_link(stage, "/World/RobotArm/Link2", "cube", 2.5, 3.0,
                  (0.0, 3.5, 0.5))     # upper arm reaching forward
    make_arm_link(stage, "/World/RobotArm/Link3", "cube", 1.5, 1.5,
                  (0.0, 3.5, 2.5))     # forearm

    # --- Joints (base yaw -> shoulder pitch -> elbow pitch) ------------------
    make_revolute_joint(
        stage, "/World/RobotArm/J1",
        "/World/RobotArm/Base", "/World/RobotArm/Link1",
        local0=(0.0, 0.5, 0.0), local1=(0.0, -1.5, 0.0),
        axis="Y", limits=(-150.0, 150.0), target=30.0)      # base yaw servo

    make_revolute_joint(
        stage, "/World/RobotArm/J2",
        "/World/RobotArm/Link1", "/World/RobotArm/Link2",
        local0=(0.0, 1.5, 0.0), local1=(0.0, 0.0, -1.0),
        axis="Z", limits=(-90.0, 90.0), target=-45.0)       # shoulder pitch

    make_revolute_joint(
        stage, "/World/RobotArm/J3",
        "/World/RobotArm/Link2", "/World/RobotArm/Link3",
        local0=(0.0, 0.0, 1.0), local1=(0.0, 0.0, -0.75),
        axis="Z", limits=(-120.0, 0.0), target=-60.0)       # elbow pitch

    stage.GetRootLayer().Save()
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage


# ==============================================================================
# Part 3: Reload and verify the articulation wiring
# ==============================================================================

def verify_stage():
    print("\n--- Step 3: Reloading and verifying ---")
    stage = Usd.Stage.Open(USDA_PATH)

    root = stage.GetPrimAtPath("/World/RobotArm")
    has_artic = root.HasAPI(UsdPhysics.ArticulationRootAPI)
    print("    articulation root     : %s" % has_artic)

    base = stage.GetPrimAtPath("/World/RobotArm/Base")
    kin = UsdPhysics.RigidBodyAPI(base).GetKinematicEnabledAttr().Get()
    print("    base kinematic        : %s" % kin)

    # Walk the joints and report body wiring + servo targets.
    joint_paths = ["/World/RobotArm/J1", "/World/RobotArm/J2",
                   "/World/RobotArm/J3"]
    for jp in joint_paths:
        jprim = stage.GetPrimAtPath(jp)
        joint = UsdPhysics.Joint(jprim)
        body0 = joint.GetBody0Rel().GetTargets()
        body1 = joint.GetBody1Rel().GetTargets()
        limits = (UsdPhysics.RevoluteJoint(jprim).GetLowerLimitAttr().Get(),
                  UsdPhysics.RevoluteJoint(jprim).GetUpperLimitAttr().Get())
        drive = UsdPhysics.DriveAPI(jprim, "angular")
        target = drive.GetTargetPositionAttr().Get()
        stiffness = drive.GetStiffnessAttr().Get()
        print("    %s: %s -> %s limits=%s drive(target=%s deg, k=%s)"
              % (jp.rsplit("/", 1)[-1],
                 body0[0].pathString.rsplit("/", 1)[-1] if body0 else "?",
                 body1[0].pathString.rsplit("/", 1)[-1] if body1 else "?",
                 limits, target, stiffness))
        assert body0 and body1, "joint %s missing body rels" % jp
        assert target is not None, "joint %s missing drive target" % jp

    assert has_artic, "ArticulationRootAPI missing on /World/RobotArm"
    assert kin, "base should be kinematic"
    print("    [OK] articulation verification passed")


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 20: Physics Articulation - A Servo-Driven Robot Arm")
    print("=" * 80)

    print("\n--- Step 1: Building articulation stage ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 20 complete!")
    print("USD output: %s" % USDA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()

