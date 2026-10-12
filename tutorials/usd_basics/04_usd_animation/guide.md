# Tutorial 04: USD Animation

> **Category:** USD Basics · **Script:** `04_usd_animation.py`

## Overview

Covers **time-sampled attributes** and **keyframe animation** in USD. Animates
objects over time — translating, rotating, scaling, and changing color — by
setting attribute values at specific time codes.

## Prerequisites

- Complete **Tutorials 01–03** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_basics\04_usd_animation\04_usd_animation.py
```

## What It Does

1. **Sets Up the Timeline** — defines start/end time codes and frame rate.
2. **Animates Translation** — moves objects along a path across frames.
3. **Animates Rotation** — spins objects over time.
4. **Animates Scale & Color** — grows/shrinks and shifts color per frame.
5. **Writes Time Samples** — stores a distinct value at each time code.

## Key API Calls

```python
# Configure the stage timeline
stage.SetStartTimeCode(1)
stage.SetEndTimeCode(120)
stage.SetTimeCodesPerSecond(24.0)

# Set a time-sampled attribute (value at frame 24)
cube.GetAttr("xformOp:translate").Set(Gf.Vec3d(2.0, 0.0, 0.0), time=24)
```

## Key Concepts

| Concept | Meaning |
|---------|---------|
| **Time Code** | A frame index on the stage timeline |
| **Time Sample** | An attribute value stored at a specific time code |
| **TimeCodesPerSecond** | The playback frame rate (e.g. 24 fps) |
| **Keyframe** | A time sample that defines a key point of animation |

## Output

```
tutorials\usd_basics\04_usd_animation\output\
└── 04_usd_animation.usda   # Animated objects (translation, rotation, scale, color)
```

Open the `.usda` to inspect the `timeSamples` blocks:
```batch
notepad tutorials\usd_basics\04_usd_animation\output\04_usd_animation.usda
```

## Notes

- **Re-running:** Uses `Usd.Stage.CreateNew()` — delete the existing
  `.usda` before re-running:
  ```batch
  del tutorials\usd_basics\04_usd_animation\output\04_usd_animation.usda
  ```
- To play animation in a viewer, ensure the timeline is set on the stage
  (`SetStartTimeCode` / `SetEndTimeCode`) and the viewer supports
  time-sampled attributes.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Animation not playing in viewer | Timeline not set on the stage | Call `stage.SetStartTimeCode(1)` / `SetEndTimeCode(...)` |
| Attribute holds only last value | Values set without a `time=` argument | Pass `time=<frame>` when calling `.Set()` |

## Next Steps

Continue to **Tutorial 05: USD Scene Assembly**.
