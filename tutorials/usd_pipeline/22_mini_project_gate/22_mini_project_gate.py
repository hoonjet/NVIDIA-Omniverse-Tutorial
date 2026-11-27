#!/usr/bin/env python
"""
================================================================================
Tutorial 22: Mini Project - Proximity Gate (One Asset, One Rule, One Sensor)
================================================================================

The second mini project in the finale: the smallest project that actually
runs, built around a DISTANCE sensor this time.

    ONE ASSET      /World/Gate         Frame + Slider (a sliding warehouse gate)
    ONE RULE       /World/Gate/Rail    PrismaticJoint + DriveAPI linear servo
                                       (the gate slides open when the sensor
                                       reports something close)
    ONE SENSOR     /World/ProximitySensor  distance readings time-sliced with
                                       VALUE CLIPS

The rule: slider target = 6 scene units (fully open) when distance < 2.0,
0 (closed) otherwise. The servo targets are authored as time samples derived
from the sensor clip readings, so a PhysX runtime slides the gate and a plain
USD viewer scrubs the whole sequence t=0..3.

Covered APIs:
    UsdPhysics.Scene / RigidBodyAPI (kinematic + dynamic) / CollisionAPI /
    PrismaticJoint / DriveAPI (linear position servo with time samples)
    Value clips: template clip set + manifest (sensor readings)

Run:
    cd E:/omniverse_env
    Scripts/activate
    python tutorials/usd_pipeline/22_mini_project_gate/22_mini_project_gate.py
================================================================================
"""

import os

from pxr import Usd, UsdPhysics, UsdGeom, Sdf, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
USDA_PATH = os.path.join(OUTPUT_DIR, "22_mini_project_gate.usda")

NUM_CLIPS = 4                              # time codes t = 0 .. 3
SENSOR_DISTANCES = [5.0, 3.0, 1.2, 0.4]    # scene units, one reading per clip
OPEN_DISTANCE = 2.0                        # rule: open when closer than this
OPEN_POSITION = 6.0                        # rule: slider target when open
RAIL_AXIS = "X"                            # slide along world X


# ==============================================================================
# Part 1: The sensor cache - value clips of distance readings
# ==============================================================================

def write_sensor_clips():
    """One tiny clip file per time code holding the distance reading.

    NOTE: clip prims use the SAME path as the stage prim
    (/World/ProximitySensor) - this build's clips machinery maps clips by
    identical paths, and the manifest must declare the attribute too.
    """
    if not os.path.isdir(CLIPS_DIR):
        os.makedirs(CLIPS_DIR)

    for i, dist in enumerate(SENSOR_DISTANCES):
        path = os.path.join(CLIPS_DIR, "sim_t.%04d.usd" % i)
        with open(path, "w") as f:
            f.write(
                "#usda 1.0\n"
                "(\n"
                "    defaultPrim = \"World\"\n"
                "    startTimeCode = %d\n"
                "    endTimeCode = %d\n"
                ")\n"
                "\n"
                "def Xform \"World\"\n"
                "{\n"
                "    def Xform \"ProximitySensor\"\n"
                "    {\n"
                "        custom float data:distance.timeSamples = {\n"
                "            %d: %.4f,\n"
                "        }\n"
                "    }\n"
                "}\n" % (i, i, i, dist))

    with open(os.path.join(CLIPS_DIR, "manifest.usda"), "w") as f:
        f.write(
            "#usda 1.0\n"
            "(\n"
            "    defaultPrim = \"World\"\n"
            ")\n"
            "\n"
            "def Xform \"World\"\n"
            "{\n"
            "    def Xform \"ProximitySensor\"\n"
            "    {\n"
            "        custom float data:distance\n"
            "    }\n"
            "}\n")
    print("  [Sensor] %d distance clips written to clips/ (%s)"
          % (NUM_CLIPS, SENSOR_DISTANCES))


def slider_target(distance):
    """THE RULE: map a distance reading to a slider target position.

    Fully open (OPEN_POSITION) when something is closer than OPEN_DISTANCE,
    closed (0) otherwise.
    """
    return OPEN_POSITION if distance < OPEN_DISTANCE else 0.0


# ==============================================================================
# Part 2: The asset + the physics rule
# ==============================================================================

def build_stage():
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)
    stage.SetStartTimeCode(0)
    stage.SetEndTimeCode(NUM_CLIPS - 1)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    scene = UsdPhysics.Scene.Define(stage, "/World/PhysicsScene")
    scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, -1.0, 0.0))
    scene.CreateGravityMagnitudeAttr().Set(981.0)

    # ---------------------------------------------------------------- ONE ASSET
    # The gate: an anchored frame and a sliding panel. Two prims.
    frame = UsdGeom.Cube.Define(stage, "/World/Gate/Frame")
    frame.GetSizeAttr().Set(0.3)
    frame.AddTranslateOp().Set(Gf.Vec3d(-3.0, 1.0, 0.0))
    frame_prim = frame.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(frame_prim)
    UsdPhysics.CollisionAPI.Apply(frame_prim)
    UsdPhysics.RigidBodyAPI(frame_prim).CreateKinematicEnabledAttr().Set(True)

    slider = UsdGeom.Cube.Define(stage, "/World/Gate/Slider")
    slider.GetSizeAttr().Set(6.0)
    slider.AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 0.0))
    slider_prim = slider.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(slider_prim)
    UsdPhysics.CollisionAPI.Apply(slider_prim)
    UsdPhysics.MassAPI.Apply(slider_prim)
    UsdPhysics.MassAPI(slider_prim).CreateMassAttr().Set(20.0)
    print("  [Asset] /World/Gate (Frame + Slider)")

    # ------------------------------------------------------------- ONE RULE
    # The rail servo: prismatic joint with a linear position drive. Target
    # TIME SAMPLES are the sensor rule (open when something is close).
    rail = UsdPhysics.PrismaticJoint.Define(stage, "/World/Gate/Rail")
    rail.CreateBody0Rel().SetTargets(["/World/Gate/Frame"])
    rail.CreateBody1Rel().SetTargets(["/World/Gate/Slider"])
    rail.CreateAxisAttr(RAIL_AXIS)
    rail.CreateLocalPos0Attr().Set(Gf.Vec3f(3.0, 0.0, 0.0))
    rail.CreateLocalPos1Attr().Set(Gf.Vec3f(-3.0, 0.0, 0.0))
    rail.CreateLowerLimitAttr().Set(0.0)
    rail.CreateUpperLimitAttr().Set(OPEN_POSITION)
    UsdPhysics.DriveAPI.Apply(rail.GetPrim(), "linear")
    drive = UsdPhysics.DriveAPI(rail.GetPrim(), "linear")
    drive.CreateTypeAttr().Set("linear")
    drive.CreateMaxForceAttr().Set(1000.0)
    drive.CreateStiffnessAttr().Set(500.0)
    drive.CreateDampingAttr().Set(30.0)
    target = drive.CreateTargetPositionAttr()
    for i, dist in enumerate(SENSOR_DISTANCES):
        target.Set(slider_target(dist), Usd.TimeCode(i))
    print("  [Rule] Rail servo: %d target samples from the distance rule"
          % NUM_CLIPS)

    # ------------------------------------------------------------ ONE SENSOR
    sensor = UsdGeom.Sphere.Define(stage, "/World/ProximitySensor")
    sensor.GetRadiusAttr().Set(0.2)
    sensor.AddTranslateOp().Set(Gf.Vec3d(3.5, 1.0, 0.0))
    sensor_prim = sensor.GetPrim()
    sensor_prim.CreateAttribute("data:distance", Sdf.ValueTypeNames.Float)
    sensor_prim.CreateRelationship("sensor:mountedOn").SetTargets(
        ["/World/Gate/Frame"])

    clipsapi = Usd.ClipsAPI(sensor_prim)
    clipsapi.SetClipManifestAssetPath(
        Sdf.AssetPath("./clips/manifest.usda"), "default")
    clipsapi.SetClipTemplateAssetPath("./clips/sim_t.####.usd", "default")
    clipsapi.SetClipPrimPath("/World/ProximitySensor", "default")
    clipsapi.SetClipTemplateStartTime(0.0, "default")
    clipsapi.SetClipTemplateEndTime(float(NUM_CLIPS - 1), "default")
    clipsapi.SetClipTemplateStride(1.0, "default")
    print("  [Sensor] /World/ProximitySensor bound to value clips")

    stage.GetRootLayer().Save()
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage


# ==============================================================================
# Part 3: Reload and verify - sensor readings drive the servo rule
# ==============================================================================

def verify_stage():
    print("\n--- Step 3: Reloading and verifying ---")
    stage = Usd.Stage.Open(USDA_PATH)

    scene = UsdPhysics.Scene(stage.GetPrimAtPath("/World/PhysicsScene"))
    slider = stage.GetPrimAtPath("/World/Gate/Slider")
    rail = stage.GetPrimAtPath("/World/Gate/Rail")
    sensor = stage.GetPrimAtPath("/World/ProximitySensor")

    assert scene.GetPrim().IsValid(), "PhysicsScene missing"
    assert slider.IsValid() and rail.IsValid(), "gate asset incomplete"
    assert sensor.IsValid(), "sensor prim missing"

    frame_rb = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/World/Gate/Frame"))
    assert frame_rb.GetKinematicEnabledAttr().Get() is True, "Frame not kinematic"
    assert slider.HasAPI(UsdPhysics.CollisionAPI), "Slider not collidable"
    print("    frame kinematic       : %s" % frame_rb.GetKinematicEnabledAttr().Get())

    # The rule: recomputed servo targets must match the authored samples.
    drive = UsdPhysics.DriveAPI(rail, "linear")
    target = drive.GetTargetPositionAttr()
    distances = sensor.GetAttribute("data:distance")
    for i in range(NUM_CLIPS):
        reading = distances.Get(i)
        authored = target.Get(i)
        expected = slider_target(reading)
        assert abs(authored - expected) < 1e-4, \
            "t=%d: target %s != rule %s" % (i, authored, expected)
        print("    t=%d: sensor %.1f -> slider %.1f" % (i, reading, authored))

    limits = (rail.GetAttribute("physics:lowerLimit").Get(),
              rail.GetAttribute("physics:upperLimit").Get())
    axis = rail.GetAttribute("physics:axis").Get()
    print("    rail axis/limits      : %s %s" % (axis, limits))
    assert axis == RAIL_AXIS, "unexpected rail axis"
    assert limits == (0.0, OPEN_POSITION), "unexpected rail limits"

    # The sensor: readings must resolve through VALUE CLIPS.
    info = distances.GetResolveInfo(Usd.TimeCode(2))
    assert info.GetSource() == Usd.ResolveInfoSourceValueClips, \
        "sensor reading did not come from clips: %s" % info.GetSource()
    print("    readings source       : %s" % info.GetSource())
    print("    [OK] mini project verification passed")


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 22: Mini Project - Proximity Gate")
    print("=" * 80)

    print("\n--- Step 1: Writing sensor clips (the sensor's data stream) ---")
    write_sensor_clips()

    print("\n--- Step 2: Building the asset + the physics rule ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 22 complete!")
    print("One asset (/World/Gate) + one rule (Rail linear servo) + one sensor")
    print("(/World/ProximitySensor, value clips). Scrub t=0..3 in USDView, or")
    print("drop the stage into Omniverse Composer and PhysX slides the gate.")
    print("USD output: %s" % USDA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()
