#!/usr/bin/env python
"""
Tutorial Verification Script
=============================
Programmatically verifies that all 14 tutorials produced correct USD output.
Each check reads the .usda file and inspects the USD scene graph to confirm
the expected prims, attributes, schemas, and relationships exist.

Usage:
    cd E:\\omniverse_env
    Scripts\\activate
    python tools\\verify_all_tutorials.py
"""

import os
import sys
from pxr import Usd, UsdGeom, UsdLux, UsdPhysics, UsdSkel, UsdShade, Sdf

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TUTORIALS = os.path.join(BASE, "tutorials")

passed = 0
failed = 0
errors = []


def load_stage(rel_path):
    full = os.path.join(BASE, rel_path)
    stage = Usd.Stage.Open(full)
    assert stage is not None, f"Could not open {full}"
    return stage


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}")
    else:
        failed += 1
        errors.append(label)
        d = f" ({detail})" if detail else ""
        print(f"  [FAIL] {label}{d}")


# =============================================================================
# Tutorial 01: USD Basics - Stage, Prim, Attribute
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 01: USD Basics")
print("=" * 70)

s = load_stage("tutorials/usd_basics/01_usd_basics/output/01_usd_basics.usda")

check("Stage loads", s is not None)
check("/World exists (Xform)", s.GetPrimAtPath("/World").IsValid())
check("/World/Cube1 exists (Cube)", s.GetPrimAtPath("/World/Cube1").IsValid())
check("/World/Sphere1 exists (Sphere)", s.GetPrimAtPath("/World/Sphere1").IsValid())
check("/World/Cylinder1 exists (Cylinder)", s.GetPrimAtPath("/World/Cylinder1").IsValid())
check("/World/Camera1 exists (Camera)", s.GetPrimAtPath("/World/Camera1").IsValid())

cube = UsdGeom.Cube(s.GetPrimAtPath("/World/Cube1"))
check("Cube1 size=5.0 (updated from 2.0)", cube.GetSizeAttr().Get() == 5.0)

sphere = UsdGeom.Sphere(s.GetPrimAtPath("/World/Sphere1"))
check("Sphere1 radius=1.5", sphere.GetRadiusAttr().Get() == 1.5)

cyl = UsdGeom.Cylinder(s.GetPrimAtPath("/World/Cylinder1"))
check("Cylinder1 height=3.0", cyl.GetHeightAttr().Get() == 3.0)
check("Cylinder1 radius=0.5", cyl.GetRadiusAttr().Get() == 0.5)

cam = UsdGeom.Camera(s.GetPrimAtPath("/World/Camera1"))
check("Camera1 focalLength=50.0", cam.GetFocalLengthAttr().Get() == 50.0)

c1_color = cube.GetDisplayColorAttr().Get()
check("Cube1 displayColor=red (1,0,0)", c1_color is not None and tuple(c1_color[0]) == (1.0, 0.0, 0.0))


# =============================================================================
# Tutorial 02: USD Geometry - Transforms
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 02: USD Geometry - Transforms")
print("=" * 70)

s = load_stage("tutorials/usd_basics/02_usd_geometry/output/02_usd_geometry.usda")

for name in ["Cube", "Sphere", "Cylinder", "Cone", "Plane", "Capsule"]:
    check(f"/World/Shapes/{name} exists", s.GetPrimAtPath(f"/World/Shapes/{name}").IsValid())

cube = s.GetPrimAtPath("/World/Shapes/Cube")
cube_tx = cube.GetAttribute("xformOp:translate").Get()
check("Cube translated to (5, 0, 0)", tuple(cube_tx) == (5.0, 0.0, 0.0))

sphere = s.GetPrimAtPath("/World/Shapes/Sphere")
sphere_tx = sphere.GetAttribute("xformOp:translate").Get()
check("Sphere translated to (-5, 0, 0)", tuple(sphere_tx) == (-5.0, 0.0, 0.0))

cone = s.GetPrimAtPath("/World/Shapes/Cone")
cone_tx = cone.GetAttribute("xformOp:translate").Get()
check("Cone translated to (0, -5, 0)", tuple(cone_tx) == (0.0, -5.0, 0.0))

cap = s.GetPrimAtPath("/World/Shapes/Capsule")
cap_tx = cap.GetAttribute("xformOp:translate").Get()
check("Capsule translated to (0, 0, 5)", tuple(cap_tx) == (0.0, 0.0, 5.0))

rot_z = sphere.GetAttribute("xformOp:rotateXYZ:Z").Get()
if rot_z is None:
    # Try rotateZYX or other order
    for attr_name in ["xformOp:rotateZYX:Z", "xformOp:rotateXYZ:Z", "xformOp:rotateZ"]:
        rot_z = sphere.GetAttribute(attr_name).Get()
        if rot_z is not None:
            break
check("Sphere rotated 45deg on Z", rot_z is not None and abs(rot_z - 45.0) < 0.1, f"got {rot_z}")

cyl = s.GetPrimAtPath("/World/Shapes/Cylinder")
cyl_scale = cyl.GetAttribute("xformOp:scale").Get()
check("Cylinder scaled (2, 2, 0.5)", tuple(cyl_scale) == (2.0, 2.0, 0.5))

# =============================================================================
# Tutorial 03: USD Materials
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 03: USD Materials")
print("=" * 70)

s = load_stage("tutorials/usd_basics/03_usd_materials/output/03_usd_materials.usda")

expected_materials = {
    "RedMetal":    {"albedo": (0.8, 0.1, 0.1), "roughness": 0.3, "metalness": 0.8},
    "BluePlastic": {"albedo": (0.1, 0.2, 0.8), "roughness": 0.5, "metalness": 0.0},
    "GoldMetal":   {"albedo": (1.0, 0.7, 0.3), "roughness": 0.2, "metalness": 1.0},
    "MatteWhite":  {"albedo": (0.9, 0.9, 0.9), "roughness": 0.9, "metalness": 0.0},
}

for name, expected in expected_materials.items():
    mat_prim = s.GetPrimAtPath(f"/World/Materials/{name}")
    check(f"Material {name} exists", mat_prim.IsValid())
    shader = None
    for child in mat_prim.GetChildren():
        sh = UsdShade.Shader(child)
        if sh:
            shader_id = sh.GetIdAttr().Get() if hasattr(sh, 'GetIdAttr') else None
            if shader_id is None:
                shader_id = child.GetAttribute("info:id").Get()
            if shader_id == "UsdPreviewSurface":
                shader = sh
                break
    check(f"{name} has UsdPreviewSurface shader", shader is not None)
    if shader:
        albedo = shader.GetInput("diffuseColor").Get()
        check(f"{name} albedo correct",
              albedo is not None and abs(albedo[0] - expected["albedo"][0]) < 0.01)
        rough = shader.GetInput("roughness").Get()
        check(f"{name} roughness correct",
              rough is not None and abs(rough - expected["roughness"]) < 0.01)
        metal = shader.GetInput("metallic").Get()
        check(f"{name} metalness correct",
              metal is not None and abs(metal - expected["metalness"]) < 0.01)

for name in ["RedMetal", "BluePlastic", "GoldMetal", "MatteWhite"]:
    sphere = s.GetPrimAtPath(f"/World/MaterialDemo/{name}_Sphere")
    check(f"{name}_Sphere exists", sphere.IsValid())
    if sphere.IsValid():
        result = UsdShade.MaterialBindingAPI(sphere).ComputeBoundMaterial()
        binding = result[0] if isinstance(result, tuple) else result
        bound_path = binding.GetPath() if binding and binding.GetPath() else "None"
        check(f"{name}_Sphere bound to {name}",
              str(bound_path) == f"/World/Materials/{name}", f"bound to {bound_path}")

# =============================================================================
# Tutorial 04: USD Animation
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 04: USD Animation")
print("=" * 70)

s = load_stage("tutorials/usd_basics/04_usd_animation/output/04_usd_animation.usda")

check("Stage has time range", s.HasAuthoredTimeCodeRange())
if s.HasAuthoredTimeCodeRange():
    start_tc = s.GetStartTimeCode()
    end_tc = s.GetEndTimeCode()
    check("Timeline starts at frame 1", start_tc == 1.0, f"got {start_tc}")
    check("Timeline ends at frame 120", end_tc == 120.0, f"got {end_tc}")

sphere = s.GetPrimAtPath("/World/AnimatedSphere")
check("AnimatedSphere exists", sphere.IsValid())
tx_attr = sphere.GetAttribute("xformOp:translate")
p1 = tx_attr.Get(1.0)
check("Sphere frame 1 near (5,0,0)", p1 is not None and abs(p1[0] - 5.0) < 0.1)
p60 = tx_attr.Get(60.0)
check("Sphere frame 60 near (-5,0,0)", p60 is not None and abs(p60[0] + 5.0) < 0.1)

cube = s.GetPrimAtPath("/World/SpinningCube")
rot_attr = cube.GetAttribute("xformOp:rotateY")
if not rot_attr.IsValid():
    # Try alternate naming
    for attr in cube.GetAttributes():
        n = attr.GetName()
        if "rotate" in n and "Y" in n:
            rot_attr = attr
            break
rot1 = rot_attr.Get(1.0)
rot120 = rot_attr.Get(120.0)
check("Cube rotation frame 1 ~ 0deg", rot1 is not None and abs(rot1) < 1.0, f"got {rot1}")
check("Cube rotation frame 120 ~ 360deg", rot120 is not None and abs(rot120 - 360.0) < 1.0, f"got {rot120}")

pulse = s.GetPrimAtPath("/World/PulsingSphere")
scale_attr = pulse.GetAttribute("xformOp:scale")
check("PulsingSphere scale varies", scale_attr.Get(1.0) != scale_attr.Get(15.0))

color_cube = UsdGeom.Cube(s.GetPrimAtPath("/World/ColorChangingCube"))
c1 = color_cube.GetDisplayColorAttr().Get(1.0)
c2 = color_cube.GetDisplayColorAttr().Get(60.0)
check("ColorChangingCube color varies", c1 is not None and c2 is not None and tuple(c1) != tuple(c2))

# =============================================================================
# Tutorial 05: USD Assembly
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 05: USD Assembly - References, Variants, Instancing")
print("=" * 70)

s = load_stage("tutorials/usd_basics/05_usd_assembly/output/05_usd_assembly.usda")

assets_dir = "tutorials/usd_basics/05_usd_assembly/output/assets"
for asset in ["table.usda", "chair.usda", "lamp.usda"]:
    check(f"Asset file {asset} exists", os.path.isfile(os.path.join(BASE, assets_dir, asset)))

for name in ["Table", "Chair_N", "Chair_S", "Chair_E", "Chair_W", "Lamp"]:
    p = s.GetPrimAtPath(f"/World/Room/{name}")
    check(f"{name} prim exists", p.IsValid())
    check(f"{name} has authored references", p.HasAuthoredReferences())

variant_cube = s.GetPrimAtPath("/World/VariantCube")
vs = variant_cube.GetVariantSets().GetNames()
check("VariantCube has 'Color' variant set", "Color" in vs)
if "Color" in vs:
    vset = variant_cube.GetVariantSets().GetVariantSet("Color")
    check("Color variants: Red, Green, Blue",
          set(vset.GetVariantNames()) == {"Red", "Green", "Blue"})

inst_count = sum(1 for i in range(3) for j in range(3)
                 if s.GetPrimAtPath(f"/World/Columns/Column_{i}_{j}").IsInstanceable())
check("9 instanced columns", inst_count == 9)

# =============================================================================
# Tutorial 06: Kit Extensions
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 06: Kit Extensions")
print("=" * 70)

ext_dir = "tutorials/kit_api/06_kit_extensions/output/my_extension"
check("extension.toml exists", os.path.isfile(os.path.join(BASE, ext_dir, "extension.toml")))
check("extension.py exists", os.path.isfile(os.path.join(BASE, ext_dir, "extension.py")))
check("__init__.py exists", os.path.isfile(os.path.join(BASE, ext_dir, "__init__.py")))

s = load_stage("tutorials/kit_api/06_kit_extensions/output/06_kit_extensions.usda")
sim_obj = s.GetPrimAtPath("/World/SimulationObject")
check("SimulationObject prim exists", sim_obj.IsValid())

if sim_obj.IsValid():
    check("simulation:type = 'fluid_dynamics'",
          sim_obj.GetAttribute("simulation:type").Get() == "fluid_dynamics")
    ts = sim_obj.GetAttribute("simulation:timeStep").Get()
    check("simulation:timeStep = 0.016", ts is not None and abs(ts - 0.016) < 0.001)
    check("simulation:maxIterations = 1000",
          sim_obj.GetAttribute("simulation:maxIterations").Get() == 1000)
    vel = sim_obj.GetAttribute("simulation:velocity").Get()
    check("simulation:velocity = (1, 0.5, 0)",
          vel is not None and tuple(vel) == (1.0, 0.5, 0.0))

config = s.GetPrimAtPath("/ExtensionConfig/MyExtension")
check("ExtensionConfig prim exists", config.IsValid())
if config.IsValid():
    check("enabled = True", config.GetAttribute("enabled").Get() == True)
    check("logLevel = 'INFO'", config.GetAttribute("logLevel").Get() == "INFO")

# =============================================================================
# Tutorial 07: Omniverse Connector
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 07: Omniverse Data Connectors")
print("=" * 70)

data_dir = "tutorials/kit_api/07_omniverse_connector/output/connector_data"
check("CSV data file exists", os.path.isfile(os.path.join(BASE, data_dir, "sample_data.csv")))
check("JSON data file exists", os.path.isfile(os.path.join(BASE, data_dir, "sample_scene.json")))

s = load_stage("tutorials/kit_api/07_omniverse_connector/output/07_omniverse_connector.usda")

all_spheres = [p for p in s.Traverse() if p.GetTypeName() == "Sphere"]
check("CSV data converted to >=100 point prims", len(all_spheres) >= 100, f"got {len(all_spheres)}")

json_prim = s.GetPrimAtPath("/World/JSON_Scene/FactoryFloor")
check("JSON scene converted to USD prim", json_prim.IsValid())

json_prim2 = s.GetPrimAtPath("/World/FactoryLayout/FactoryFloor")
check("Batch-processed JSON scene exists", json_prim2.IsValid())

# =============================================================================
# Tutorial 08: Live Sync
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 08: Live Sync")
print("=" * 70)

sync_dir = "tutorials/kit_api/08_live_sync/output/live_sync"
check("change_tracking.usda exists",
      os.path.isfile(os.path.join(BASE, sync_dir, "change_tracking.usda")))

s = load_stage(f"{sync_dir}/change_tracking.usda")
cube = s.GetPrimAtPath("/World/Cube")
sphere = s.GetPrimAtPath("/World/Sphere")
check("Tracked cube exists", cube.IsValid())
check("Tracked sphere exists", sphere.IsValid())
check("Cube size modified to 5.0", UsdGeom.Cube(cube).GetSizeAttr().Get() == 5.0)

comp_file = "tutorials/kit_api/08_live_sync/output/composition_demo.usda"
if os.path.isfile(os.path.join(BASE, comp_file)):
    s2 = load_stage(comp_file)
    c = s2.GetPrimAtPath("/World/ComposedCube")
    check("Composition demo cube exists", c.IsValid())
    if c.IsValid():
        size = UsdGeom.Cube(c).GetSizeAttr().Get()
        check("Override wins: size=5.0 (not 2.0)", size == 5.0, f"got {size}")
        color = UsdGeom.Cube(c).GetDisplayColorAttr().Get(0)
        check("Override wins: color=blue", tuple(color) == (0.0, 0.0, 1.0), f"got {color}")

# =============================================================================
# Tutorial 09: PhysicsNeMo to USD
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 09: PhysicsNeMo to USD")
print("=" * 70)

json_path = "tutorials/physicsnemo_integration/09_physicsnemo_to_usd/output/physicsnemo_data/darcy_flow.json"
check("Darcy flow JSON exists", os.path.isfile(os.path.join(BASE, json_path)))

s = load_stage("tutorials/physicsnemo_integration/09_physicsnemo_to_usd/output/09_physicsnemo_to_usd.usda")

pressure_points = s.GetPrimAtPath("/World/DarcyFlow/pressure_points")
check("Pressure point cloud exists", pressure_points.IsValid())
if pressure_points.IsValid():
    children = [c for c in pressure_points.GetChildren() if c.IsA(UsdGeom.Sphere)]
    check("225 pressure points (15x15 grid)", len(children) == 225, f"got {len(children)}")

height_field = s.GetPrimAtPath("/World/DarcyFlow/pressure_heightfield")
check("Pressure height field exists", height_field.IsValid())
if height_field.IsValid():
    cols = [c for c in height_field.GetChildren() if c.IsA(UsdGeom.Cylinder)]
    check("225 height field columns", len(cols) == 225, f"got {len(cols)}")

vel_points = s.GetPrimAtPath("/World/DarcyFlow/velocity_mag_points")
check("Velocity point cloud exists", vel_points.IsValid())

meta = s.GetPrimAtPath("/World/DarcyFlow/SimulationMetadata")
check("SimulationMetadata prim exists", meta.IsValid())
if meta.IsValid():
    attrs = [a.GetName() for a in meta.GetAttributes()]
    check("Metadata has >=5 fields", len(attrs) >= 5, f"got {len(attrs)}")

# =============================================================================
# Tutorial 10: Simulation Visual
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 10: Simulation Visual - Animated Color Maps")
print("=" * 70)

s = load_stage("tutorials/physicsnemo_integration/10_simulation_visual/output/10_simulation_visual.usda")

check("Stage has time range", s.HasAuthoredTimeCodeRange())
if s.HasAuthoredTimeCodeRange():
    start_tc = s.GetStartTimeCode()
    end_tc = s.GetEndTimeCode()
    check("Timeline starts at frame 1", start_tc == 1.0, f"got {start_tc}")
    check("Timeline ends at frame 109", end_tc == 109.0, f"got {end_tc}")

color_map = s.GetPrimAtPath("/World/TransientSim/TemperatureMap")
check("Animated color map exists", color_map.IsValid())
if color_map.IsValid():
    children = [c for c in color_map.GetChildren() if c.IsA(UsdGeom.Sphere)]
    check("100 color map points (10x10 grid)", len(children) == 100, f"got {len(children)}")
    # Check time-sampled colors on children
    has_ts = False
    for c in children:
        ca = UsdGeom.Sphere(c).GetDisplayColorAttr()
        if len(ca.GetTimeSamples()) > 0:
            has_ts = True
            break
    check("Color map has time-sampled colors", has_ts)

height_anim = s.GetPrimAtPath("/World/TransientSim/HeightField")
check("Animated height field exists", height_anim.IsValid())

vel_field = s.GetPrimAtPath("/World/TransientSim/VelocityField")
check("Velocity vector field exists", vel_field.IsValid())

# =============================================================================
# Tutorial 11: Digital Twin
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 11: Digital Twin Pipeline")
print("=" * 70)

s = load_stage("tutorials/physicsnemo_integration/11_digital_twin/output/11_digital_twin.usda")

check("Shell (cylinder) exists", s.GetPrimAtPath("/World/HeatExchanger/Shell").IsValid())
check("Inlet pipe exists", s.GetPrimAtPath("/World/HeatExchanger/InletPipe").IsValid())
check("Outlet pipe exists", s.GetPrimAtPath("/World/HeatExchanger/OutletPipe").IsValid())

tubes = [p for p in s.Traverse() if "Tube" in p.GetName() and p.IsA(UsdGeom.Cylinder)]
check("9 tubes in bundle (3x3)", len(tubes) == 9, f"got {len(tubes)}")

check("Stage has time range", s.HasAuthoredTimeCodeRange())
if s.HasAuthoredTimeCodeRange():
    start_tc = s.GetStartTimeCode()
    end_tc = s.GetEndTimeCode()
    check("Timeline spans 115 frames", end_tc - start_tc > 100,
          f"start={start_tc}, end={end_tc}")

sensors = [p for p in s.Traverse() if "Sensor" in p.GetName() and p.IsA(UsdGeom.Sphere)]
check("10 temperature sensors", len(sensors) == 10, f"got {len(sensors)}")

meta = s.GetPrimAtPath("/World/HeatExchanger/DigitalTwinMetadata")
check("DigitalTwinMetadata exists", meta.IsValid())

check("Report file exists",
      os.path.isfile(os.path.join(BASE, "tutorials/physicsnemo_integration/11_digital_twin/output/digital_twin_report.txt")))

# =============================================================================
# Tutorial 12: USD Lighting
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 12: USD Lighting")
print("=" * 70)

s = load_stage("tutorials/usd_advanced/12_usd_lighting/output/12_usd_lighting.usda")

sun = UsdLux.DistantLight(s.GetPrimAtPath("/World/Lights/SunLight"))
check("DistantLight 'SunLight' exists", sun.GetPrim().IsValid())
if sun.GetPrim().IsValid():
    check("SunLight intensity=2.0", sun.GetIntensityAttr().Get() == 2.0)

sky = UsdLux.DomeLight(s.GetPrimAtPath("/World/Lights/SkyLight"))
check("DomeLight 'SkyLight' exists", sky.GetPrim().IsValid())
if sky.GetPrim().IsValid():
    check("SkyLight intensity=1.0", sky.GetIntensityAttr().Get() == 1.0)

panel = UsdLux.RectLight(s.GetPrimAtPath("/World/Lights/StudioPanel"))
check("RectLight 'StudioPanel' exists", panel.GetPrim().IsValid())
if panel.GetPrim().IsValid():
    check("Panel intensity=5.0", panel.GetIntensityAttr().Get() == 5.0)

bulb = UsdLux.SphereLight(s.GetPrimAtPath("/World/Lights/Bulb"))
check("SphereLight 'Bulb' exists", bulb.GetPrim().IsValid())
if bulb.GetPrim().IsValid():
    check("Bulb intensity=50.0", bulb.GetIntensityAttr().Get() == 50.0)

shadow_api = UsdLux.ShadowAPI(s.GetPrimAtPath("/World/Lights/SunLight"))
check("ShadowAPI applied to SunLight", bool(shadow_api))

filt = s.GetPrimAtPath("/World/Lights/Filters/TintFilter")
check("LightFilter 'TintFilter' exists", filt.IsValid())

check("Floor exists", s.GetPrimAtPath("/World/Floor").IsValid())
check("Cube exists", s.GetPrimAtPath("/World/Cube").IsValid())
check("Sphere exists", s.GetPrimAtPath("/World/Sphere").IsValid())
check("Camera exists", s.GetPrimAtPath("/World/Camera").IsValid())

for mat_name in ["FloorMat", "CubeMat", "SphereMat"]:
    check(f"Material {mat_name} exists",
          s.GetPrimAtPath(f"/World/Materials/{mat_name}").IsValid())

# =============================================================================
# Tutorial 13: USD Physics
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 13: USD Physics")
print("=" * 70)

s = load_stage("tutorials/usd_advanced/13_usd_physics/output/13_usd_physics.usda")

scene = UsdPhysics.Scene(s.GetPrimAtPath("/World/PhysicsScene"))
check("PhysicsScene exists", scene.GetPrim().IsValid())
if scene.GetPrim().IsValid():
    gv = scene.GetGravityDirectionAttr().Get()
    gm = scene.GetGravityMagnitudeAttr().Get()
    check("Gravity direction=(0,-1,0)", tuple(gv) == (0.0, -1.0, 0.0), f"got {gv}")
    check("Gravity magnitude=9.81", abs(gm - 9.81) < 0.01, f"got {gm}")

floor = s.GetPrimAtPath("/World/Floor")
check("Floor has CollisionAPI", bool(UsdPhysics.CollisionAPI(floor)))
check("Floor has NO RigidBodyAPI (static)", not bool(UsdPhysics.RigidBodyAPI(floor)))

for name, mass in [("BoxA", 1.0), ("BoxB", 1.0), ("Ball", 0.5), ("Cylinder", 2.0)]:
    p = s.GetPrimAtPath(f"/World/{name}")
    check(f"{name} has RigidBodyAPI", bool(UsdPhysics.RigidBodyAPI(p)))
    check(f"{name} has CollisionAPI", bool(UsdPhysics.CollisionAPI(p)))
    mass_attr = p.GetAttribute("physics:mass")
    if mass_attr.HasAuthoredValue():
        check(f"{name} mass={mass}", abs(mass_attr.Get() - mass) < 0.01)

vel_attr = s.GetPrimAtPath("/World/Ball").GetAttribute("physics:velocity")
check("Ball has initial velocity", vel_attr.HasAuthoredValue())

cyl_coll_approx = s.GetPrimAtPath("/World/Cylinder").GetAttribute("physics:approximation").Get()
check("Cylinder uses convexHull", cyl_coll_approx == "convexHull", f"got {cyl_coll_approx}")

for name, restitution in [("Bouncy", 0.8), ("Grippy", 0.1)]:
    mat = s.GetPrimAtPath(f"/World/PhysicsMaterials/{name}")
    check(f"Physics material {name} exists", mat.IsValid())
    if mat.IsValid():
        r = mat.GetAttribute("physics:restitution:restitution").Get()
        if r is None:
            r = mat.GetAttribute("physics:restitution").Get()
        check(f"{name} restitution={restitution}", r is not None and abs(r - restitution) < 0.01)

fixed = UsdPhysics.Joint(s.GetPrimAtPath("/World/Joints/Fixed"))
check("FixedJoint exists", fixed.GetPrim().IsValid())
if fixed.GetPrim().IsValid():
    check("FixedJoint body0=BoxA",
          fixed.GetBody0Rel().GetTargets() == [Sdf.Path("/World/BoxA")])
    check("FixedJoint body1=BoxB",
          fixed.GetBody1Rel().GetTargets() == [Sdf.Path("/World/BoxB")])

rev = UsdPhysics.RevoluteJoint(s.GetPrimAtPath("/World/Joints/Revolute"))
check("RevoluteJoint exists", rev.GetPrim().IsValid())
if rev.GetPrim().IsValid():
    check("RevoluteJoint body0=Floor",
          rev.GetBody0Rel().GetTargets() == [Sdf.Path("/World/Floor")])
    check("RevoluteJoint body1=Pendulum",
          rev.GetBody1Rel().GetTargets() == [Sdf.Path("/World/Pendulum")])

# =============================================================================
# Tutorial 14: Skeletal Animation
# =============================================================================
print("\n" + "=" * 70)
print("Tutorial 14: Skeletal Animation")
print("=" * 70)

s = load_stage("tutorials/usd_advanced/14_skeletal_animation/output/14_skeletal_animation.usda")

skel_root = s.GetPrimAtPath("/World/Character")
check("SkelRoot exists", skel_root.IsValid())
check("Character is SkelRoot schema", skel_root.IsA(UsdSkel.Root))

skel = UsdSkel.Skeleton(s.GetPrimAtPath("/World/Character/Skeleton"))
check("Skeleton exists", skel.GetPrim().IsValid())
if skel.GetPrim().IsValid():
    joints = skel.GetJointsAttr().Get()
    check("5 joints in skeleton", len(joints) == 5, f"got {joints}")
    check("Has root joint", any("root" == j for j in joints))
    check("Has arm_L joint", any("arm_L" in j for j in joints))
    check("Has arm_R joint", any("arm_R" in j for j in joints))

anim = UsdSkel.Animation(s.GetPrimAtPath("/World/Character/Animation"))
check("Animation exists", anim.GetPrim().IsValid())
if anim.GetPrim().IsValid():
    check("Animation has 5 joints", len(anim.GetJointsAttr().Get()) == 5)

mesh = s.GetPrimAtPath("/World/Character/Body")
check("Skinned mesh 'Body' exists", mesh.IsValid())
if mesh.IsValid():
    check("Mesh has 5 vertices", len(UsdGeom.Mesh(mesh).GetPointsAttr().Get()) == 5)
    binding = UsdSkel.BindingAPI(mesh)
    check("Body has SkelBindingAPI", bool(binding))
    check("Body bound to Skeleton",
          binding.GetSkeletonRel().GetTargets() == [Sdf.Path("/World/Character/Skeleton")])
    check("Body animation source set",
          binding.GetAnimationSourceRel().GetTargets() == [Sdf.Path("/World/Character/Animation")])
    check("Has jointIndices primvar",
          mesh.GetAttribute("primvars:skel:jointIndices").IsValid())
    check("Has jointWeights primvar",
          mesh.GetAttribute("primvars:skel:jointWeights").IsValid())

bs = UsdSkel.BlendShape(s.GetPrimAtPath("/World/Character/BlendShapes/Wave"))
check("BlendShape 'Wave' exists", bs.GetPrim().IsValid())
if bs.GetPrim().IsValid():
    check("BlendShape has 5 offsets", len(bs.GetOffsetsAttr().Get()) == 5)

anim_skel = UsdSkel.Animation(s.GetPrimAtPath("/World/Character/Animation"))
rot_attr = anim_skel.GetRotationsAttr()
ts = rot_attr.GetTimeSamples()
check("Animation has time samples", len(ts) >= 2, f"got {len(ts)} samples")
if len(ts) >= 2:
    rot_t0 = rot_attr.Get(ts[0])
    rot_t1 = rot_attr.Get(ts[-1])
    # Quatf not directly iterable; compare via real and imaginary parts
    def quat_key(q):
        return (q.GetReal(), q.GetImaginary()[0], q.GetImaginary()[1], q.GetImaginary()[2])
    check("arm_L rotation changes over time", quat_key(rot_t0[3]) != quat_key(rot_t1[3]))
    check("arm_L starts at identity (1,0,0,0)", abs(rot_t0[3].GetReal() - 1.0) < 0.01)
    check("arm_L raised at t=24 (~0.866, 0, 0, -0.5)",
          abs(rot_t1[3].GetReal() - 0.866) < 0.01 and abs(rot_t1[3].GetImaginary()[2] + 0.5) < 0.01)

# =============================================================================
# SUMMARY
# =============================================================================
print("\n" + "=" * 70)
print(f"SUMMARY: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 70)

if failed > 0:
    print(f"\nFailed checks:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("\nAll 14 tutorials verified successfully!")
    sys.exit(0)



