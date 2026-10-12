"""
================================================================================
Tutorial 05: USD Scene Assembly - References, Variants, and Instancing
================================================================================

This tutorial covers:
  1. Using References to compose multiple USD files into one scene
  2. Using Variants to switch between different configurations
  3. Using Instancing to efficiently duplicate objects
  4. Using Payloads for deferred loading
  5. Building a complete scene assembly

Key Concepts:
  - Reference:  A link to another USD file. The referenced file's content
                is composed into the current stage. Changes to the referenced
                file are reflected in all stages that reference it.
  - Variant:    A set of alternative configurations for a prim. For example,
                a "chair" prim could have variants for "red", "blue", "green".
  - Instance:   A shared copy of a prim. All instances share the same data,
                reducing memory usage. Only the transform differs.
  - Payload:    Like a reference, but loaded lazily (only when needed).
                Useful for large assets that shouldn't always be loaded.

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\05_usd_assembly.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf


# ==============================================================================
# Part 1: Creating Asset Files for Referencing
# ==============================================================================

def create_asset_files(output_dir):
    """
    Create separate USD files that will be referenced by the main scene.

    In a real production pipeline, assets (furniture, vehicles, characters)
    are stored in separate USD files and assembled into scenes using references.

    We create:
      1. table.usda  - A simple table asset
      2. chair.usda  - A simple chair asset
      3. lamp.usda   - A simple lamp asset

    Args:
        output_dir (str): Directory to save the asset files.

    Returns:
        dict: Mapping of asset name to file path.
    """
    assets = {}

    # --- Create Table Asset ---
    table_path = os.path.join(output_dir, "table.usda")
    stage = Usd.Stage.CreateNew(table_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Table top
    top = UsdGeom.Cube.Define(stage, "/Table")
    top.GetSizeAttr().Set(4.0)
    top.GetDisplayColorAttr().Set([(0.6, 0.4, 0.2)])  # Brown
    UsdGeom.Xformable(top).AddTranslateOp().Set(Gf.Vec3d(0.0, 1.5, 0.0))
    stage.SetDefaultPrim(top.GetPrim())
    stage.GetRootLayer().Save()
    assets["table"] = table_path
    print(f"  [+] Created table asset: {table_path}")

    # --- Create Chair Asset ---
    chair_path = os.path.join(output_dir, "chair.usda")
    stage = Usd.Stage.CreateNew(chair_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Seat
    seat = UsdGeom.Cube.Define(stage, "/Chair")
    seat.GetSizeAttr().Set(1.0)
    seat.GetDisplayColorAttr().Set([(0.3, 0.3, 0.8)])  # Blue
    UsdGeom.Xformable(seat).AddTranslateOp().Set(Gf.Vec3d(0.0, 0.5, 0.0))
    stage.SetDefaultPrim(seat.GetPrim())
    stage.GetRootLayer().Save()
    assets["chair"] = chair_path
    print(f"  [+] Created chair asset: {chair_path}")

    # --- Create Lamp Asset ---
    lamp_path = os.path.join(output_dir, "lamp.usda")
    stage = Usd.Stage.CreateNew(lamp_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Lamp shade (cone)
    lamp = UsdGeom.Cone.Define(stage, "/Lamp")
    lamp.GetHeightAttr().Set(0.8)
    lamp.GetRadiusAttr().Set(0.5)
    lamp.GetDisplayColorAttr().Set([(1.0, 1.0, 0.8)])  # Warm yellow
    UsdGeom.Xformable(lamp).AddTranslateOp().Set(Gf.Vec3d(0.0, 2.0, 0.0))
    stage.SetDefaultPrim(lamp.GetPrim())
    stage.GetRootLayer().Save()
    assets["lamp"] = lamp_path
    print(f"  [+] Created lamp asset: {lamp_path}")

    return assets


# ==============================================================================
# Part 2: Using References to Assemble a Scene
# ==============================================================================

def assemble_with_references(stage, assets):
    """
    Assemble a room scene by referencing the asset files.

    References allow us to compose multiple USD files into one scene.
    Each reference creates a new prim whose content comes from the referenced file.

    Key points about references:
      - The referenced file's default prim is loaded
      - The reference can be given a custom prim path
      - Changes to the referenced file are reflected in all scenes that use it
      - References can be layered (a reference can reference other files)

    Args:
        stage (Usd.Stage): The main scene stage.
        assets (dict): Mapping of asset name to file path.
    """
    # Create a room Xform to hold all furniture
    room = UsdGeom.Xform.Define(stage, "/World/Room")

    # --- Reference the Table ---
    # Create a prim that will hold the table reference
    table_prim = stage.DefinePrim("/World/Room/Table", "Xform")
    # Add a reference to the table.usda file
    # The reference's content will appear under this prim
    table_prim.GetReferences().AddReference(assets["table"])
    # Position the table in the center of the room
    # Use MakeMatrixXform to avoid conflicts with referenced prim's existing xformOps
    UsdGeom.Xformable(table_prim).MakeMatrixXform().Set(
        Gf.Matrix4d().SetTranslate(Gf.Vec3d(0.0, 0.0, 0.0))
    )
    print("  [+] Referenced table at room center")

    # --- Reference Chairs around the table ---
    chair_positions = [
        ("Chair_N", (0.0, 0.0, -3.0)),    # North
        ("Chair_S", (0.0, 0.0, 3.0)),     # South
        ("Chair_E", (3.0, 0.0, 0.0)),     # East
        ("Chair_W", (-3.0, 0.0, 0.0)),    # West
    ]

    for name, pos in chair_positions:
        chair_prim = stage.DefinePrim(f"/World/Room/{name}", "Xform")
        chair_prim.GetReferences().AddReference(assets["chair"])
        UsdGeom.Xformable(chair_prim).MakeMatrixXform().Set(
            Gf.Matrix4d().SetTranslate(Gf.Vec3d(pos[0], 0.0, pos[2]))
        )
        print(f"  [+] Referenced {name} at ({pos[0]}, 0, {pos[2]})")

    # --- Reference the Lamp on the table ---
    lamp_prim = stage.DefinePrim("/World/Room/Lamp", "Xform")
    lamp_prim.GetReferences().AddReference(assets["lamp"])
    UsdGeom.Xformable(lamp_prim).MakeMatrixXform().Set(
        Gf.Matrix4d().SetTranslate(Gf.Vec3d(0.0, 1.5, 0.0))
    )
    print("  [+] Referenced lamp on table")


# ==============================================================================
# Part 3: Using Variants for Configuration Switching
# ==============================================================================

def create_variants(stage):
    """
    Create variant sets to demonstrate configuration switching.

    Variants allow a prim to have multiple alternative configurations.
    For example, a "Material" variant set could have "Wood", "Metal", and
    "Plastic" variants, each with different material bindings.

    This is extremely useful for:
      - LOD (Level of Detail) switching
      - Material alternatives
      - Configuration options (e.g. "open" vs "closed" door)

    Args:
        stage (Usd.Stage): The stage to add variants to.
    """
    # Create a cube that will have color variants
    cube = UsdGeom.Cube.Define(stage, "/World/VariantCube")
    cube.GetSizeAttr().Set(2.0)
    UsdGeom.Xformable(cube).AddTranslateOp().Set(Gf.Vec3d(8.0, 0.0, 0.0))

    # Get the prim from the cube
    prim = cube.GetPrim()

    # Create a variant set named "Color"
    # A variant set is a collection of named alternatives
    variant_set = prim.GetVariantSets().AddVariantSet("Color")

    # Add variants to the set
    # Each variant defines a different configuration
    for color_name, color_value in [
        ("Red",   (1.0, 0.0, 0.0)),
        ("Green", (0.0, 1.0, 0.0)),
        ("Blue",  (0.0, 0.0, 1.0)),
    ]:
        # Add a variant to the set
        variant_set.AddVariant(color_name)

        # Set the variant's content
        # We must switch to the variant to edit its content
        variant_set.SetVariantSelection(color_name)

        # Get the edit context for this variant
        # Changes made within this context only apply when this variant is selected
        with variant_set.GetVariantEditContext():
            cube.GetDisplayColorAttr().Set([color_value])

    # Set the default selection to "Red"
    variant_set.SetVariantSelection("Red")
    print("  [+] Created variant set 'Color' with Red, Green, Blue variants")

    # Demonstrate switching variants
    print("  [~] Switching through variants:")
    for color_name in ["Red", "Green", "Blue"]:
        variant_set.SetVariantSelection(color_name)
        current_color = cube.GetDisplayColorAttr().Get()
        print(f"      Variant '{color_name}': color = {current_color}")

    # Reset to Red
    variant_set.SetVariantSelection("Red")


# ==============================================================================
# Part 4: Using Instancing for Efficient Duplication
# ==============================================================================

def demonstrate_instancing(stage):
    """
    Demonstrate instancing for efficient object duplication.

    When you need many copies of the same object, instancing is much more
    efficient than creating separate prims. All instances share the same
    scene description; only the transform differs.

    Benefits of instancing:
      - Reduced memory usage (shared data)
      - Faster scene loading
      - Easier to modify all instances at once

    Args:
        stage (Usd.Stage): The stage to add instances to.
    """
    # Create a "prototype" sphere that will be instanced
    # The "instanceable" flag marks this prim as a prototype for instancing
    prototype = UsdGeom.Sphere.Define(stage, "/World/InstancedColumn")
    prototype.GetRadiusAttr().Set(0.3)
    prototype.GetDisplayColorAttr().Set([(0.7, 0.7, 0.7)])  # Gray
    UsdGeom.Xformable(prototype).AddTranslateOp().Set(Gf.Vec3d(0.0, 1.0, 0.0))

    # Mark the prototype as instanceable
    # This tells USD that this prim can be shared across instances
    prototype.GetPrim().SetInstanceable(True)

    # Create instances of the column in a grid pattern
    # Each instance is a reference to the prototype with a different transform
    print("  [+] Creating instanced columns in a grid:")

    grid_size = 3
    spacing = 2.0
    start_offset = -(grid_size - 1) * spacing / 2

    for i in range(grid_size):
        for j in range(grid_size):
            instance_name = f"Column_{i}_{j}"
            instance_path = f"/World/Columns/{instance_name}"

            # Create an instance by referencing the prototype
            instance_prim = stage.DefinePrim(instance_path, "Xform")

            # Add a reference to the prototype within this stage
            # Using a relative reference to the prototype prim
            instance_prim.GetReferences().AddReference(
                "",  # Internal reference (same stage)
                prototype.GetPrim().GetPath()
            )

            # Set the instance's position
            # Use MakeMatrixXform to avoid conflicts with referenced prototype's xformOps
            x = start_offset + i * spacing
            z = start_offset + j * spacing
            UsdGeom.Xformable(instance_prim).MakeMatrixXform().Set(
                Gf.Matrix4d().SetTranslate(Gf.Vec3d(x, 0.0, z))
            )

    print(f"  [+] Created {grid_size}x{grid_size} = {grid_size * grid_size} instanced columns")


# ==============================================================================
# Part 5: Inspecting the Assembled Scene
# ==============================================================================

def inspect_scene(stage):
    """
    Inspect and print the structure of the assembled scene.

    This shows how to traverse the scene hierarchy and identify:
      - Referenced prims (prims whose content comes from another file)
      - Instanced prims (prims that share data with other prims)
      - Variant sets on prims

    Args:
        stage (Usd.Stage): The stage to inspect.
    """
    print("\n--- Scene Structure ---")

    def print_prim_tree(prim, indent=0):
        """Recursively print the prim tree with annotations."""
        prefix = "  " * indent
        prim_name = prim.GetName()
        prim_type = prim.GetTypeName()
        prim_path = prim.GetPath()

        # Check for special properties
        annotations = []

        # Check if this prim has references
        refs = prim.GetMetadata("references")
        if refs:
            annotations.append("[REFERENCED]")

        # Check if this prim is an instance
        if prim.IsInstance():
            annotations.append("[INSTANCE]")

        # Check if this prim is instanceable
        if prim.IsInstanceable():
            annotations.append("[INSTANCEABLE]")

        # Check for variant sets
        variant_sets = prim.GetVariantSets()
        if variant_sets.GetNames():
            annotations.append(f"[VARIANTS: {variant_sets.GetNames()}]")

        annotation_str = " ".join(annotations)
        print(f"{prefix}- {prim_name} ({prim_type}) {annotation_str}")

        # Recurse into children
        for child in prim.GetChildren():
            print_prim_tree(child, indent + 1)

    # Start from the root prim
    root = stage.GetDefaultPrim()
    if root.IsValid():
        print_prim_tree(root)
    else:
        # If no default prim, traverse from pseudo-root
        for child in stage.GetPseudoRoot().GetChildren():
            print_prim_tree(child)


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 05: USD Scene Assembly - References, Variants, and Instancing")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    assets_dir = os.path.join(output_dir, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    # Step 1: Create asset files
    print("\n--- Step 1: Creating Asset Files ---")
    assets = create_asset_files(assets_dir)

    # Step 2: Assemble scene with references
    print("\n--- Step 2: Assembling Scene with References ---")
    main_file = os.path.join(output_dir, "05_usd_assembly.usda")
    stage = Usd.Stage.CreateNew(main_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    assemble_with_references(stage, assets)

    # Step 3: Create variants
    print("\n--- Step 3: Creating Variants ---")
    create_variants(stage)

    # Step 4: Demonstrate instancing
    print("\n--- Step 4: Demonstrating Instancing ---")
    demonstrate_instancing(stage)

    # Step 5: Inspect the scene
    inspect_scene(stage)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {main_file}")

    print("\n" + "=" * 80)
    print("Tutorial 05 complete!")
    print(f"Main scene: {main_file}")
    print(f"Asset files: {assets_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
