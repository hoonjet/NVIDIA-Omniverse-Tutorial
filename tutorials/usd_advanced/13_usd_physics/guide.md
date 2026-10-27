# Tutorial 13: USD Physics

> **Category:** USD Advanced · **Script:** `13_usd_physics.py`

## Overview

Introduces **physics simulation** in USD using the `UsdPhysics` schema set — the
part of USD that defines rigid body dynamics, collisions, mass, friction,
joints, and motors. Creates a complete physics-ready scene with a gravity scene,
static colliders, dynamic rigid bodies (with mass and initial velocity), mesh
collision approximation, physics materials (friction/restitution), and two
joint types (fixed + revolute with limits and a motor drive).

> **Note:** This tutorial authors physics *data* only. To actually *simulate*
> the physics (bodies falling, colliding, joints rotating), open the `.usda`
> in a physics-enabled viewer such as Omniverse USD Composer (with PhysX) or
> NVIDIA Isaac Sim. On this PC the scene is verified by reading attributes back
> programmatically.

## Prerequisites

- Complete **Tutorial 12 (USD Lighting)** or the **USD Basics set (01–05)**.
- Activate the virtual environment:
  ```batch
  cd YOUR_DIRECTORY\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd YOUR_DIRECTORY\omniverse_env
Scripts\activate
python tutorials\usd_advanced\13_usd_physics\13_usd_physics.py
```

## What It Does

1. **Creates a Physics Scene** — defines global gravity (9.81 m/s², -Y direction).
2. **Static Floor Collider** — a box with `CollisionAPI` but no `RigidBodyAPI`
   (immovable surface that dynamic bodies can hit).
3. **Dynamic Rigid Bodies** — two cubes with `RigidBodyAPI` + `CollisionAPI` +
   `MassAPI` (gravity and collisions affect them).
4. **Dynamic Sphere with Velocity** — a sphere with an initial velocity vector
   (it will fly forward, then fall under gravity).
5. **Mesh Collision (Convex Hull)** — a cylinder using `MeshCollisionAPI` with
   `convexHull` approximation (fast, stable collision for complex shapes).
6. **Physics Materials** — two materials: Bouncy (high restitution=0.8) and
   Grippy (high friction=0.9), bound to specific colliders.
7. **Joints:**
   - **FixedJoint** — rigidly connects BoxA and BoxB (they move together).
   - **RevoluteJoint** — a hinge between the floor and a pendulum box, with
     angular limits (-90° to +90°) and a `DriveAPI` motor (target velocity 30°/s).
## Key API Calls

```python
from pxr import UsdPhysics, UsdGeom, UsdShade, Gf

# Physics scene (gravity)
scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0, -1, 0))
scene.CreateGravityMagnitudeAttr().Set(9.81)

# Static collider (CollisionAPI only)
UsdPhysics.CollisionAPI.Apply(floor_prim)

# Dynamic rigid body (RigidBodyAPI + CollisionAPI + MassAPI)
UsdPhysics.RigidBodyAPI.Apply(prim).CreateRigidBodyEnabledAttr().Set(True)
UsdPhysics.CollisionAPI.Apply(prim)
UsdPhysics.MassAPI.Apply(prim).CreateMassAttr().Set(1.0)

# Mesh collision approximation
UsdPhysics.MeshCollisionAPI.Apply(prim).CreateApproximationAttr().Set("convexHull")

# Physics material (friction + restitution)
phys = UsdPhysics.MaterialAPI.Apply(material_prim)
phys.CreateDynamicFrictionAttr().Set(0.7)
phys.CreateRestitutionAttr().Set(0.8)  # bounciness

# Joints
joint = UsdPhysics.FixedJoint.Define(stage, "/World/Joint")
joint.CreateBody0Rel().SetTargets(["/World/BoxA"])
joint.CreateBody1Rel().SetTargets(["/World/BoxB"])

# Revolute joint with limits and motor drive
rj = UsdPhysics.RevoluteJoint.Define(stage, "/World/Hinge")
rj.CreateAxisAttr().Set("Y")
rj.CreateLowerLimitAttr().Set(-90.0)
rj.CreateUpperLimitAttr().Set(90.0)
drive = UsdPhysics.DriveAPI.Apply(rj.GetPrim(), "angular")
drive.CreateTargetVelocityAttr().Set(30.0)
```

## Key Concepts

| API | Purpose | Key Attributes |
|-----|---------|----------------|
| **Scene** | Global gravity + simulation settings | `gravityDirection`, `gravityMagnitude` |
| **RigidBodyAPI** | Marks a prim as dynamic (simulated) | `rigidBodyEnabled`, `velocity`, `angularVelocity` |
| **CollisionAPI** | Marks a prim as a collider | `collisionEnabled` |
| **MassAPI** | Physical mass and inertia | `mass`, `density`, `centerOfMass` |
| **MeshCollisionAPI** | Collision approximation for meshes | `approximation` (convexHull, boundingSphere…) |
| **MaterialAPI** | Surface friction + restitution | `staticFriction`, `dynamicFriction`, `restitution` |
| **FixedJoint** | Welds two bodies together | `body0`, `body1`, `localPos0/1` |
| **RevoluteJoint** | Hinge (1-axis rotation) | `axis`, `lowerLimit`, `upperLimit` |
| **DriveAPI** | Motor on a joint | `targetVelocity`, `stiffness`, `damping`, `maxForce` |

### Static vs Dynamic

| Type | CollisionAPI | RigidBodyAPI | Behavior |
|------|-------------|--------------|----------|
| **Static** | Yes | No | Immovable wall — other bodies bounce off it |
| **Dynamic** | Yes | Yes | Falls under gravity, collides, responds to forces |

### Collision Approximations

| Token | Description |
|-------|-------------|
| `convexHull` | Shrink-wrap the mesh into a convex shape (most common, fast) |
| `boundingCube` | Use an axis-aligned bounding box |
| `boundingSphere` | Use a bounding sphere |
| `convexDecomposition` | Decompose into multiple convex pieces (V-HACD) |

## Output

```
tutorials\usd_advanced\13_usd_physics\output\
└── 13_usd_physics.usda   # Physics scene with rigid bodies, joints, materials
```

## Notes

- **Safe to re-run:** The script removes an existing `.usda` before creating a
  new one, so it can be run repeatedly without manual cleanup.
- **No simulation runtime:** This PC has no PhysX runtime. The scene contains
  all the *data* needed for simulation, but actual physics stepping requires
  a physics-enabled viewer (Omniverse USD Composer with PhysX, or Isaac Sim).
- **Static vs Dynamic:** A prim with `CollisionAPI` but no `RigidBodyAPI` is a
  static collider (immovable). Adding `RigidBodyAPI` makes it dynamic.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Bodies don't fall in viewer | No `UsdPhysics.Scene` prim, or gravity not set | Add a Scene prim with `gravityDirection`/`gravityMagnitude` |
| Body passes through floor | Floor missing `CollisionAPI` | Apply `CollisionAPI.Apply(floor_prim)` |
| Body doesn't respond to gravity | Missing `RigidBodyAPI` | Apply `RigidBodyAPI` and set `rigidBodyEnabled=True` |
| Joint not connecting bodies | `body0`/`body1` rels not set | Call `joint.CreateBody0Rel().SetTargets([path])` |
| Complex mesh collides poorly | Using raw mesh (slow/unstable) | Apply `MeshCollisionAPI` with `convexHull` |
| `DriveAPI.Apply` fails | Wrong instance name | Use `DriveAPI.Apply(joint_prim, "angular")` for revolute joints |

## Next Steps

Continue to **Tutorial 14: Skeletal Animation** to learn how to author skinned
character animation using the `UsdSkel` schema (skeletons, joints, skinning,
and animation).

