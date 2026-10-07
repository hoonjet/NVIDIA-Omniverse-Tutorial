"""
================================================================================
Tutorial 02: USD Geometry - Creating and Transforming Shapes
================================================================================

This tutorial covers:
  1. Creating various geometry types (Cube, Sphere, Cylinder, Cone, Plane, Capsule)
  2. Applying Transformations (translate, rotate, scale)
  3. Understanding the Xform schema (transformable objects)
  4. Using XformCommonAPI for simplified transform operations
  5. Organizing geometry in a hierarchy

Key Concepts:
  - Xform:     A prim that can be transformed (moved, rotated, scaled).
               Most geometry prims inherit from Xform.
  - Transform: A 4x4 matrix that encodes position, rotation, and scale.
  - XformOps:  Individual transform operations (translate, rotate, scale)
               that are composed in order to produce the final matrix.

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\02_usd_geometry.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, Sdf
import math


# ==============================================================================
# Part 1: Creating Various Geometry Types
# ==============================================================================

def create_geometry_types(stage):
    """
    Create one of each major geometry type available in USD.

    USD provides several built-in geometry schemas:
      - Cube:     A box with equal edge lengths
      - Sphere:   A sphere defined by radius
      - Cylinder:  A cylinder with height and radius
      - Cone:      A cone with height and radius
      - Plane:     A flat plane (grid)
      - Capsule:   A capsule (cylinder with hemispheric caps)

    Each geometry is placed under a parent Xform prim to demonstrate hierarchy.

    Args:
        stage (Usd.Stage): The stage to add geometry to.
    """
    # Create a parent Xform to hold all geometry
    # This demonstrates how prims can be organized hierarchically
    shapes_parent = UsdGeom.Xform.Define(stage, "/World/Shapes")

    # --- Cube ---
    # A cube is defined by a single "size" attribute (edge length)
    cube = UsdGeom.Cube.Define(stage, "/World/Shapes/Cube")
    cube.GetSizeAttr().Set(2.0)
    cube.GetDisplayColorAttr().Set([(1.0, 0.2, 0.2)])  # Red-ish
    print("  [+] Cube created (size=2.0)")

    # --- Sphere ---
    # A sphere is defined by "radius" and optionally "extent" (bounding box)
    sphere = UsdGeom.Sphere.Define(stage, "/World/Shapes/Sphere")
    sphere.GetRadiusAttr().Set(1.0)
    sphere.GetDisplayColorAttr().Set([(0.2, 1.0, 0.2)])  # Green-ish
    print("  [+] Sphere created (radius=1.0)")

    # --- Cylinder ---
    # A cylinder is defined by "height" and "radius"
    # The axis is along Z by default (can be changed with the "axis" attribute)
    cylinder = UsdGeom.Cylinder.Define(stage, "/World/Shapes/Cylinder")
    cylinder.GetHeightAttr().Set(3.0)
    cylinder.GetRadiusAttr().Set(0.5)
    cylinder.GetDisplayColorAttr().Set([(0.2, 0.2, 1.0)])  # Blue-ish
    print("  [+] Cylinder created (height=3.0, radius=0.5)")

    # --- Cone ---
    # A cone is defined by "height" and "radius"
    cone = UsdGeom.Cone.Define(stage, "/World/Shapes/Cone")
    cone.GetHeightAttr().Set(2.0)
    cone.GetRadiusAttr().Set(1.0)
    cone.GetDisplayColorAttr().Set([(1.0, 0.6, 0.0)])  # Orange
    print("  [+] Cone created (height=2.0, radius=1.0)")

    # --- Plane ---
    # A plane is a flat rectangular surface defined by "width" and "length"
    # Useful for ground planes, walls, etc.
    plane = UsdGeom.Plane.Define(stage, "/World/Shapes/Plane")
    plane.GetWidthAttr().Set(10.0)
    plane.GetLengthAttr().Set(10.0)
    plane.GetDisplayColorAttr().Set([(0.5, 0.5, 0.5)])  # Gray
    print("  [+] Plane created (width=10.0, length=10.0)")

    # --- Capsule ---
    # A capsule is a cylinder with hemispheric caps
    # Defined by "radius" and "height" (total height including caps)
    capsule = UsdGeom.Capsule.Define(stage, "/World/Shapes/Capsule")
    capsule.GetRadiusAttr().Set(0.5)
    capsule.GetHeightAttr().Set(2.0)
    capsule.GetDisplayColorAttr().Set([(0.8, 0.2, 0.8)])  # Purple
    print("  [+] Capsule created (radius=0.5, height=2.0)")


# ==============================================================================
# Part 2: Applying Transformations
# ==============================================================================

def apply_transforms(stage):
    """
    Apply transformations (translate, rotate, scale) to geometry prims.

    In USD, transforms are applied using "XformOps" (transform operations).
    Each Xform can have multiple ops that are composed in a defined order.

    Common transform operations:
      - Translate: Move the prim along X, Y, Z axes
      - Rotate:     Rotate the prim around X, Y, Z axes (in degrees)
      - Scale:      Scale the prim along X, Y, Z axes

    The order of operations matters! Translate then Rotate is different
    from Rotate then Translate.

    Args:
        stage (Usd.Stage): The stage containing the geometry.
    """
    # --- Translate the Cube ---
    # Move the cube 5 units along the X axis
    cube = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Shapes/Cube"))
    # AddTranslateOp() adds a translation operation to the Xform's op stack
    # The value is a Gf.Vec3d (3-component double vector)
    from pxr import Gf
    cube.AddTranslateOp().Set(Gf.Vec3d(5.0, 0.0, 0.0))
    print("  [~] Cube translated to (5, 0, 0)")

    # --- Translate and Rotate the Sphere ---
    # Move the sphere and rotate it 45 degrees around the Z axis
    sphere = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Shapes/Sphere"))
    sphere.AddTranslateOp().Set(Gf.Vec3d(-5.0, 0.0, 0.0))
    # AddRotateZOp() adds a rotation around the Z axis (in degrees)
    sphere.AddRotateZOp().Set(45.0)
    print("  [~] Sphere translated to (-5, 0, 0) and rotated 45deg on Z")

    # --- Scale the Cylinder ---
    # Scale the cylinder to be twice as wide but half as tall
    cylinder = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Shapes/Cylinder"))
    cylinder.AddTranslateOp().Set(Gf.Vec3d(0.0, 5.0, 0.0))
    # AddScaleOp() adds a non-uniform scale operation
    cylinder.AddScaleOp().Set(Gf.Vec3f(2.0, 2.0, 0.5))
    print("  [~] Cylinder translated to (0, 5, 0) and scaled (2, 2, 0.5)")

    # --- Combined Transform on the Cone ---
    # Demonstrate multiple operations: translate, rotate, then scale
    cone = UsdGeom.Xformable(stage.GetPrimAtPath("/World/Shapes/Cone"))
    cone.AddTranslateOp().Set(Gf.Vec3d(0.0, -5.0, 0.0))
    cone.AddRotateXYZOp().Set(Gf.Vec3f(90.0, 0.0, 0.0))  # Rotate 90deg around X
    cone.AddScaleOp().Set(Gf.Vec3f(1.5, 1.5, 1.5))       # Uniform scale 1.5x
    print("  [~] Cone translated, rotated 90deg on X, and scaled 1.5x")


# ==============================================================================
# Part 3: Using XformCommonAPI for Simplified Transforms
# ==============================================================================

def use_common_api(stage):
    """
    Use UsdGeom.XformCommonAPI for a simpler way to set transforms.

    XformCommonAPI provides a simplified interface that handles the common
    case of: translate, rotate (Euler angles), scale, and pivot point.

    This is easier to use than raw XformOps but less flexible.

    Args:
        stage (Usd.Stage): The stage containing the geometry.
    """
    from pxr import Gf

    # Get the capsule prim and wrap it with XformCommonAPI
    capsule_path = "/World/Shapes/Capsule"
    capsule_prim = stage.GetPrimAtPath(capsule_path)
    capsule_api = UsdGeom.XformCommonAPI(capsule_prim)

    # Set translation directly
    capsule_api.SetTranslate((0.0, 0.0, 5.0))

    # Set rotation (Euler angles in degrees, XYZ rotation order)
    capsule_api.SetRotate((0.0, 0.0, 30.0))

    # Set scale
    capsule_api.SetScale((1.0, 1.0, 1.0))

    print("  [~] Capsule transform set via XformCommonAPI: translate=(0,0,5), rotate=(0,0,30)")


# ==============================================================================
# Part 4: Reading Back Transforms
# ==============================================================================

def read_transforms(stage):
    """
    Read and display the transformation matrix of each prim.

    USD computes the final transformation by composing all XformOps.
    The result is a 4x4 matrix that can be retrieved with GetLocalTransformation().

    Args:
        stage (Usd.Stage): The stage to inspect.
    """
    print("\n--- Reading Transforms ---")

    # Iterate over all shape prims
    shapes_path = "/World/Shapes"
    shapes_prim = stage.GetPrimAtPath(shapes_path)

    for child in shapes_prim.GetChildren():
        prim_path = child.GetPath()
        prim_type = child.GetTypeName()

        # Get the Xformable interface
        xformable = UsdGeom.Xformable(child)

        # Compute the local transformation matrix at the current time
        # The matrix is a 4x4 Gf.Matrix4d
        local_matrix = xformable.GetLocalTransformation()

        # Extract translation from the matrix
        # The translation is in the last column of the matrix
        translation = local_matrix.ExtractTranslation()

        print(f"  {prim_path} ({prim_type}):")
        print(f"    Translation: ({translation[0]:.2f}, {translation[1]:.2f}, {translation[2]:.2f})")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 02: USD Geometry - Creating and Transforming Shapes")
    print("=" * 80)

    # Define output path
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "output", "02_usd_geometry.usda")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create stage
    stage = Usd.Stage.CreateNew(output_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Set default prim
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Step 1: Create geometry
    print("\n--- Step 1: Creating Geometry Types ---")
    create_geometry_types(stage)

    # Step 2: Apply transforms
    print("\n--- Step 2: Applying Transforms ---")
    apply_transforms(stage)

    # Step 3: Use CommonAPI
    print("\n--- Step 3: Using XformCommonAPI ---")
    use_common_api(stage)

    # Step 4: Read back transforms
    read_transforms(stage)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Tutorial 02 complete!")
    print(f"Output file: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
