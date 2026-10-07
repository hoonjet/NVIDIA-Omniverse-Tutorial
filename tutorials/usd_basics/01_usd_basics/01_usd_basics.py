"""
================================================================================
Tutorial 01: USD Basics - Stage, Prim, and Attribute
================================================================================

This tutorial covers the fundamental building blocks of USD (Universal Scene
Description):

  1. Creating a USD Stage (the root container for a USD scene)
  2. Creating Prims (scene objects/primitives)
  3. Setting Attributes (properties on prims, e.g. size, color)
  4. Saving a USD file to disk
  5. Loading and traversing a USD file

Key Concepts:
  - Stage:    The top-level container. Think of it as a "scene file".
  - Prim:     A single object in the scene (cube, sphere, camera, etc.).
  - Attribute: A property of a prim (e.g. "size" on a cube, "radius" on a sphere).
  - Schema:   A predefined type that defines what attributes a prim can have
              (e.g. "Cube", "Sphere", "Xform").

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\01_usd_basics.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, Sdf


# ==============================================================================
# Part 1: Creating a New USD Stage
# ==============================================================================

def create_stage(filepath):
    """
    Create a new USD Stage and save it to a .usda file.

    A Stage is the root container for a USD scene. It holds all the prims
    (objects) and their relationships. We use .usda format (ASCII text) so
    the file is human-readable for learning purposes.

    Args:
        filepath (str): Path where the USD file will be saved.

    Returns:
        Usd.Stage: The newly created stage object.
    """
    # Create a new in-memory stage with a default prim named "World"
    # The 'upAxis' is set to Y (standard for most 3D applications)
    # The 'metersPerUnit' is set to 0.01 (centimeters), common in Omniverse
    stage = Usd.Stage.CreateNew(filepath)

    # Set the default prim (the root prim that will be loaded when the file
    # is referenced by another file). We create an Xform prim named "World".
    world_prim = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world_prim.GetPrim())

    # Set stage metadata: up axis and unit
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)  # 1 unit = 1 cm

    print(f"[OK] Stage created: {filepath}")
    return stage


# ==============================================================================
# Part 2: Creating Prims (Scene Objects)
# ==============================================================================

def create_prims(stage):
    """
    Create several prims on the stage to demonstrate different USD schema types.

    A "Prim" (primitive) is the basic unit of a USD scene. Each prim has:
      - A path (e.g. "/World/Cube1") that uniquely identifies it
      - A type (schema) that determines what attributes it can have
      - Attributes (properties like size, color, position)

    We create:
      1. A Cube prim
      2. A Sphere prim
      3. A Cylinder prim
      4. A Camera prim

    Args:
        stage (Usd.Stage): The stage to add prims to.
    """
    # --- Create a Cube ---
    # UsdGeom.Cube.Define() creates a cube prim at the given path.
    # The path must start with "/" and be hierarchical (e.g. /World/Cube1).
    cube_path = "/World/Cube1"
    cube = UsdGeom.Cube.Define(stage, cube_path)

    # Set the size attribute (edge length in stage units)
    # GetSizeAttr() returns the size attribute; we set its value with .Set()
    cube.GetSizeAttr().Set(2.0)  # 2cm cube

    # Set the display color (RGBA - red, green, blue, alpha)
    # The color is specified as a tuple of floats in range [0.0, 1.0]
    cube.GetDisplayColorAttr().Set([(1.0, 0.0, 0.0)])  # Red

    print(f"  [+] Created Cube at {cube_path}, size=2.0, color=red")

    # --- Create a Sphere ---
    sphere_path = "/World/Sphere1"
    sphere = UsdGeom.Sphere.Define(stage, sphere_path)

    # Set the radius attribute
    sphere.GetRadiusAttr().Set(1.5)  # 1.5cm radius
    sphere.GetDisplayColorAttr().Set([(0.0, 1.0, 0.0)])  # Green

    print(f"  [+] Created Sphere at {sphere_path}, radius=1.5, color=green")

    # --- Create a Cylinder ---
    cylinder_path = "/World/Cylinder1"
    cylinder = UsdGeom.Cylinder.Define(stage, cylinder_path)

    # Set height and radius attributes
    cylinder.GetHeightAttr().Set(3.0)   # 3cm tall
    cylinder.GetRadiusAttr().Set(0.5)   # 0.5cm radius
    cylinder.GetDisplayColorAttr().Set([(0.0, 0.0, 1.0)])  # Blue

    print(f"  [+] Created Cylinder at {cylinder_path}, height=3.0, radius=0.5, color=blue")

    # --- Create a Camera ---
    # Cameras are prims too! They define the viewpoint for rendering.
    camera_path = "/World/Camera1"
    camera = UsdGeom.Camera.Define(stage, camera_path)

    # Set the focal length (in mm)
    camera.GetFocalLengthAttr().Set(50.0)

    print(f"  [+] Created Camera at {camera_path}, focalLength=50.0")


# ==============================================================================
# Part 3: Setting and Reading Attributes
# ==============================================================================

def demonstrate_attributes(stage):
    """
    Demonstrate how to read and modify attributes on existing prims.

    Attributes are the properties of a prim. Each attribute has:
      - A name (e.g. "size", "radius")
      - A type (e.g. float, double, color3f)
      - A value (which can vary over time for animation)

    This function shows how to:
      1. Get a prim by its path
      2. Read an attribute value
      3. Modify an attribute value
      4. List all attributes on a prim

    Args:
        stage (Usd.Stage): The stage containing the prims.
    """
    print("\n--- Attribute Demonstration ---")

    # Get the cube prim by its path
    cube_prim = stage.GetPrimAtPath("/World/Cube1")

    # Check if the prim is valid (exists on the stage)
    if not cube_prim.IsValid():
        print("  [ERROR] Cube prim not found!")
        return

    # Read the "size" attribute
    size_attr = cube_prim.GetAttribute("size")
    current_size = size_attr.Get()
    print(f"  Cube current size: {current_size}")

    # Modify the size attribute
    size_attr.Set(5.0)
    print(f"  Cube size updated to: {size_attr.Get()}")

    # List ALL attributes on the cube prim
    print(f"  All attributes on Cube1:")
    for attr in cube_prim.GetAttributes():
        value = attr.Get()
        print(f"    - {attr.GetName()}: {value}")


# ==============================================================================
# Part 4: Saving and Loading USD Files
# ==============================================================================

def save_and_reload(filepath):
    """
    Save the stage to disk, then reload it to verify the data persists.

    USD files can be saved in several formats:
      - .usda  : ASCII text (human-readable, good for learning)
      - .usdc  : Binary (compact, faster loading)
      - .usd   : Can be either (USD auto-detects)

    Args:
        filepath (str): Path to the USD file.
    """
    # Load the file we saved earlier
    stage = Usd.Stage.Open(filepath)

    print(f"\n--- Reloading {filepath} ---")

    # Traverse all prims in the stage
    # TraverseAll() visits every prim in depth-first order
    for prim in stage.TraverseAll():
        prim_type = prim.GetTypeName()  # e.g. "Cube", "Sphere", "Xform"
        prim_path = prim.GetPath()
        print(f"  Prim: {prim_path} (type: {prim_type})")

        # For each prim, print its attributes
        for attr in prim.GetAttributes():
            value = attr.Get()
            if value is not None:
                print(f"    -> {attr.GetName()} = {value}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 01: USD Basics - Stage, Prim, and Attribute")
    print("=" * 80)

    # Define the output file path
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "output", "01_usd_basics.usda")

    # Create output directory if it doesn't exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Step 1: Create a new stage
    print("\n--- Step 1: Creating Stage ---")
    stage = create_stage(output_file)

    # Step 2: Create prims (objects)
    print("\n--- Step 2: Creating Prims ---")
    create_prims(stage)

    # Step 3: Demonstrate attribute operations
    demonstrate_attributes(stage)

    # Step 4: Save the stage to disk
    print(f"\n--- Step 3: Saving Stage ---")
    stage.GetRootLayer().Save()
    print(f"  [OK] Stage saved to: {output_file}")

    # Step 5: Reload and verify
    save_and_reload(output_file)

    print("\n" + "=" * 80)
    print("Tutorial 01 complete!")
    print(f"Output file: {output_file}")
    print("You can open this .usda file in any text editor to see the USD format.")
    print("=" * 80)


if __name__ == "__main__":
    main()
