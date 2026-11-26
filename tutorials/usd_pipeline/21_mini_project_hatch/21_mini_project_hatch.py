#!/usr/bin/env python
"""
================================================================================
Tutorial 21: Mini Project - Servo-Driven Dryer Hatch (One Asset, One Rule,
             One Sensor)
================================================================================

The grand finale of the series: the SMALLEST project that actually runs.
Everything the previous tutorials taught is compressed into three parts:

    ONE ASSET      /World/Hatch        Frame + Door (a dryer-style hatch)
    ONE RULE       /World/Hatch/Hinge  RevoluteJoint + DriveAPI position servo
                                       (the door swings open when the sensor
                                       reports a hot load)
    ONE SENSOR     /World/Sensor       TemperatureSensor whose data:temperature
                                       reading is time-sliced with VALUE CLIPS

The rule is pure USD wiring, no code in the stage: the servo target position
is authored as time samples DERIVED from the sensor readings
(angle = clamp((T - 60C) / 25C) * 110 deg). Load the stage in Omniverse
Composer and the PhysX solver swings the door open as time advances; in a
plain USD viewer you can scrub t=0..3 and watch both the sensor readings and
the servo targets slide.

Covered APIs:
    UsdPhysics.Scene / RigidBodyAPI (kinematic + dynamic) / CollisionAPI /
    RevoluteJoint / DriveAPI (position servo with time samples)
    Value clips: template clip set + manifest (sensor readings)

Run:
    cd E:/omniverse_env
    Scripts/activate
    python tutorials/usd_pipeline/21_mini_project_hatch/21_mini_project_hatch.py
================================================================================
"""

import os

from pxr import Usd, UsdPhysics, UsdGeom, Sdf, Gf

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
CLIPS_DIR = os.path.join(OUTPUT_DIR, "clips")
USDA_PATH = os.path.join(OUTPUT_DIR, "21_mini_project_hatch.usda")

NUM_CLIPS = 4                             # time codes t = 0 .. 3
SENSOR_TEMPS = [40.0, 55.0, 70.0, 85.0]   # degrees C, one reading per clip
TEMP_OPEN = 60.0                          # rule: door opens above this temp
TEMP_FULL = 85.0                          # rule: fully open at this temp
OPEN_ANGLE = 110.0                        # max servo angle (degrees)


# ==============================================================================
# Part 1: The sensor cache - value clips of temperature readings
# ==============================================================================

def write_sensor_clips():
    """One tiny clip file per time code holding the sensor reading.

    Same pattern as tutorial 18: a manifest declares the attributes, and each
    clip carries ONE time sample of data:temperature. This IS the sensor's
    data stream - a real simulator or IoT feed would write these files.
    """
    if not os.path.isdir(CLIPS_DIR):
        os.makedirs(CLIPS_DIR)

    for i, temp in enumerate(SENSOR_TEMPS):
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
                "    def Xform \"Sensor\"\n"
                "    {\n"
                "        custom float data:temperature.timeSamples = {\n"
                "            %d: %.4f,\n"
                "        }\n"
                "    }\n"
                "}\n" % (i, i, i, temp))

    with open(os.path.join(CLIPS_DIR, "manifest.usda"), "w") as f:
        f.write(
            "#usda 1.0\n"
            "(\n"
            "    defaultPrim = \"World\"\n"
            ")\n"
            "\n"
            "def Xform \"World\"\n"
            "{\n"
            "    def Xform \"Sensor\"\n"
            "    {\n"
            "        custom float data:temperature\n"
            "    }\n"
            "}\n")
    print("  [Sensor] %d temperature clips written to clips/ (%s C)"
          % (NUM_CLIPS, SENSOR_TEMPS))


def sensor_angle(temperature):
    """THE RULE: map a sensor reading to a servo target angle (degrees).

    0 deg (closed) below TEMP_OPEN, OPEN_ANGLE deg at TEMP_FULL and above,
    linear in between.
    """
    t = (temperature - TEMP_OPEN) / (TEMP_FULL - TEMP_OPEN)
    return max(0.0, min(1.0, t)) * OPEN_ANGLE


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
    scene.CreateGravityMagnitudeAttr().Set(981.0)   # 9.81 m/s^2 at 0.01 scale

    # ---------------------------------------------------------------- ONE ASSET
    # The hatch: an anchored frame and a hinged door. Two prims - that is the
    # whole asset.
    frame = UsdGeom.Cube.Define(stage, "/World/Hatch/Frame")
    frame.GetSizeAttr().Set(4.0)
    frame.AddTranslateOp().Set(Gf.Vec3d(0.0, 2.0, 0.0))
    frame_prim = frame.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(frame_prim)
    UsdPhysics.CollisionAPI.Apply(frame_prim)
    UsdPhysics.RigidBodyAPI(frame_prim).CreateKinematicEnabledAttr().Set(True)

    door = UsdGeom.Cube.Define(stage, "/World/Hatch/Door")
    door.GetSizeAttr().Set(3.8)
    door.AddTranslateOp().Set(Gf.Vec3d(0.0, 2.0, 2.0))
    door_prim = door.GetPrim()
    UsdPhysics.RigidBodyAPI.Apply(door_prim)
    UsdPhysics.CollisionAPI.Apply(door_prim)
    UsdPhysics.MassAPI.Apply(door_prim)
    UsdPhysics.MassAPI(door_prim).CreateMassAttr().Set(1.5)
    print("  [Asset] /World/Hatch (Frame + Door)")

    # ------------------------------------------------------------- ONE RULE
    # The hinge servo: target position TIME SAMPLES are the sensor rule.
    # When PhysX runs the stage, the servo drives the door along this curve.
    hinge = UsdPhysics.RevoluteJoint.Define(stage, "/World/Hatch/Hinge")
    hinge.CreateBody0Rel().SetTargets(["/World/Hatch/Frame"])
    hinge.CreateBody1Rel().SetTargets(["/World/Hatch/Door"])
    hinge.CreateAxisAttr("X")
    hinge.CreateLocalPos0Attr().Set(Gf.Vec3f(0.0, 0.0, -2.0))
    hinge.CreateLocalPos1Attr().Set(Gf.Vec3f(0.0, 0.0, -1.9))
    hinge.CreateLowerLimitAttr().Set(0.0)
    hinge.CreateUpperLimitAttr().Set(OPEN_ANGLE)
    UsdPhysics.DriveAPI.Apply(hinge.GetPrim(), "angular")
    drive = UsdPhysics.DriveAPI(hinge.GetPrim(), "angular")
    drive.CreateTypeAttr().Set("angular")
    drive.CreateMaxForceAttr().Set(500.0)
    drive.CreateStiffnessAttr().Set(200.0)
    drive.CreateDampingAttr().Set(10.0)
    target = drive.CreateTargetPositionAttr()
    for i, temp in enumerate(SENSOR_TEMPS):
        target.Set(sensor_angle(temp), Usd.TimeCode(i))
    print("  [Rule] Hinge servo: %d target samples from the temperature rule"
          % NUM_CLIPS)

    # ------------------------------------------------------------ ONE SENSOR
    # The sensor prim in the main stage. No reading authored here - it comes
    # from the clips via the template clip set below.
    sensor = UsdGeom.Xform.Define(stage, "/World/Sensor")
    sensor.AddTranslateOp().Set(Gf.Vec3d(2.2, 0.5, 2.2))
    sensor_prim = sensor.GetPrim()
    sensor_prim.CreateAttribute("data:temperature",
                                Sdf.ValueTypeNames.Float)   # declared only
    sensor_prim.CreateRelationship("sensor:mountedOn").SetTargets(
        ["/World/Hatch/Frame"])

    layer = stage.GetRootLayer()
    clipsapi = Usd.ClipsAPI(sensor_prim)
    clipsapi.SetClipManifestAssetPath(
        Sdf.AssetPath("./clips/manifest.usda"), "default")
    clipsapi.SetClipTemplateAssetPath("./clips/sim_t.####.usd", "default")
    clipsapi.SetClipPrimPath("/World/Sensor", "default")
    clipsapi.SetClipTemplateStartTime(0.0, "default")
    clipsapi.SetClipTemplateEndTime(float(NUM_CLIPS - 1), "default")
    clipsapi.SetClipTemplateStride(1.0, "default")
    print("  [Sensor] /World/Sensor bound to value clips (manifest + template)")

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
    gravity = scene.GetGravityMagnitudeAttr().Get()
    print("    scene gravity        : %s" % gravity)

    door = stage.GetPrimAtPath("/World/Hatch/Door")
    hinge = stage.GetPrimAtPath("/World/Hatch/Hinge")
    sensor = stage.GetPrimAtPath("/World/Sensor")

    assert scene.GetPrim().IsValid(), "PhysicsScene missing"
    assert door.IsValid() and hinge.IsValid(), "hatch asset incomplete"
    assert sensor.IsValid(), "sensor prim missing"

    # The asset: frame anchored, door dynamic and collidable.
    frame_rb = UsdPhysics.RigidBodyAPI(stage.GetPrimAtPath("/World/Hatch/Frame"))
    assert frame_rb.GetKinematicEnabledAttr().Get() is True, "Frame not kinematic"
    assert door.HasAPI(UsdPhysics.CollisionAPI), "Door not collidable"
    print("    frame kinematic       : %s" % frame_rb.GetKinematicEnabledAttr().Get())

    # The rule: servo targets on disk must equal the rule applied to the
    # sensor readings - recompute and compare sample by sample.
    drive = UsdPhysics.DriveAPI(hinge, "angular")
    target = drive.GetTargetPositionAttr()
    temps = sensor.GetAttribute("data:temperature")
    for i in range(NUM_CLIPS):
        reading = temps.Get(i)
        authored = target.Get(i)
        expected = sensor_angle(reading)
        assert abs(authored - expected) < 1e-4, \
            "t=%d: target %s != rule %s" % (i, authored, expected)
        print("    t=%d: sensor %.1f C -> servo %.1f deg" % (i, reading, authored))

    limits = (hinge.GetAttribute("physics:lowerLimit").Get(),
              hinge.GetAttribute("physics:upperLimit").Get())
    print("    hinge limits          : %s" % (limits,))
    assert limits == (0.0, OPEN_ANGLE), "unexpected hinge limits"

    # The sensor: readings must resolve through VALUE CLIPS.
    info = temps.GetResolveInfo(Usd.TimeCode(2))
    assert info.GetSource() == Usd.ResolveInfoSourceValueClips, \
        "sensor reading did not come from clips: %s" % info.GetSource()
    print("    readings source       : %s" % info.GetSource())
    print("    [OK] mini project verification passed")


# ==============================================================================
# Main entry point
# ==============================================================================

def main():
    print("=" * 80)
    print("Tutorial 21: Mini Project - Servo-Driven Dryer Hatch")
    print("=" * 80)

    print("\n--- Step 1: Writing sensor clips (the sensor's data stream) ---")
    write_sensor_clips()

    print("\n--- Step 2: Building the asset + the physics rule ---")
    build_stage()

    verify_stage()

    print("\n" + "=" * 80)
    print("Tutorial 21 complete!")
    print("One asset (/World/Hatch) + one rule (Hinge servo) + one sensor")
    print("(/World/Sensor, value clips). Scrub t=0..3 in USDView, or drop the")
    print("stage into Omniverse Composer and PhysX swings the door open.")
    print("USD output: %s" % USDA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()
