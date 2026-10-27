"""
Tutorial 13: USD Physics
=========================

Introduces physics simulation authoring in USD using the UsdPhysics schema set.
Creates a physics-ready scene with a gravity scene, static colliders, dynamic
rigid bodies (with mass and initial velocity), mesh collision approximation,
physics materials (friction/restitution), and joints (fixed + revolute with
limits and a motor drive).

This tutorial runs on pure USD authoring APIs (no Kit, no PhysX runtime, no GPU
required). The scene is written to a .usda file. To *simulate* the physics, open
it in a physics-enabled viewer (Omniverse USD Composer with PhysX, or Isaac Sim).

Run:
    cd E:\\omniverse_env
    Scripts\\activate
    python tutorials\\usd_advanced\\13_usd_physics\\13_usd_physics.py
"""

import os
import sys

try:
    from pxr import Usd, UsdGeom, UsdPhysics, UsdShade, Sdf, Gf
except ImportError as e:
    print("ERROR: Could not import pxr. Activate the virtual environment first:")
    print("  cd E:\\omniverse_env")
    print("  Scripts\\activate")
    raise


# ---------------------------------------------------------------------------
# 1. Physics Scene (gravity)
# ---------------------------------------------------------------------------

def create_physics_scene(stage):
    """
    A UsdPhysics.Scene prim defines global simulation parameters:
    gravity direction and magnitude. All bodies in the stage are affected.
    """
    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    # Gravity points down (-Y) at 9.81 m/s^2 (Earth surface gravity)
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, -1.0, 0.0))
    scene.CreateGravityMagnitudeAttr().Set(9.81)
    print("  [Scene] PhysicsScene - gravity=(0,-1,0), magnitude=9.81")
    return scene


# ---------------------------------------------------------------------------
# 2. Static floor collider (collision only, no rigid body = static)
# ---------------------------------------------------------------------------

def create_static_floor(stage):
    """
    A static collider: has CollisionAPI but NOT RigidBodyAPI.
    This makes it an immovable surface that dynamic bodies can hit.
    """
    floor = UsdGeom.Cube.Define(stage, "/World/Floor")
    floor.CreateSizeAttr().Set(20.0)
    floor.AddTranslateOp().Set(Gf.Vec3d(0, -0.5, 0))  # top surface at y=0

    # Apply CollisionAPI to make it a collider
    UsdPhysics.CollisionAPI.Apply(floor.GetPrim())

    print("  [Static] Floor collider (CollisionAPI, no RigidBody = static)")
    return floor


# ---------------------------------------------------------------------------
# 3. Dynamic rigid body (box) with mass
# ---------------------------------------------------------------------------

def create_dynamic_box(stage, path, position, mass=1.0):
    """
    A dynamic rigid body: has both RigidBodyAPI and CollisionAPI, plus MassAPI.
    Gravity and collisions will affect it during simulation.
    """
    box = UsdGeom.Cube.Define(stage, path)
    box.CreateSizeAttr().Set(1.0)
    box.AddTranslateOp().Set(position)

    prim = box.GetPrim()

    # RigidBodyAPI marks this as a dynamic (simulated) body
    rb = UsdPhysics.RigidBodyAPI.Apply(prim)
    rb.CreateRigidBodyEnabledAttr().Set(True)
    rb.CreateVelocityAttr().Set(Gf.Vec3f(0, 0, 0))  # initial linear velocity
    rb.CreateAngularVelocityAttr().Set(Gf.Vec3f(0, 0, 0))

    # CollisionAPI makes it collide with other bodies
    UsdPhysics.CollisionAPI.Apply(prim)

    # MassAPI gives it physical mass (affects momentum, inertia)
    mass_api = UsdPhysics.MassAPI.Apply(prim)
    mass_api.CreateMassAttr().Set(mass)

    print(f"  [Dynamic] {path} - RigidBody + Collision, mass={mass}")
    return box


# ---------------------------------------------------------------------------
# 4. Dynamic sphere with initial velocity
# ---------------------------------------------------------------------------

def create_dynamic_sphere(stage, path, position, velocity, mass=0.5):
    """A dynamic sphere with an initial velocity (will fly then fall)."""
    sphere = UsdGeom.Sphere.Define(stage, path)
    sphere.CreateRadiusAttr().Set(0.5)
    sphere.AddTranslateOp().Set(position)

    prim = sphere.GetPrim()

    rb = UsdPhysics.RigidBodyAPI.Apply(prim)
    rb.CreateRigidBodyEnabledAttr().Set(True)
    rb.CreateVelocityAttr().Set(velocity)  # initial velocity!
    rb.CreateAngularVelocityAttr().Set(Gf.Vec3f(0, 0, 0))

    UsdPhysics.CollisionAPI.Apply(prim)

    mass_api = UsdPhysics.MassAPI.Apply(prim)
    mass_api.CreateMassAttr().Set(mass)

    print(f"  [Dynamic] {path} - velocity={velocity}, mass={mass}")
    return sphere


# ---------------------------------------------------------------------------
# 5. Mesh collision with convex hull approximation
# ---------------------------------------------------------------------------

def create_convex_hull_collider(stage, path, position):
    """
    For complex mesh geometry, USD physics uses MeshCollisionAPI to specify
    how the mesh should be approximated for collision (convex hull is the
    most common choice - fast and stable).
    """
    # Create a more complex mesh (a cylinder) as visual geometry
    cyl = UsdGeom.Cylinder.Define(stage, path)
    cyl.CreateRadiusAttr().Set(0.4)
    cyl.CreateHeightAttr().Set(1.5)
    cyl.AddTranslateOp().Set(position)

    prim = cyl.GetPrim()

    # CollisionAPI + MeshCollisionAPI with convexHull approximation
    UsdPhysics.CollisionAPI.Apply(prim)
    mesh_coll = UsdPhysics.MeshCollisionAPI.Apply(prim)
    mesh_coll.CreateApproximationAttr().Set("convexHull")

    # Also make it a dynamic rigid body
    rb = UsdPhysics.RigidBodyAPI.Apply(prim)
    rb.CreateRigidBodyEnabledAttr().Set(True)

    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr().Set(2.0)

    print(f"  [MeshColl] {path} - convexHull approximation, mass=2.0")
    return cyl


# ---------------------------------------------------------------------------
# 6. Physics material (friction + restitution)
# ---------------------------------------------------------------------------

def create_physics_material(stage, path, static_friction, dynamic_friction,
                           restitution):
    """
    A UsdPhysics.MaterialAPI defines surface properties: friction and
    restitution (bounciness). Applied to colliders just like render materials.
    """
    # Create a material prim (same prim type as render materials)
    material = UsdShade.Material.Define(stage, path)
    prim = material.GetPrim()

    phys_mat = UsdPhysics.MaterialAPI.Apply(prim)
    phys_mat.CreateStaticFrictionAttr().Set(static_friction)
    phys_mat.CreateDynamicFrictionAttr().Set(dynamic_friction)
    phys_mat.CreateRestitutionAttr().Set(restitution)

    print(f"  [Material] {path} - sFriction={static_friction}, "
          f"dFriction={dynamic_friction}, restitution={restitution}")
    return material


def bind_physics_material(prim, material):
    """Bind a physics material to a collider using MaterialBindingAPI."""
    UsdShade.MaterialBindingAPI(prim).Bind(material)


# ---------------------------------------------------------------------------
# 7. Joints: Fixed and Revolute (with limits and drive)
# ---------------------------------------------------------------------------

def create_fixed_joint(stage, path, body0_path, body1_path):
    """
    A FixedJoint rigidly connects two bodies so they move together.
    Common use: welding parts, attaching accessories.
    """
    joint = UsdPhysics.FixedJoint.Define(stage, path)
    joint.CreateBody0Rel().SetTargets([body0_path])
    joint.CreateBody1Rel().SetTargets([body1_path])

    # Local frame transforms (where the joint attaches on each body)
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0.5, 0, 0))  # edge of body0
    joint.CreateLocalPos1Attr().Set(Gf.Vec3f(-0.5, 0, 0))  # edge of body1
    joint.CreateLocalRot0Attr().Set(Gf.Quatf(1, 0, 0, 0))  # identity
    joint.CreateLocalRot1Attr().Set(Gf.Quatf(1, 0, 0, 0))

    print(f"  [Joint] FixedJoint {path}: {body0_path} <-> {body1_path}")
    return joint


def create_revolute_joint(stage, path, body0_path, body1_path):
    """
    A RevoluteJoint is a hinge: allows rotation around one axis.
    Here we add angular limits and a motor drive.
    """
    joint = UsdPhysics.RevoluteJoint.Define(stage, path)
    joint.CreateBody0Rel().SetTargets([body0_path])
    joint.CreateBody1Rel().SetTargets([body1_path])

    joint.CreateAxisAttr().Set("Y")  # rotate around Y axis
    joint.CreateLocalPos0Attr().Set(Gf.Vec3f(0, 0, 0))
    joint.CreateLocalPos1Attr().Set(Gf.Vec3f(0, 1.0, 0))

    # Angular limits (in degrees): -90 to +90
    joint.CreateLowerLimitAttr().Set(-90.0)
    joint.CreateUpperLimitAttr().Set(90.0)

    # DriveAPI adds a motor: target velocity with stiffness/damping
    drive = UsdPhysics.DriveAPI.Apply(joint.GetPrim(), "angular")
    drive.CreateTypeAttr().Set("angular")
    drive.CreateTargetVelocityAttr().Set(30.0)   # deg/s
    drive.CreateDampingAttr().Set(10.0)
    drive.CreateStiffnessAttr().Set(100.0)
    drive.CreateMaxForceAttr().Set(50.0)

    print(f"  [Joint] RevoluteJoint {path}: axis=Y, limits=[-90,90]deg, "
          f"drive(vel=30, stiff=100)")
    return joint


# ---------------------------------------------------------------------------
# 8. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("Tutorial 13: USD Physics")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    usd_file = os.path.join(output_dir, "13_usd_physics.usda")

    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    print("\n[1/7] Creating physics scene (gravity)...")
    create_physics_scene(stage)

    print("\n[2/7] Creating static floor collider...")
    floor = create_static_floor(stage)

    print("\n[3/7] Creating dynamic rigid bodies...")
    box_a = create_dynamic_box(stage, "/World/BoxA",
                               Gf.Vec3d(-3, 5, 0), mass=1.0)
    box_b = create_dynamic_box(stage, "/World/BoxB",
                               Gf.Vec3d(-1.5, 5, 0), mass=1.0)

    print("\n[4/7] Creating dynamic sphere with initial velocity...")
    sphere = create_dynamic_sphere(stage, "/World/Ball",
                                   Gf.Vec3d(2, 8, 0),
                                   Gf.Vec3f(2.0, 0, 1.0), mass=0.5)

    print("\n[5/7] Creating mesh collider with convex hull...")
    create_convex_hull_collider(stage, "/World/Cylinder",
                                Gf.Vec3d(4, 6, 0))

    print("\n[6/7] Creating physics materials...")
    bouncy_mat = create_physics_material(
        stage, "/World/PhysicsMaterials/Bouncy",
        static_friction=0.3, dynamic_friction=0.2, restitution=0.8
    )
    grippy_mat = create_physics_material(
        stage, "/World/PhysicsMaterials/Grippy",
        static_friction=0.9, dynamic_friction=0.7, restitution=0.1
    )
    bind_physics_material(sphere.GetPrim(), bouncy_mat)
    bind_physics_material(box_a.GetPrim(), grippy_mat)
    print("  [Bind] Bouncy -> Sphere, Grippy -> BoxA")

    print("\n[7/7] Creating joints...")
    create_fixed_joint(stage, "/World/Joints/Fixed",
                       "/World/BoxA", "/World/BoxB")
    # Revolute joint between the static floor and a hanging box
    pendulum_box = create_dynamic_box(stage, "/World/Pendulum",
                                      Gf.Vec3d(6, 3, 0), mass=0.3)
    create_revolute_joint(stage, "/World/Joints/Revolute",
                          "/World/Floor", "/World/Pendulum")

    print("\n[8/8] Saving stage...")
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    # --- Verification ---
    print("\n--- Verification: Physics prims in stage ---")
    for p in stage.Traverse():
        prim = stage.GetPrimAtPath(p.GetPath())
        apis = []
        if UsdPhysics.RigidBodyAPI(prim):
            apis.append("RigidBody")
        if UsdPhysics.CollisionAPI(prim):
            apis.append("Collision")
        if UsdPhysics.MassAPI(prim):
            mass = UsdPhysics.MassAPI(prim).GetMassAttr().Get()
            apis.append(f"Mass={mass}")
        if UsdPhysics.MaterialAPI(prim):
            r = UsdPhysics.MaterialAPI(prim).GetRestitutionAttr().Get()
            apis.append(f"Restitution={r}")
        if apis:
            print(f"  {p.GetPath()}: {', '.join(apis)}")

    # Verify joints
    for joint_path in ["/World/Joints/Fixed", "/World/Joints/Revolute"]:
        jp = stage.GetPrimAtPath(joint_path)
        if jp.IsValid():
            b0 = UsdPhysics.Joint(jp).GetBody0Rel().GetTargets()
            b1 = UsdPhysics.Joint(jp).GetBody1Rel().GetTargets()
            print(f"  Joint {joint_path}: body0={b0}, body1={b1}")

    # Verify mesh collision approximation
    cyl_prim = stage.GetPrimAtPath("/World/Cylinder")
    approx = UsdPhysics.MeshCollisionAPI(cyl_prim).GetApproximationAttr().Get()
    print(f"  Cylinder collision approximation: {approx}")

    # Verify scene gravity
    scene = UsdPhysics.Scene(stage.GetPrimAtPath("/World/PhysicsScene"))
    g_dir = scene.GetGravityDirectionAttr().Get()
    g_mag = scene.GetGravityMagnitudeAttr().Get()
    print(f"  Gravity: dir={tuple(g_dir)}, mag={g_mag}")

    print(f"\nOutput file: {usd_file}")
    print("Open in a physics-enabled viewer (Omniverse USD Composer with PhysX,")
    print("or Isaac Sim) to simulate the physics. Inspect the .usda text to see")
    print("how physics attributes are authored.")
    print("=" * 80)
    print("Tutorial 13 complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()


