"""
================================================================================
Tutorial 03: USD Materials - Colors, Shaders, and Material Binding
================================================================================

This tutorial covers:
  1. Setting display colors on geometry (simple coloring)
  2. Creating USD Material prims
  3. Creating shader networks (PBR - Physically Based Rendering)
  4. Binding materials to geometry
  5. Using Material Binding API

Key Concepts:
  - Display Color:   A simple per-prim color (no lighting, for preview only)
  - Material:        A prim that contains a shader network defining surface
                     appearance (metalness, roughness, albedo, etc.)
  - Shader:          A node within a material that computes surface properties
  - PBR:             Physically Based Rendering - a standard for realistic
                     material representation (albedo, roughness, metalness, normal)
  - Material Binding: The relationship between a geometry prim and a material

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\03_usd_materials.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, UsdShade, Sdf


# ==============================================================================
# Part 1: Simple Display Colors
# ==============================================================================

def set_display_colors(stage):
    """
    Set simple display colors on geometry prims.

    Display color is the simplest way to add color to geometry in USD.
    It does NOT require materials or shaders - it's a "preview" color
    that USD viewers display when no material is bound.

    Display color is stored as a "primvars:displayColor" attribute.
    Each color is an RGB tuple with values in [0.0, 1.0].

    Args:
        stage (Usd.Stage): The stage containing geometry.
    """
    # Create a few cubes with different colors
    colors = [
        ("RedCube",    (1.0, 0.0, 0.0)),
        ("GreenCube",  (0.0, 1.0, 0.0)),
        ("BlueCube",   (0.0, 0.0, 1.0)),
        ("YellowCube", (1.0, 1.0, 0.0)),
        ("PurpleCube", (0.5, 0.0, 0.5)),
    ]

    for name, color in colors:
        # Define a cube prim
        cube = UsdGeom.Cube.Define(stage, f"/World/{name}")
        cube.GetSizeAttr().Set(1.5)

        # Set the display color
        # GetDisplayColorAttr() returns the color primvar attribute
        # The value is a list of color tuples (one per face, or one for all)
        cube.GetDisplayColorAttr().Set([color])

        print(f"  [+] {name}: display color = {color}")


# ==============================================================================
# Part 2: Creating a PBR Material
# ==============================================================================

def create_pbr_material(stage, material_path="/World/Materials/RedMetal"):
    """
    Create a PBR (Physically Based Rendering) material.

    A material in USD is a prim that contains a "shader network" - a graph
    of shader nodes that compute the final surface appearance.

    For PBR, we typically use:
      - albedo (diffuse color): The base color of the material
      - roughness: How rough the surface is (0=mirror, 1=fully diffuse)
      - metalness: Whether the material is a metal (0=non-metal, 1=metal)
      - normal: Surface normal map for adding surface detail

    In Omniverse, the standard shader is "UsdPreviewSurface".

    Args:
        stage (Usd.Stage): The stage to create the material on.
        material_path (str): The prim path for the material.

    Returns:
        UsdShade.Material: The created material object.
    """
    # Create the Material prim
    # A Material is a container for shader networks
    material = UsdShade.Material.Define(stage, material_path)

    # Create a Shader prim inside the material
    # This shader uses the "UsdPreviewSurface" shader model
    # UsdPreviewSurface is the standard PBR shader in USD
    shader_path = material_path + "/PreviewSurface"
    shader = UsdShade.Shader.Define(stage, shader_path)

    # Set the shader's implementation (which shader to use)
    # "UsdPreviewSurface" is the standard USD PBR shader
    shader.CreateIdAttr("UsdPreviewSurface")

    # --- Set PBR Properties ---

    # Albedo (diffuse color): The base color of the material
    # This is an RGB color input, values in [0.0, 1.0]
    albedo_input = shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f)
    albedo_input.Set((0.8, 0.1, 0.1))  # Red-ish

    # Roughness: Surface roughness (0.0 = smooth/mirror, 1.0 = rough/diffuse)
    roughness_input = shader.CreateInput("roughness", Sdf.ValueTypeNames.Float)
    roughness_input.Set(0.3)  # Fairly smooth

    # Metalness: Whether the surface is metallic (0.0 = dielectric, 1.0 = metal)
    metalness_input = shader.CreateInput("metallic", Sdf.ValueTypeNames.Float)
    metalness_input.Set(0.8)  # Mostly metallic

    # Set this shader as the "surface" output of the material
    # This tells USD that this shader computes the surface appearance
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(),
        "surface"
    )

    print(f"  [+] PBR Material created at {material_path}")
    print(f"      albedo=(0.8, 0.1, 0.1), roughness=0.3, metalness=0.8")

    return material


# ==============================================================================
# Part 3: Creating Multiple Materials
# ==============================================================================

def create_material_variants(stage):
    """
    Create several materials with different PBR properties.

    This demonstrates how to create materials for common surface types:
      1. Red Metal (high metalness, low roughness)
      2. Blue Plastic (low metalness, medium roughness)
      3. Gold Metal (gold albedo, high metalness, low roughness)
      4. Matte White (low metalness, high roughness)

    Args:
        stage (Usd.Stage): The stage to create materials on.

    Returns:
        dict: Mapping of material name to UsdShade.Material.
    """
    materials = {}

    # Define material specifications
    # Each spec is: (name, albedo, roughness, metalness)
    material_specs = [
        ("RedMetal",     (0.8, 0.1, 0.1), 0.3, 0.8),
        ("BluePlastic",  (0.1, 0.2, 0.8), 0.5, 0.0),
        ("GoldMetal",    (1.0, 0.7, 0.3), 0.2, 1.0),
        ("MatteWhite",   (0.9, 0.9, 0.9), 0.9, 0.0),
    ]

    for name, albedo, roughness, metalness in material_specs:
        mat_path = f"/World/Materials/{name}"
        material = UsdShade.Material.Define(stage, mat_path)

        # Create the preview surface shader
        shader = UsdShade.Shader.Define(stage, mat_path + "/Shader")
        shader.CreateIdAttr("UsdPreviewSurface")

        # Set PBR properties
        shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(albedo)
        shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
        shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metalness)

        # Connect shader to material surface output
        material.CreateSurfaceOutput().ConnectToSource(
            shader.ConnectableAPI(), "surface"
        )

        materials[name] = material
        print(f"  [+] Material '{name}': albedo={albedo}, roughness={roughness}, metalness={metalness}")

    return materials


# ==============================================================================
# Part 4: Binding Materials to Geometry
# ==============================================================================

def bind_materials(stage, materials):
    """
    Bind materials to geometry prims.

    Material binding is the process of associating a material with a geometry
    prim. When the scene is rendered, the bound material's shader is used
    to compute the surface appearance.

    A prim can have:
      - One material bound directly
      - Different materials for different purposes (e.g. "preview", "full")
      - Materials inherited from parent prims

    Args:
        stage (Usd.Stage): The stage containing geometry and materials.
        materials (dict): Mapping of material name to UsdShade.Material.
    """
    # Create geometry and bind materials
    from pxr import Gf

    # Create a row of spheres, each with a different material
    sphere_names = list(materials.keys())

    for i, mat_name in enumerate(sphere_names):
        sphere_path = f"/World/MaterialDemo/{mat_name}_Sphere"
        sphere = UsdGeom.Sphere.Define(stage, sphere_path)
        sphere.GetRadiusAttr().Set(1.0)

        # Position the sphere in a row
        x_pos = (i - len(sphere_names) / 2) * 3.0
        UsdGeom.Xformable(sphere).AddTranslateOp().Set(Gf.Vec3d(x_pos, 0.0, 0.0))

        # Bind the material to the sphere
        # UsdShade.MaterialBindingAPI provides the binding interface
        material = materials[mat_name]
        UsdShade.MaterialBindingAPI.Apply(sphere.GetPrim()).Bind(material)

        print(f"  [~] Bound material '{mat_name}' to {sphere_path}")


# ==============================================================================
# Part 5: Inspecting Material Bindings
# ==============================================================================

def inspect_bindings(stage):
    """
    Inspect and display material bindings on the stage.

    This shows how to:
      1. Find which material is bound to a prim
      2. Read the shader properties of a material

    Args:
        stage (Usd.Stage): The stage to inspect.
    """
    print("\n--- Inspecting Material Bindings ---")

    # Iterate over all prims and check for material bindings
    for prim in stage.TraverseAll():
        # Check if this prim has a material binding
        binding_api = UsdShade.MaterialBindingAPI(prim)
        bound_material = binding_api.ComputeBoundMaterial()

        # ComputeBoundMaterial() may return a tuple (material, context) in some USD versions
        if isinstance(bound_material, tuple):
            bound_material = bound_material[0]

        if bound_material and prim.GetTypeName() in ("Sphere", "Cube"):
            mat_path = bound_material.GetPath()
            print(f"  {prim.GetPath()} ({prim.GetTypeName()}) -> Material: {mat_path}")

            # Read the shader properties
            # Find the shader inside the material
            for child in bound_material.GetPrim().GetChildren():
                if child.GetTypeName() == "Shader":
                    shader = UsdShade.Shader(child)
                    shader_id = shader.GetIdAttr().Get()

                    # Read PBR properties
                    albedo = shader.GetInput("diffuseColor")
                    roughness = shader.GetInput("roughness")
                    metalness = shader.GetInput("metallic")

                    if albedo:
                        print(f"    Shader: {shader_id}")
                        print(f"    albedo: {albedo.Get()}")
                        print(f"    roughness: {roughness.Get() if roughness else 'N/A'}")
                        print(f"    metalness: {metalness.Get() if metalness else 'N/A'}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 03: USD Materials - Colors, Shaders, and Material Binding")
    print("=" * 80)

    # Define output path
    output_dir = os.path.dirname(os.path.abspath(__file__))
    output_file = os.path.join(output_dir, "output", "03_usd_materials.usda")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Create stage
    stage = Usd.Stage.CreateNew(output_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    # Set default prim
    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Step 1: Set display colors
    print("\n--- Step 1: Setting Display Colors ---")
    set_display_colors(stage)

    # Step 2: Create a PBR material
    print("\n--- Step 2: Creating PBR Material ---")
    create_pbr_material(stage)

    # Step 3: Create material variants
    print("\n--- Step 3: Creating Material Variants ---")
    materials = create_material_variants(stage)

    # Step 4: Bind materials to geometry
    print("\n--- Step 4: Binding Materials to Geometry ---")
    bind_materials(stage, materials)

    # Step 5: Inspect bindings
    inspect_bindings(stage)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {output_file}")

    print("\n" + "=" * 80)
    print("Tutorial 03 complete!")
    print(f"Output file: {output_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
