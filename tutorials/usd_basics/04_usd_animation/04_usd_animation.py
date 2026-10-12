"""
================================================================================
Tutorial 04: USD Animation - Time Samples and Keyframe Animation
================================================================================

This tutorial covers:
  1. Setting up a stage with time codes (timeline)
  2. Creating keyframe animations using time samples
  3. Animating transforms (translation, rotation, scale)
  4. Animating attribute values (color, size, etc.)
  5. Reading and inspecting animated values at specific times

Key Concepts:
  - TimeCode:      A point in time on the USD timeline (measured in frames)
  - Time Sample:   A value of an attribute at a specific time code
  - Interpolation: USD automatically interpolates between time samples
                   (linear interpolation for numeric types)
  - Stage Time:    The current time being evaluated (set via UsdStage.SetTime)

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\04_usd_animation.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, Gf


# ==============================================================================
# Part 1: Setting Up the Timeline
# ==============================================================================

def setup_timeline(stage, start_frame=1, end_frame=120):
    """
    Set up the stage's timeline (start and end frames).

    USD uses a time code system measured in frames. The stage metadata
    stores the start and end time codes, which define the animation range.

    Args:
        stage (Usd.Stage): The stage to configure.
        start_frame (int): The first frame of the animation.
        end_frame (int): The last frame of the animation.

    Returns:
        Usd.Stage: The configured stage.
    """
    # Set the start and end time codes on the root layer
    # These define the animation playback range
    stage.SetStartTimeCode(start_frame)
    stage.SetEndTimeCode(end_frame)

    # Set the frames per second (FPS) for time-based playback
    # Common values: 24 (film), 30 (NTSC), 60 (smooth)
    stage.SetTimeCodesPerSecond(24.0)

    print(f"  [+] Timeline set: frames {start_frame} to {end_frame} at 24 FPS")
    return stage


# ==============================================================================
# Part 2: Animating Translation (Moving Object)
# ==============================================================================

def animate_translation(stage):
    """
    Animate a sphere moving along a path using translation keyframes.

    Time samples are set on the "xformOp:translate" attribute at different
    time codes. USD will linearly interpolate between samples.

    The sphere moves in a circular path over 120 frames.

    Args:
        stage (Usd.Stage): The stage to animate on.
    """
    import math

    # Create a sphere to animate
    sphere = UsdGeom.Sphere.Define(stage, "/World/AnimatedSphere")
    sphere.GetRadiusAttr().Set(0.5)
    sphere.GetDisplayColorAttr().Set([(1.0, 0.5, 0.0)])  # Orange

    # Get the Xformable interface to add transform operations
    xformable = UsdGeom.Xformable(sphere)

    # Add a translate operation - this returns an UsdGeom.XformOp
    # We will set time samples on this op's attribute
    translate_op = xformable.AddTranslateOp()

    # Set keyframes at various frames
    # The sphere moves in a circle of radius 5.0
    # We sample at 8 positions around the circle (every 15 frames)
    num_keyframes = 8
    total_frames = 120

    for i in range(num_keyframes + 1):
        frame = int(i * total_frames / num_keyframes)
        angle = 2 * math.pi * i / num_keyframes

        # Compute position on the circle
        x = 5.0 * math.cos(angle)
        z = 5.0 * math.sin(angle)

        # Set a time sample at this frame
        # Set(value, time) stores the value at the given time code
        translate_op.Set(Gf.Vec3d(x, 0.0, z), frame)

    print(f"  [+] Animated sphere: circular path, {num_keyframes + 1} keyframes over {total_frames} frames")


# ==============================================================================
# Part 3: Animating Rotation (Spinning Object)
# ==============================================================================

def animate_rotation(stage):
    """
    Animate a cube spinning around the Y axis.

    Rotation animation is set by providing time samples on a rotate op.
    The rotation value is in degrees.

    Args:
        stage (Usd.Stage): The stage to animate on.
    """
    # Create a cube to spin
    cube = UsdGeom.Cube.Define(stage, "/World/SpinningCube")
    cube.GetSizeAttr().Set(2.0)
    cube.GetDisplayColorAttr().Set([(0.0, 1.0, 1.0)])  # Cyan

    # Position it above the ground
    xformable = UsdGeom.Xformable(cube)
    translate_op = xformable.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(0.0, 3.0, 0.0))

    # Add a rotation operation around the Y axis
    rotate_op = xformable.AddRotateYOp()

    # Set keyframes: rotate 0 -> 360 degrees over 120 frames
    # We set samples at 0, 30, 60, 90, 120 frames
    keyframes = [
        (1,   0.0),     # Frame 1:   0 degrees
        (30,  90.0),    # Frame 30:  90 degrees
        (60,  180.0),   # Frame 60:  180 degrees
        (90,  270.0),   # Frame 90:  270 degrees
        (120, 360.0),   # Frame 120: 360 degrees (full rotation)
    ]

    for frame, angle in keyframes:
        rotate_op.Set(angle, frame)

    print(f"  [+] Spinning cube: 360deg rotation over 120 frames, {len(keyframes)} keyframes")


# ==============================================================================
# Part 4: Animating Scale (Pulsing Object)
# ==============================================================================

def animate_scale(stage):
    """
    Animate a sphere pulsing (scaling up and down).

    Scale animation uses time samples on a scale operation.
    The sphere scales between 0.5x and 2.0x repeatedly.

    Args:
        stage (Usd.Stage): The stage to animate on.
    """
    # Create a sphere to pulse
    sphere = UsdGeom.Sphere.Define(stage, "/World/PulsingSphere")
    sphere.GetRadiusAttr().Set(1.0)
    sphere.GetDisplayColorAttr().Set([(0.8, 0.0, 0.8)])  # Magenta

    # Position it to the side
    xformable = UsdGeom.Xformable(sphere)
    xformable.AddTranslateOp().Set(Gf.Vec3d(-5.0, 0.0, 0.0))

    # Add a scale operation
    scale_op = xformable.AddScaleOp()

    # Set keyframes: pulse between 0.5x and 2.0x
    # We use a sine-like pattern with explicit keyframes
    keyframes = [
        (1,   Gf.Vec3f(0.5, 0.5, 0.5)),   # Small
        (15,  Gf.Vec3f(2.0, 2.0, 2.0)),   # Large
        (30,  Gf.Vec3f(0.5, 0.5, 0.5)),   # Small
        (45,  Gf.Vec3f(2.0, 2.0, 2.0)),   # Large
        (60,  Gf.Vec3f(0.5, 0.5, 0.5)),   # Small
        (75,  Gf.Vec3f(2.0, 2.0, 2.0)),   # Large
        (90,  Gf.Vec3f(0.5, 0.5, 0.5)),   # Small
        (105, Gf.Vec3f(2.0, 2.0, 2.0)),   # Large
        (120, Gf.Vec3f(0.5, 0.5, 0.5)),   # Small
    ]

    for frame, scale in keyframes:
        scale_op.Set(scale, frame)

    print(f"  [+] Pulsing sphere: scale 0.5x <-> 2.0x, {len(keyframes)} keyframes")


# ==============================================================================
# Part 5: Animating Attributes (Color Change)
# ==============================================================================

def animate_color(stage):
    """
    Animate the display color of a cube changing over time.

    Any attribute can be animated in USD, not just transforms.
    Here we animate the "primvars:displayColor" attribute to cycle
    through colors over time.

    Args:
        stage (Usd.Stage): The stage to animate on.
    """
    # Create a cube
    cube = UsdGeom.Cube.Define(stage, "/World/ColorChangingCube")
    cube.GetSizeAttr().Set(1.5)

    # Position it
    UsdGeom.Xformable(cube).AddTranslateOp().Set(Gf.Vec3d(5.0, 0.0, 0.0))

    # Get the display color attribute
    color_attr = cube.GetDisplayColorAttr()

    # Set color keyframes: cycle through red, green, blue, yellow, magenta
    color_keyframes = [
        (1,   [(1.0, 0.0, 0.0)]),  # Red
        (30,  [(0.0, 1.0, 0.0)]),  # Green
        (60,  [(0.0, 0.0, 1.0)]),  # Blue
        (90,  [(1.0, 1.0, 0.0)]),  # Yellow
        (120, [(1.0, 0.0, 0.0)]),  # Back to Red
    ]

    for frame, color in color_keyframes:
        color_attr.Set(color, frame)

    print(f"  [+] Color-changing cube: 5 color keyframes over 120 frames")


# ==============================================================================
# Part 6: Reading Animated Values at Specific Times
# ==============================================================================

def read_animated_values(stage):
    """
    Read and display animated attribute values at specific time codes.

    This demonstrates how USD interpolates between time samples.
    We query the animated sphere's position at several frames to see
    the interpolated values.

    Args:
        stage (Usd.Stage): The stage to query.
    """
    print("\n--- Reading Animated Values ---")

    # Get the animated sphere's translate op
    sphere_prim = stage.GetPrimAtPath("/World/AnimatedSphere")
    xformable = UsdGeom.Xformable(sphere_prim)

    # Get the translate op (first op in the stack)
    translate_op = xformable.GetOrderedXformOps()[0]

    # Query the position at various frames
    # USD will interpolate between the keyframes we set
    query_frames = [1, 15, 30, 45, 60, 75, 90, 105, 120]

    print(f"  Animated Sphere position at various frames:")
    for frame in query_frames:
        # Get the value at the specified time code
        # If the time falls between keyframes, USD interpolates linearly
        value = translate_op.Get(frame)
        if value:
            print(f"    Frame {frame:3d}: ({value[0]:.2f}, {value[1]:.2f}, {value[2]:.2f})")

    # Also query the spinning cube's rotation
    print(f"\n  Spinning Cube rotation at various frames:")
    cube_prim = stage.GetPrimAtPath("/World/SpinningCube")
    cube_xform = UsdGeom.Xformable(cube_prim)
    cube_ops = cube_xform.GetOrderedXformOps()

    # Find the rotateY op (second op, after translate)
    for op in cube_ops:
        if op.GetOpType() == UsdGeom.XformOp.TypeRotateY:
            for frame in [1, 15, 30, 45, 60, 90, 120]:
                value = op.Get(frame)
                print(f"    Frame {frame:3d}: Y rotation = {value:.1f} degrees")
            break


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 04: USD Animation - Time Samples and Keyframe Animation")
    print("=" * 80)

    # Define output path
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "output", "04_usd_animation.usda")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create stage
    stage = Usd.Stage.CreateNew(output_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Set default prim
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Step 1: Set up timeline
    print("\n--- Step 1: Setting Up Timeline ---")
    setup_timeline(stage)

    # Step 2: Animate translation
    print("\n--- Step 2: Animating Translation ---")
    animate_translation(stage)

    # Step 3: Animate rotation
    print("\n--- Step 3: Animating Rotation ---")
    animate_rotation(stage)

    # Step 4: Animate scale
    print("\n--- Step 4: Animating Scale ---")
    animate_scale(stage)

    # Step 5: Animate color
    print("\n--- Step 5: Animating Color ---")
    animate_color(stage)

    # Step 6: Read animated values
    read_animated_values(stage)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Tutorial 04 complete!")
    print(f"Output file: {output_file}")
    print("Open the .usda file to see time samples in the USD format.")
    print("=" * 80)


if __name__ == "__main__":
    main()
