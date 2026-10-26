"""
Tutorial 12: USD Lighting
=========================

Introduces lighting in USD using the UsdLux schema set. Creates a complete
lighting-ready scene with geometry, PBR materials, and four fundamental
light types (Distant, Dome, Rect, Sphere), plus a light filter and shadow API.

This tutorial runs on pure USD authoring APIs (no Kit, no RTX renderer, no GPU
required). The scene is written to a .usda file that can be inspected in a text
editor or opened in USDView / Omniverse USD Composer for visual verification.

Run:
    cd YOUR_DIRECTORY\\omniverse_env
    Scripts\\activate
    python tutorials\\usd_advanced\\12_usd_lighting\\12_usd_lighting.py
"""

import os
import sys

# Ensure USD (pxr) is importable. In the omniverse_env venv usd-core provides it.
try:
    from pxr import Usd, UsdGeom, UsdShade, UsdLux, Sdf, Gf
except ImportError as e:
    print("ERROR: Could not import pxr. Activate the virtual environment first:")
    print("  cd E:\\omniverse_env")
    print("  Scripts\\activate")
    raise


# ---------------------------------------------------------------------------
# 1. Scene geometry (simple stage that lights can illuminate)
# ---------------------------------------------------------------------------

def build_scene_geometry(stage):
    """Create a floor plane, a cube, and a sphere for lights to illuminate."""
    floor = UsdGeom.Plane.Define(stage, "/World/Floor")
    floor.CreateWidthAttr().Set(20.0)
    floor.CreateLengthAttr().Set(20.0)
    floor.CreateAxisAttr().Set("Y")
    floor.AddTranslateOp().Set(Gf.Vec3d(0, 0, 0))

    cube = UsdGeom.Cube.Define(stage, "/World/Cube")
    cube.CreateSizeAttr().Set(2.0)
    cube.AddTranslateOp().Set(Gf.Vec3d(-2.5, 1.0, 0))

    sphere = UsdGeom.Sphere.Define(stage, "/World/Sphere")
    sphere.CreateRadiusAttr().Set(1.2)
    sphere.AddTranslateOp().Set(Gf.Vec3d(2.5, 1.2, 0))

    print("  [Geometry] Floor, Cube, Sphere created")
    return floor, cube, sphere


# ---------------------------------------------------------------------------
# 2. PBR materials (so surfaces react to lights)
# ---------------------------------------------------------------------------

def create_pbr_material(stage, path, color, roughness=0.5, metallic=0.0):
    """Create a UsdPreviewSurface PBR material with the given color."""
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, path + "/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(color)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    material.CreateSurfaceOutput().ConnectToSource(
        shader.ConnectableAPI(), "surface"
    )
    return material


def bind_material(prim, material):
    """Bind a material to a prim using MaterialBindingAPI."""
    UsdShade.MaterialBindingAPI(prim).Bind(material)


# ---------------------------------------------------------------------------
# 3. Camera (so the scene is renderable)
# ---------------------------------------------------------------------------

def create_camera(stage):
    """Create a perspective camera looking at the scene."""
    cam = UsdGeom.Camera.Define(stage, "/World/Camera")
    # Author camera attributes directly (Gf.Camera API varies across USD versions)
    cam.CreateFocalLengthAttr().Set(50.0)
    cam.CreateHorizontalApertureAttr().Set(20.955)  # standard 35mm
    cam.CreateVerticalApertureAttr().Set(15.2908)
    cam.CreateClippingRangeAttr().Set(Gf.Vec2f(0.1, 100.0))
    cam.CreateProjectionAttr().Set("perspective")
    xf = UsdGeom.Xformable(cam)
    xf.AddTranslateOp().Set(Gf.Vec3d(0, 4.0, 12.0))
    xf.AddRotateXOp().Set(-15.0)
    print("  [Camera] Perspective camera created (focal=50mm, 35mm sensor)")
    return cam


# ---------------------------------------------------------------------------
# 4. Lights (the core of this tutorial)
# ---------------------------------------------------------------------------

def create_distant_light(stage):
    """
    DistantLight: a parallel (directional) light, like the sun.
    Has no position - only a direction. Illuminates everything evenly.
    """
    light = UsdLux.DistantLight.Define(stage, "/World/Lights/SunLight")
    light.CreateIntensityAttr().Set(2.0)
    light.CreateColorAttr().Set(Gf.Vec3f(1.0, 0.95, 0.85))  # warm sunlight
    light.CreateAngleAttr().Set(0.53)  # ~sun angular radius (degrees)
    light.CreateEnableColorTemperatureAttr().Set(True)
    light.CreateColorTemperatureAttr().Set(5500.0)  # daylight

    xf = UsdGeom.Xformable(light)
    xf.AddRotateZOp().Set(45.0)
    xf.AddRotateXOp().Set(-55.0)

    print("  [Light] DistantLight 'SunLight' - intensity=2.0, 5500K, warm")
    return light


def create_dome_light(stage):
    """
    DomeLight: ambient environment lighting that surrounds the entire scene.
    Simulates sky/HDRI. Without a texture it is a solid color (sky tint).
    """
    light = UsdLux.DomeLight.Define(stage, "/World/Lights/SkyLight")
    light.CreateIntensityAttr().Set(1.0)
    light.CreateColorAttr().Set(Gf.Vec3f(0.6, 0.75, 1.0))  # cool sky tint
    light.CreateTextureFileAttr().Set("")  # empty = use color
    light.CreateGuideRadiusAttr().Set(1.0)

    print("  [Light] DomeLight 'SkyLight' - intensity=1.0, cool sky tint")
    return light


def create_rect_light(stage):
    """
    RectLight: a rectangular area light. Useful for soft studio-style lighting.
    Has a physical size (width x height) and a position.
    """
    light = UsdLux.RectLight.Define(stage, "/World/Lights/StudioPanel")
    light.CreateWidthAttr().Set(4.0)
    light.CreateHeightAttr().Set(2.0)
    light.CreateIntensityAttr().Set(5.0)
    light.CreateColorAttr().Set(Gf.Vec3f(1.0, 1.0, 1.0))
    light.CreateEnableColorTemperatureAttr().Set(True)
    light.CreateColorTemperatureAttr().Set(6500.0)

    xf = UsdGeom.Xformable(light)
    xf.AddTranslateOp().Set(Gf.Vec3d(0, 6.0, 0))
    xf.AddRotateXOp().Set(90.0)  # face downward

    print("  [Light] RectLight 'StudioPanel' - 4x2, intensity=5.0, 6500K")
    return light


def create_sphere_light(stage):
    """
    SphereLight: a point light with a radius (a glowing sphere).
    Good for practical light sources like lamps or bulbs.
    """
    light = UsdLux.SphereLight.Define(stage, "/World/Lights/Bulb")
    light.CreateRadiusAttr().Set(0.3)
    light.CreateIntensityAttr().Set(50.0)
    light.CreateColorAttr().Set(Gf.Vec3f(1.0, 0.8, 0.5))  # warm bulb
    light.CreateNormalizeAttr().Set(True)

    xf = UsdGeom.Xformable(light)
    xf.AddTranslateOp().Set(Gf.Vec3d(2.5, 3.0, 0))

    print("  [Light] SphereLight 'Bulb' - radius=0.3, intensity=50.0, warm")
    return light


# ---------------------------------------------------------------------------
# 5. Light filter + Shadow API (advanced lighting control)
# ---------------------------------------------------------------------------

def create_light_filter(stage, target_light):
    """
    A LightFilter modifies the light it is applied to (e.g. gobo patterns,
    color modulation). Applied via the light's 'light:filters' relationship.
    """
    light_filter = UsdLux.LightFilter.Define(
        stage, "/World/Lights/Filters/TintFilter"
    )

    filter_shader = UsdShade.Shader.Define(
        stage, "/World/Lights/Filters/TintFilter/FilterShader"
    )
    filter_shader.CreateIdAttr("UsdLuxTintFilterColorOpacity")
    filter_shader.CreateInput("tint", Sdf.ValueTypeNames.Color3f).Set(
        Gf.Vec3f(1.0, 0.9, 0.85)
    )

    target_light.CreateFiltersRel().AddTarget(
        "/World/Lights/Filters/TintFilter"
    )

    print("  [Filter] LightFilter 'TintFilter' applied to RectLight")
    return light_filter


def apply_shadow_api(stage, light_prim_path):
    """
    ShadowAPI lets you control shadow casting per-light: enable/disable,
    shadow color, shadow distance falloff.
    """
    light = stage.GetPrimAtPath(light_prim_path)
    shadow_api = UsdLux.ShadowAPI.Apply(light)
    shadow_api.CreateShadowEnableAttr().Set(True)
    shadow_api.CreateShadowColorAttr().Set(Gf.Vec3f(0.0, 0.0, 0.0))
    shadow_api.CreateShadowDistanceAttr().Set(0.0)

    print("  [Shadow] ShadowAPI applied to SunLight (shadows enabled)")
    return shadow_api


# ---------------------------------------------------------------------------
# 6. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 80)
    print("Tutorial 12: USD Lighting")
    print("=" * 80)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    usd_file = os.path.join(output_dir, "12_usd_lighting.usda")

    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    print("\n[1/6] Building scene geometry...")
    floor, cube, sphere = build_scene_geometry(stage)

    print("\n[2/6] Creating PBR materials...")
    floor_mat = create_pbr_material(
        stage, "/World/Materials/FloorMat",
        Gf.Vec3f(0.4, 0.4, 0.45), roughness=0.8, metallic=0.0
    )
    cube_mat = create_pbr_material(
        stage, "/World/Materials/CubeMat",
        Gf.Vec3f(0.8, 0.2, 0.2), roughness=0.4, metallic=0.1
    )
    sphere_mat = create_pbr_material(
        stage, "/World/Materials/SphereMat",
        Gf.Vec3f(0.2, 0.5, 0.9), roughness=0.3, metallic=0.7
    )
    bind_material(floor, floor_mat)
    bind_material(cube, cube_mat)
    bind_material(sphere, sphere_mat)
    print("  [Material] FloorMat (gray), CubeMat (red), SphereMat (blue metal)")

    print("\n[3/6] Creating camera...")
    create_camera(stage)

    print("\n[4/6] Creating lights...")
    sun = create_distant_light(stage)
    sky = create_dome_light(stage)
    panel = create_rect_light(stage)
    bulb = create_sphere_light(stage)

    print("\n[5/6] Applying light filter and shadow API...")
    create_light_filter(stage, panel)
    apply_shadow_api(stage, "/World/Lights/SunLight")

    print("\n[6/6] Saving stage...")
    stage.GetRootLayer().Save()

    print(f"\n  [OK] Stage saved to: {usd_file}")

    print("\n--- Verification: Lights in stage ---")
    for light_type, type_name in [
        (UsdLux.DistantLight, "DistantLight"),
        (UsdLux.DomeLight, "DomeLight"),
        (UsdLux.RectLight, "RectLight"),
        (UsdLux.SphereLight, "SphereLight"),
    ]:
        prims = [p.GetPath() for p in stage.Traverse() if light_type(p)]
        for p in prims:
            l = light_type(stage.GetPrimAtPath(p))
            intensity = l.GetIntensityAttr().Get()
            color = l.GetColorAttr().Get()
            print(f"  {type_name:14s} {p}: intensity={intensity}, color={tuple(round(c,2) for c in color)}")

    sun_prim = stage.GetPrimAtPath("/World/Lights/SunLight")
    if UsdLux.ShadowAPI(sun_prim).GetShadowEnableAttr().Get():
        print("  ShadowAPI on SunLight: shadows ENABLED")

    rect_prim = stage.GetPrimAtPath("/World/Lights/StudioPanel")
    filters = UsdLux.RectLight(rect_prim).GetFiltersRel().GetTargets()
    print(f"  RectLight filters: {filters}")

    print(f"\nOutput file: {usd_file}")
    print("Open the .usda file in a text editor to see the lighting data,")
    print("or in USDView / Omniverse USD Composer to see the lit scene.")
    print("=" * 80)
    print("Tutorial 12 complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()


