# Tutorial 18: Value Clips - Time-Sliced Simulation Caches

## Overview

A long simulation cache does not fit in one layer, and loading it whole
wastes memory when consumers only scrub a few frames. USD **value clips**
solve this: attribute values are pulled at runtime from a SEQUENCE of
per-time-range layers ("clips"), like a video player pulling frames. The
composed stage still looks like ONE prim with ONE animated attribute -
consumers never see the slicing.

Three pieces are involved:

1. **Clip files** - `sim_t.0000.usd` .. `sim_t.0004.usd`, each holding the
   attributes sampled over ONE unit of time.
2. **A manifest** - `manifest.usda` declares which properties the clips
   supply; attributes NOT declared there are not clip-sourced.
3. **Template clip metadata** on the prim - asset path pattern
   (`./clips/sim_t.####.usd`), start/end time and stride. USD expands the
   template into per-clip asset paths and maps stage time ->
   (clip index, local time).

## Files

- `18_value_clips.py` - the tutorial script
- `output/18_value_clips.usda` - root stage with clip metadata
- `output/clips/sim_t.0000..0004.usd` - the clip layers
- `output/clips/manifest.usda` - property manifest

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\18_value_clips\18_value_clips.py
```

## Sample output

```
time   temperature  pressure
0      20.000       1.000
1      40.000       1.200
2      60.000       1.400
3      80.000       1.600
4      100.000      1.800
[OK] composed values slide through all 5 clips
resolve info source at t=2: ResolveInfoSourceValueClips
```

`ResolveInfoSourceValueClips` is the prove-out: the attribute's winning
opinion comes from the clip set, not from any authored layer.

## Key concepts

- **Template asset path format** - `path/basename.####.usd`. The `#` group
  MUST be its own dot-separated token and the hash count must match the
  zero-padding of your file names (4 files digits = 4 hashes). A mismatched
  hash count silently yields empty values.
- **Time mapping** - stage time `t` maps to clip index
  `floor((t - templateStartTime) / templateStride)`; local time inside the
  clip is `t - index * stride`. Each clip in this tutorial samples its
  value at local time 0.
- **Manifest** - without one, USD uses every attribute it finds in the
  clips. With one, only the declared properties are clip-sourced, which
  keeps the clip set cheap to evaluate and documents intent.
- **Interpolation across clips** - by default values do NOT interpolate
  between clips (each clip owns its time range). Author overlapping time
  ranges in clips plus `interpolateMissingClipValues` for smooth blending.
- **Prim path** - all clips must store the data under the SAME prim path
  (`/Sim` here), declared via `SetClipPrimPath`.

## Exercises

1. Add a `data:residual` attribute to clips + manifest and print it.
2. Author 24 time samples per clip (stride 0.0417) to mimic a 120 fps cache.
3. Switch to explicit clip sets: replace the template with
   `SetClipAssetPaths([...])` + `SetClipTimes(...)` and confirm identical output.
4. Call `Usd.ClipsAPI.GenerateClipManifestFromLayers(stage, '/Sim')` and
   compare the auto-generated manifest with the handwritten one.
