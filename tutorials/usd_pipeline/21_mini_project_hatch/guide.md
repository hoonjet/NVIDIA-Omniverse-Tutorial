# Tutorial 21: Mini Project — Servo-Driven Dryer Hatch

The finale of the series: the **smallest project that actually runs** — one
asset, one physics rule, one sensor, in a single ~300-line script.

## Overview

Everything tutorials 01–20 taught is compressed into three parts:

| Piece | Prim(s) | What it is |
|-------|---------|------------|
| **One asset** | `/World/Hatch` (Frame + Door) | A dryer-style hatch: an anchored frame and a hinged door |
| **One rule** | `/World/Hatch/Hinge` | A `RevoluteJoint` with a `DriveAPI` position servo: the door opens as the sensor reports a hot load |
| **One sensor** | `/World/Sensor` | A temperature sensor whose `data:temperature` readings stream in as **value clips** |

The rule itself is *pure USD wiring, no code in the stage*: the servo target
position is authored as time samples derived from the sensor readings —

```
angle = clamp((T − 60 °C) / 25 °C, 0, 1) × 110°
```

## Prerequisites

- Tutorials 01–20 (especially 13, 18, 20 — physics, value clips, articulation)
- USD 26.x via `usd-core`; no GPU or renderer required to build and verify

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\21_mini_project_hatch\21_mini_project_hatch.py
```

Re-running is safe: the script deletes and regenerates its output.

## What It Does

1. **Writes the sensor cache** — `output\clips\sim_t.0000–0003.usd` hold one
   temperature sample each (40, 55, 70, 85 °C) plus a manifest declaring
   `data:temperature`. This is the sensor's data stream, exactly like the
   value clips of tutorial 18.
2. **Builds the stage** — PhysicsScene (gravity 981 cm/s²), the hatch asset
   (kinematic Frame + dynamic Door with mass 1.5 kg), the hinge rule
   (RevoluteJoint on X, limits 0–110°, angular DriveAPI whose
   `targetPosition` has four time samples computed by the rule), and the
   sensor prim bound to the clip set via `Usd.ClipsAPI`.
3. **Reloads and verifies** — the sensor readings must resolve through
   `ResolveInfoSourceValueClips`, and every authored servo target must equal
   the rule applied to the corresponding reading:

```
t=0: sensor 40.0 C -> servo 0.0 deg     (closed)
t=1: sensor 55.0 C -> servo 0.0 deg     (closed)
t=2: sensor 70.0 C -> servo 44.0 deg    (opening)
t=3: sensor 85.0 C -> servo 110.0 deg   (fully open)
```

## Key API / Concepts

- `UsdPhysics.RevoluteJoint` + `UsdPhysics.DriveAPI(prim, "angular")` — a
  position servo with `targetPosition` **time samples**
- `Usd.ClipsAPI` (`SetClipManifestAssetPath`, `SetClipTemplateAssetPath`,
  `SetClipPrimPath`, `SetClipTemplateStartTime/EndTime/Stride`) — the
  programmatic way to author a template clip set (tutorial 18 wrote the same
  metadata by hand)
- `UsdGeom.GetStageMetersPerUnit` / gravity magnitude — unit consistency
- `Usd.ResolveInfo.GetSource() == Usd.ResolveInfoSourceValueClips`

## Output

```
21_mini_project_hatch\
├── 21_mini_project_hatch.py
├── guide.md
└── output\
    ├── 21_mini_project_hatch.usda   # the runnable stage
    └── clips\                       # manifest + sim_t.0000–0003.usd
```

## Notes

- **"Actually runs" means:** scrub t=0..3 in any USD viewer and both the
  sensor readings and the servo targets slide; drop the stage into Omniverse
  Composer and the PhysX solver swings the door open as time advances.
- Clip prims use the **same path as the stage prim** (`/World/Sensor`); this
  build's clips machinery maps clips by identical paths.
- Extend it by adding a second sensor, changing the rule curve, or replacing
  the clips with live simulator output — that is what the series prepared
  you for.
