# Tutorial 08: Live Sync

> **Category:** Kit API · **Script:** `08_live_sync.py`

## Overview

Covers **Live Sync** — real-time collaborative editing of USD scenes through
layer composition. Demonstrates layer overrides, change tracking, session
layers, and conflict resolution, all using USD's composition engine.

## Prerequisites

- Complete **Tutorials 01–07** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\kit_api\08_live_sync\08_live_sync.py
```

## What It Does

1. **Creates a Base Layer** — the foundational scene (`base_layer.usda`).
2. **Creates an Override Layer** — edits on top of the base (`override_layer.usda`),
   demonstrating non-destructive composition.
3. **Shared Scene Composition** — combines multiple layers into one shared
   scene (`shared_scene.usda`).
4. **Change Tracking** — uses `Tf.Notice` to listen for stage changes
   (`change_tracking.usda`).
5. **Conflict Resolution** — shows how stronger opinions win when layers
   disagree (`conflict_scene.usda`).

## Key API / Concepts

```python
from pxr import Sdf, Usd, Tf

# Anonymous session layer for non-destructive edits
session = Sdf.Layer.CreateAnonymous("my_session")
stage.GetSessionLayer().subLayerPaths.append(session.identifier)

# Listen for stage changes
def on_stage_changed(notice, sender):
    for path in notice.GetChangedInfoOnlyPaths():
        print(f"Prim changed: {path}")
listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, on_stage_changed, stage)
# ... make changes ...
listener.Revoke()
```

| Concept | Meaning |
|---------|---------|
| **Layer** | A single file/anonymous layer holding opinions |
| **Composition** | Merging opinions from multiple layers by strength |
| **Session Layer** | A non-persistent layer for live, unsaved edits |
| **Tf.Notice** | USD's event/observer system for change tracking |

## Output

```
tutorials\kit_api\08_live_sync\output\
└── live_sync\
    ├── base_layer.usda         # Foundational scene
    ├── override_layer.usda     # Edits on top of the base
    ├── shared_scene.usda       # Composed multi-layer scene
    ├── change_tracking.usda    # Demonstrates Tf.Notice listeners
    └── conflict_scene.usda      # Demonstrates composition strength / conflicts
```

## Notes

- **Safe to re-run:** The script removes each output file before recreating it,
  so it can be run repeatedly without manual cleanup.
- `Tf.Notice.Register` must be called **before** making changes — register the
  listener first, then modify the stage.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `Tf.Notice.Register` not receiving callbacks | Listener registered after changes, or wrong stage object | Register listener FIRST, then modify the same `stage` object |
| Session layer edits not visible | Session layer not added to stage's session sublayers | Append to `stage.GetSessionLayer().subLayerPaths` |

## Architecture

```
Extensions (Tutorial 06)
    │
Connectors (Tutorial 07)
    │
Live Sync (Tutorial 08)  ◄──►  Nucleus Server  ◄──►  Client B
    │
USD Core (Tutorials 01-05)
```

## Next Steps

Kit API complete! Proceed to **Tutorial Set 3: PhysicsNeMo Integration**
(Tutorials 09–11).
