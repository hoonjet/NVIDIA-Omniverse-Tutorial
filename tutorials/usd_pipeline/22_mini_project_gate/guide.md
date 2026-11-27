# Tutorial 22: Mini Project — Proximity Gate

Second mini project of the finale: one asset, one physics rule, one sensor —
built around a **distance** sensor this time.

## Overview

| Piece | Prim(s) | What it is |
|-------|---------|------------|
| **One asset** | `/World/Gate` (Frame + Slider) | A sliding warehouse gate: an anchored post and a sliding panel |
| **One rule** | `/World/Gate/Rail` | A `PrismaticJoint` with a `DriveAPI` **linear** position servo: the gate slides open when the sensor reports something close |
| **One sensor** | `/World/ProximitySensor` | A proximity sensor whose `data:distance` readings stream in as **value clips** |

The rule: slider target = 6 scene units (fully open) when distance < 2.0,
closed (0) otherwise.

## Prerequisites

- Tutorials 01–20 (especially 13, 18, 20 — physics, value clips, articulation)
- USD 26.x via `usd-core`; no GPU or renderer required to build and verify

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\22_mini_project_gate\22_mini_project_gate.py
```

Re-running is safe: the script deletes and regenerates its output.

## What It Does

1. **Writes the sensor cache** — `output\clips\sim_t.0000–0003.usd` hold one
   distance sample each (5.0, 3.0, 1.2, 0.4 — an object approaching the
   gate) plus a manifest declaring `data:distance`.
2. **Builds the stage** — PhysicsScene, the gate asset (kinematic Frame +
   dynamic Slider with mass 20 kg), the rail rule (`PrismaticJoint` on X,
   limits 0–6, linear DriveAPI whose `targetPosition` has four time samples
   computed by the rule), and the sensor prim bound to the clip set.
3. **Reloads and verifies** — every authored servo target must equal the
   rule applied to the corresponding sensor reading:

```
t=0: sensor 5.0 -> slider 0.0     (far — closed)
t=1: sensor 3.0 -> slider 0.0     (still far — closed)
t=2: sensor 1.2 -> slider 6.0     (close — open)
t=3: sensor 0.4 -> slider 6.0     (very close — open)
```

## Key API / Concepts

- `UsdPhysics.PrismaticJoint` — a translational joint; pairs with the
  **linear** flavour of `UsdPhysics.DriveAPI(prim, "linear")` and
  `drive:linear:physics:*` attributes
- `Usd.ClipsAPI` setters (`SetClipManifestAssetPath`,
  `SetClipTemplateAssetPath`, `SetClipPrimPath`,
  `SetClipTemplateStartTime/EndTime/Stride`) — template clip sets authored
  programmatically
- `Usd.ResolveInfo.GetSource() == Usd.ResolveInfoSourceValueClips`
- Revolute vs Prismatic joints: rotation vs translation; angular vs linear
  drive

## Output

```
22_mini_project_gate\
├── 22_mini_project_gate.py
├── guide.md
└── output\
    ├── 22_mini_project_gate.usda    # the runnable stage
    └── clips\                       # manifest + sim_t.0000–0003.usd
```

## Notes

- **"Actually runs" means:** scrub t=0..3 in any USD viewer and the sensor
  readings and servo targets slide together; drop the stage into Omniverse
  Composer and PhysX slides the gate open as the "object" approaches.
- Clip prims use the **same path as the stage prim**
  (`/World/ProximitySensor`); this build's clips machinery maps clips by
  identical paths.
- Where tutorial 21 rotated (RevoluteJoint + angular drive), this tutorial
  translates (PrismaticJoint + linear drive) — together they cover the two
  fundamental servo motions.
