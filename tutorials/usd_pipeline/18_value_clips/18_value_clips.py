#!/usr/bin/env python
"""
================================================================================
Tutorial 18: Value Clips - Time-Sliced Simulation Caches
================================================================================

A long simulation cache (1000 frames x 10 fields) does not fit in one layer.
USD **value clips** solve this: attribute values are pulled at runtime from a
SEQUENCE of per-time-range layers ("clips"), exactly like a video player
pulls frames from video files. The composed stage still looks like ONE prim
with ONE animated attribute - consumers never see the slicing.

Three pieces are involved:
  1. Clip files  - `sim_t0000.usd` .. `sim_t0004.usd`, each holding the
                   attributes sampled over ONE unit of time.
  2. A manifest  - a layer declaring which properties the clips supply
                   (attributes NOT in the manifest are not clip-sourced).
  3. Clip metadata on the prim - a "template" clip set naming the clip
                   asset path pattern (`sim_t###.usd`), start time, stride
                   and end time. USD expands the template into per-clip
                   asset paths and maps stage time -> (clip, local time).

This tutorial writes 5 tiny clips (temperature 20->100, pressure 1.0->1.8),
wires them with Usd.ClipsAPI, then samples the composed stage at t=0..4 and
proves the values slide through the clip sequence.

Covered APIs:
  Usd.ClipsAPI - SetClipTemplateAssetPath / SetClipTemplateStartTime /
                 SetClipTemplateEndTime / SetClipTemplateStride /
                 SetClipManifestAssetPath / SetClipPrimPath
  UsdStage timeCode range + sampled attribute reads

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/18_value_clips/18_value_clips.py
================================================================================
"""

import os

from pxr import Usd, Sdf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
USDA_PATH = os.path.join(OUTPUT_DIR, "18_value_clips.usda")

NUM_CLIPS = 5            # clip files: sim_t0000 .. sim_t0004
START_TEMP = 20.0        # temperature at clip 0
END_TEMP = 100.0         # temperature at the last clip
START_PRESSURE = 1.0     # pressure at clip 0
END_PRESSURE = 1.8       # pressure at the last clip


# ==============================================================================
# Part 1: Write the clip files + manifest
# ==============================================================================

CLIP_TEMPLATE = """\
#usda 1.0
(
    defaultPrim = "Sim"
    startTimeCode = 0
    endTimeCode = 0
    timeCodesPerSecond = 24
)

def Xform "Sim"
{
    float data:temperature.timeSamples = {
        0: %s,
    }
    float data:pressure.timeSamples = {
        0: %s,
    }
}
"""

MANIFEST = """\
#usda 1.0
(
    defaultPrim = "Sim"
)

def Xform "Sim"
{
    float data:temperature
    float data:pressure
}
"""


def write_clips():
    """Write 5 clip layers + the manifest declaring clip-sourced properties."""
    if not os.path.isdir(CLIPS_DIR):
        os.makedirs(CLIPS_DIR)

    for i in range(NUM_CLIPS):
        frac = float(i) / (NUM_CLIPS - 1)
        temp = START_TEMP + (END_TEMP - START_TEMP) * frac
        press = START_PRESSURE + (END_PRESSURE - START_PRESSURE) * frac
        body = CLIP_TEMPLATE % ("%.4f" % temp, "%.4f" % press)
        path = os.path.join(CLIPS_DIR, "sim_t.%04d.usd" % i)
        with open(path, "w") as f:
            f.write(body)

    with open(os.path.join(CLIPS_DIR, "manifest.usda"), "w") as f:
        f.write(MANIFEST)

    print("  [+] Wrote %d clip files + manifest to: %s"
          % (NUM_CLIPS, os.path.relpath(CLIPS_DIR, SCRIPT_DIR)))


# ==============================================================================
# Part 2: Build the root stage with template clip metadata
# ==============================================================================

def build_stage():
    """Author clip metadata on /Sim and save the stage."""
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(NUM_CLIPS - 1)

    sim = stage.DefinePrim("/Sim", "Xform")
    stage.SetDefaultPrim(sim)

    # The template clip set. '#' in the asset path is the zero-padded frame
    # placeholder; USD expands sim_t###.usd -> sim_t0000.usd etc. and maps
    # stage time t to clip index floor((t - startTime) / stride).
    clips = Usd.ClipsAPI(sim)
    clips.SetClipTemplateAssetPath("./clips/sim_t.####.usd")
    clips.SetClipTemplateStartTime(0.0)
    clips.SetClipTemplateEndTime(float(NUM_CLIPS - 1))
    clips.SetClipTemplateStride(1.0)
    clips.SetClipManifestAssetPath("./clips/manifest.usda")
    # Prim path of the data INSIDE each clip file (they all store /Sim).
    clips.SetClipPrimPath("/Sim")

    stage.GetRootLayer().Save()
    print("  [+] Authored template clip metadata on /Sim")
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage


# ==============================================================================
# Part 3: Sample the composed stage and verify the clip slide
# ==============================================================================

def verify_stage():
    """Reload and read clip-sourced values at every stage time."""
    print("\n--- Step 3: Sampling composed values through the clip set ---")
    stage = Usd.Stage.Open(USDA_PATH)

    temp_attr = stage.GetPrimAtPath("/Sim").GetAttribute("data:temperature")
    press_attr = stage.GetPrimAtPath("/Sim").GetAttribute("data:pressure")

    print("    %-6s %-12s %-10s" % ("time", "temperature", "pressure"))
    for t in range(int(stage.GetStartTimeCode()), int(stage.GetEndTimeCode()) + 1):
        temp = temp_attr.Get(Usd.TimeCode(t))
        press = press_attr.Get(Usd.TimeCode(t))
        print("    %-6d %-12.3f %-10.3f" % (t, temp, press))

    # The composed value at each time must match the clip written for it -
    # temperature ramps 20 -> 100 across the five clips.
    expected = [START_TEMP + (END_TEMP - START_TEMP) * i / (NUM_CLIPS - 1)
                for i in range(NUM_CLIPS)]
    for t, want in enumerate(expected):
        got = temp_attr.Get(Usd.TimeCode(t))
        assert abs(got - want) < 1e-4, "t=%d: got %s want %s" % (t, got, want)

    print("    [OK] composed values slide through all %d clips" % NUM_CLIPS)

    # Show where the value came from: ResolveInfo source is 'ValueClips'
    # for clip-sourced attributes - the LIVRPS machinery from tutorial 15
    # routes through the clip set before hitting layers.
    info = temp_attr.GetResolveInfo(Usd.TimeCode(2))
    print("    resolve info source at t=2: %s"
          % str(info.GetSource()).split(".")[-1])


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 18: Value Clips - Time-Sliced Simulation Caches")
    print("=" * 80)

    print("\n--- Step 1: Writing clip files + manifest ---")
    write_clips()

    print("\n--- Step 2: Building root stage with clip metadata ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 18 complete!")
    print("USD output: %s" % USDA_PATH)
    print("Clip files: %s" % CLIPS_DIR)
    print("=" * 80)


if __name__ == "__main__":
    main()

