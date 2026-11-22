# Tutorial 20: Physics Articulation - A Servo-Driven Robot Arm

## Overview

Loose joints between independent rigid bodies (tutorial 13) are fine for
props, but robots are **kinematic trees**: bodies connected by joints in a
rigid hierarchy, solved by a dedicated articulation solver. In USD Physics,
marking the tree root with `UsdPhysics.ArticulationRootAPI` turns the whole
subtree into ONE articulated body:

- joints become internal constraints (no inter-body collision inside the tree),
- `DriveAPI` with `targetPosition` + stiffness acts as a **servo motor**,
- the solver advances the tree in one step (stable, fast, pose-controllable).

This tutorial builds a 3-DOF robot arm:

```
/World/RobotArm              <- ArticulationRootAPI
  Base    (kinematic rigid body, cube)     - anchored root link
  Link1   (cylinder, mass 5.0)             - vertical column
  Link2   (cube, mass 3.0)                 - upper arm
  Link3   (cube, mass 1.5)                 - forearm
  J1 (Base  -> Link1, axis Y, [-150,150]deg, target  30deg)  base yaw
  J2 (Link1 -> Link2, axis Z, [ -90, 90]deg, target -45deg)  shoulder pitch
  J3 (Link2 -> Link3, axis Z, [-120,  0]deg, target -60deg)  elbow pitch
/World/PhysicsScene          <- gravity (0,-1,0) magnitude 981 cm/s^2
```

## Files

- `20_physics_articulation.py` - the tutorial script
- `output/20_physics_articulation.usda` - scene + articulation (116 lines)

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\20_physics_articulation\20_physics_articulation.py
```

## Sample output

```
[Root] ArticulationRootAPI on /World/RobotArm
[Link] Base (kinematic rigid body): /World/RobotArm/Base
[Joint] J1: Base -> Link1 axis=Y limits=[-150, 150]deg drive(target=30, k=400)
...
articulation root     : True
base kinematic        : True
J1: Base -> Link1 limits=(-150.0, 150.0) drive(target=30.0 deg, k=400.0)
J2: Link1 -> Link2 limits=(-90.0, 90.0) drive(target=-45.0 deg, k=400.0)
J3: Link2 -> Link3 limits=(-120.0, 0.0) drive(target=-60.0 deg, k=400.0)
[OK] articulation verification passed
```

## Key concepts

- **ArticulationRootAPI** - marks the kinematic tree root. Without it,
  joints act as loose constraints between independent rigid bodies.
- **Kinematic base link** - the root link has `RigidBodyAPI` with
  `kinematicEnabled = True`: it is simulated but unaffected by forces, so
  the arm hangs from an immovable anchor.
- **Position servo drives** - `DriveAPI(type="angular")` with
  `targetPosition` (deg), `stiffness` (spring pull toward target) and
  `damping` (velocity bleed). `maxForce` caps the servo torque. Contrast
  with tutorial 13's velocity drives (fan wheels).
- **Joint limits** - `lowerLimit`/`upperLimit` in degrees on the
  RevoluteJoint; the solver clamps motion to this range.
- **Local frames** - `localPos0/localPos1` anchor the joint on each body's
  local frame; getting these wrong is THE classic ragdoll bug.

## Exercises

1. Add a fourth link (gripper) with a prismatic joint
   (`UsdPhysics.PrismaticJoint`) driving along X.
2. Author `drive:angular:targetPosition` time samples to make the arm
   perform a pick-and-place motion; scrub the stage.
3. Change J2's stiffness from 400 to 20 and predict what gravity does to
   the shoulder; re-run in a solver (Isaac Sim / Omniverse Physics).
4. Remove `ArticulationRootAPI` and compare how a solver treats the same
   joint graph.
