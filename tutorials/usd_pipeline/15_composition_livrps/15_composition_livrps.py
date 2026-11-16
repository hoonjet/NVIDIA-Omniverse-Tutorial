#!/usr/bin/env python
"""
================================================================================
Tutorial 15: USD Composition Deep Dive - The LIVRPS Strength Ordering
================================================================================

USD composes opinions from many sources into one final scene. When the same
attribute is authored in more than one place, USD picks a winner using the
LIVRPS strength ordering (strongest first):

    L  - Local opinions (directly authored on the prim, incl. the root layer)
    I  - Inherits (opinions from a class the prim inherits)
    V  - VariantSets (opinions from the selected variant)
    R  - References (opinions from referenced layers)
    P  - Payloads (opinions from payload layers, like references but deferrable)
    S  - SubLayers (opinions from nested sublayers, weakest of all)

This tutorial builds ONE stage that exercises all six mechanisms, authors the
SAME attribute ("data:material") at several levels, and then reads back the
composed result together with the LAYER that actually won. This proves the
ordering programmatically instead of asking you to trust a diagram.

Note on sublayers: within a layer stack, the FIRST-listed sublayer is the
STRONGEST. A sublayer can never beat Local, Inherits, Variants, References
or Payloads, no matter where it sits in the list.

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/15_composition_livrps/15_composition_livrps.py
================================================================================
"""

import os
from pxr import Usd, UsdGeom, Sdf, Gf

# Output locations. The main stage plus four small asset layers that provide
# the "remote" opinions used by the reference / payload / sublayer examples.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
ASSETS_DIR = os.path.join(OUTPUT_DIR, "assets")
USDA_PATH = os.path.join(OUTPUT_DIR, "15_composition_livrps.usda")


def V(r, g, b):
    """Small helper - a color3f array default value."""
    return [Gf.Vec3f(r, g, b)]


def author_material(prim, value):
    """Create and set the shared 'data:material' attribute on a prim."""
    attr = prim.CreateAttribute("data:material", Sdf.ValueTypeNames.String)
    attr.Set(value)


# ==============================================================================
# Part 1: Build the asset layers used by References / Payloads / SubLayers
# ==============================================================================

def build_asset_layers():
    """Create the four small layers referenced by the main stage.

    Each asset is intentionally tiny so the composition story stays readable.
    Every asset authors a "data:material" opinion so we can trace which layer
    wins during composition.
    """
    if not os.path.isdir(ASSETS_DIR):
        os.makedirs(ASSETS_DIR)

    # --- (a) base_layout.usda: the STRONGEST sublayer (listed first) ----------
    # Sublayer opinions are the weakest in LIVRPS: any other mechanism that
    # speaks up about the same attribute will override this layer.
    base = Sdf.Layer.CreateNew(os.path.join(ASSETS_DIR, "base_layout.usda"))
    prim_spec = Sdf.CreatePrimInLayer(base, "/World/Geometry/Floor")
    prim_spec.typeName = "Cube"
    prim_spec.specifier = Sdf.SpecifierDef
    size_attr = Sdf.AttributeSpec(prim_spec, "size", Sdf.ValueTypeNames.Double)
    size_attr.default = 8.0
    color_attr = Sdf.AttributeSpec(
        prim_spec, "primvars:displayColor", Sdf.ValueTypeNames.Color3fArray)
    color_attr.default = V(0.2, 0.4, 0.9)   # blue - wins the sublayer battle
    mat_attr = Sdf.AttributeSpec(prim_spec, "data:material", Sdf.ValueTypeNames.String)
    mat_attr.default = "sublayer:blue-concrete"
    base.Save()

    # --- (b) sim_overrides.usda: a WEAKER sublayer (listed after base) --------
    # In USD the sublayer list is ordered STRONG to WEAK: the FIRST sublayer
    # wins. This layer re-authors the Floor color + material to prove that
    # being later in the list loses the sublayer battle - it would still lose
    # to every other LIVRPS mechanism regardless of list position.
    overrides = Sdf.Layer.CreateNew(os.path.join(ASSETS_DIR, "sim_overrides.usda"))
    over_spec = Sdf.CreatePrimInLayer(overrides, "/World/Geometry/Floor")
    over_spec.specifier = Sdf.SpecifierOver  # Over = "edit, do not define"
    over_color = Sdf.AttributeSpec(
        over_spec, "primvars:displayColor", Sdf.ValueTypeNames.Color3fArray)
    over_color.default = V(0.2, 0.9, 0.3)   # green - loses to base_layout
    over_mat = Sdf.AttributeSpec(over_spec, "data:material", Sdf.ValueTypeNames.String)
    over_mat.default = "sublayer:green-painted"
    overrides.Save()

    # --- (c) robot.usda: layer grafted in via a REFERENCE ----------------------
    robot = Sdf.Layer.CreateNew(os.path.join(ASSETS_DIR, "robot.usda"))
    robot_prim = Sdf.CreatePrimInLayer(robot, "/Robot")
    robot_prim.typeName = "Xform"
    robot_prim.specifier = Sdf.SpecifierDef
    arm_spec = Sdf.CreatePrimInLayer(robot, "/Robot/Arm")
    arm_spec.typeName = "Cylinder"
    arm_spec.specifier = Sdf.SpecifierDef
    arm_mat = Sdf.AttributeSpec(arm_spec, "data:material", Sdf.ValueTypeNames.String)
    arm_mat.default = "reference:alloy-arm"

    robot.Save()

    # --- (d) sensor.usda: layer grafted in via a PAYLOAD -----------------------
    payload = Sdf.Layer.CreateNew(os.path.join(ASSETS_DIR, "sensor.usda"))
    sensor_prim = Sdf.CreatePrimInLayer(payload, "/Sensor")
    sensor_prim.typeName = "Xform"
    sensor_prim.specifier = Sdf.SpecifierDef
    probe_spec = Sdf.CreatePrimInLayer(payload, "/Sensor/Probe")
    probe_spec.typeName = "Sphere"
    probe_spec.specifier = Sdf.SpecifierDef
    probe_mat = Sdf.AttributeSpec(probe_spec, "data:material", Sdf.ValueTypeNames.String)
    probe_mat.default = "payload:titanium-probe"
    payload.Save()

    print("  [+] Wrote 4 asset layers to: %s" % os.path.relpath(ASSETS_DIR, SCRIPT_DIR))


# ==============================================================================
# Part 2: Build the main stage exercising all six LIVRPS mechanisms
# ==============================================================================

def build_main_stage():
    """Compose the root layer that uses every LIVRPS mechanism once."""
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    # 6) SUBLAYERS: attach both layout layers. "base_layout" is listed FIRST,
    #    which makes it the stronger of the two sublayers.
    root = stage.GetRootLayer()
    root.subLayerPaths.append(
        os.path.relpath(os.path.join(ASSETS_DIR, "base_layout.usda"), OUTPUT_DIR))
    root.subLayerPaths.append(
        os.path.relpath(os.path.join(ASSETS_DIR, "sim_overrides.usda"), OUTPUT_DIR))

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- 1) LOCAL: strongest possible opinion --------------------------------
    sphere_local = UsdGeom.Sphere.Define(stage, "/World/LocalSphere")
    author_material(sphere_local.GetPrim(), "local:red-anodized")
    sphere_local.GetRadiusAttr().Set(0.5)

    # --- 5) INHERITS: opinions broadcast from a class prim --------------------
    # Class prims are not rendered; they are recipe containers. Any prim that
    # "inherits" the class picks up all opinions authored there - unless a
    # stronger mechanism (like Local) says otherwise.
    cls = stage.CreateClassPrim("/_class_SharedMaterial")
    cls_mat = cls.CreateAttribute("data:material", Sdf.ValueTypeNames.String)
    cls_mat.Set("inherit:shared-steel")
    sphere_inh = UsdGeom.Sphere.Define(stage, "/World/InheritedSphere")
    sphere_inh.GetPrim().GetInherits().AddInherit("/_class_SharedMaterial")
    sphere_inh.GetRadiusAttr().Set(0.5)

    # --- 3) VARIANTS: named alternatives switched at composition time ---------
    sphere_var = UsdGeom.Sphere.Define(stage, "/World/VariantSphere")
    vs = sphere_var.GetPrim().GetVariantSets().AddVariantSet("finish")
    vs.AddVariant("matte")
    vs.AddVariant("glossy")
    # Opinions authored inside a variant edit context belong to that variant.
    vs.SetVariantSelection("matte")
    with vs.GetVariantEditContext():
        sphere_var.GetRadiusAttr().Set(0.25)
        author_material(sphere_var.GetPrim(), "variant:matte-plastic")
    vs.SetVariantSelection("glossy")
    with vs.GetVariantEditContext():
        sphere_var.GetRadiusAttr().Set(0.4)
        author_material(sphere_var.GetPrim(), "variant:glossy-ceramic")

    # --- 4) REFERENCES: graft an asset layer under a prim ---------------------
    ref_prim = stage.DefinePrim("/World/RobotRef", "Xform")
    ref_prim.GetReferences().AddReference("./assets/robot.usda", "/Robot")

    # --- 2) PAYLOADS: like a reference, but unloadable ------------------------
    pay_prim = stage.DefinePrim("/World/SensorPayload", "Xform")
    pay_prim.GetPayloads().AddPayload("./assets/sensor.usda", "/Sensor")

    # --- Local override ON TOP of a reference: Local beats R ------------------
    # The referenced arm authors data:material="reference:alloy-arm", but a
    # local opinion on the same attribute wins because L comes before R.
    stage.DefinePrim("/World/RobotRef/Arm")  # ensure target exists post-compose
    ref_arm_mat = stage.GetPrimAtPath("/World/RobotRef/Arm").CreateAttribute(
        "data:material", Sdf.ValueTypeNames.String)
    ref_arm_mat.Set("local:painted-over-reference")

    stage.GetRootLayer().Save()
    print("  [+] Built stage with all 6 LIVRPS mechanisms: %s"
          % os.path.basename(USDA_PATH))
    return stage




# ==============================================================================
# Part 3: Prove the ordering by reading back composed values + their source
# ===============================================================================

def _locate_layer(stage, node, prim_path, attr_name):
    """Find the layer file that holds the winning opinion for an attribute."""
    stack_layers = list(node.site.layerStack.layers)
    # arcType renders like "Pcp.ArcTypeRoot" - normalize to the tail token.
    arc = str(node.arcType).split(".")[-1]

    def has_spec(layer, p):
        spec = layer.GetPrimAtPath(p)
        return spec is not None and attr_name in spec.attributes

    if arc in ("ArcTypeInherit", "ArcTypeVariant"):
        # Inherit / Variant opinions live under a different site path
        # (the class prim, or the variant-edited prim) in the same stack.
        node_path = str(node.site.path)
        for L in stack_layers:
            if has_spec(L, node_path):
                return "%s (via %s)" % (os.path.basename(L.identifier), node_path)
        return "(root layer, via %s)" % node_path

    if arc != "ArcTypeRoot":
        # Reference / Payload: the opinion lives in the grafted asset layer.
        for L in stack_layers:
            if has_spec(L, prim_path):
                return os.path.basename(L.identifier)
        return "(asset: %s)" % os.path.basename(stack_layers[-1].identifier)

    # Root arc: a LOCAL opinion. The node layer stack lists its layers
    # strong-to-weak, so the FIRST layer carrying a spec is the winner
    # (root layer first, then sublayers in list order).
    for L in stack_layers:
        if has_spec(L, prim_path):
            return os.path.basename(L.identifier)

    # Fallback: the opinion may sit at another path (e.g. a class prim).
    node_path = str(node.site.path)
    if node_path and has_spec(stack_layers[0], node_path):
        return "%s (via %s)" % (os.path.basename(stack_layers[0].identifier), node_path)
    return "?"


def probe(stage, prim_path, expected_winner):
    """Print the composed data:material value and WHERE it came from.

    UsdResolveInfo.GetNode() returns the PcpNodeRef of the winning opinion.
    Its arcType IS the LIVRPS mechanism (Root=Local, Inherit, Variant,
    Reference, Payload); we then locate the exact layer that carried it.
    """
    prim = stage.GetPrimAtPath(prim_path)
    attr = prim.GetAttribute("data:material")
    info = attr.GetResolveInfo()
    value = attr.Get()

    layer_name = "SCHEMA FALLBACK (no opinion authored)"
    arc_name = "Fallback"
    node = info.GetNode()
    if node is not None:
        try:
            arc_name = str(node.arcType).split(".")[-1].replace("ArcType", "")
            layer_name = _locate_layer(stage, node, prim_path, "data:material")
        except Exception as e:
            layer_name = "<resolve error: %s>" % e

    status = "OK " if expected_winner in str(value) else "???"
    print("    %s %-22s -> %-28s [arc: %-9s | layer: %s]"
          % (status, prim_path.rsplit("/", 1)[-1], value, arc_name, layer_name))


def verify_composition():
    """Reload the saved stage and report who won for each mechanism."""
    print("\\n--- Composed 'data:material' values (LIVRPS check) ---")
    stage = Usd.Stage.Open(USDA_PATH)

    probe(stage, "/World/LocalSphere",         "local:red-anodized")
    probe(stage, "/World/InheritedSphere",     "inherit:shared-steel")
    probe(stage, "/World/VariantSphere",       "variant:glossy-ceramic")
    probe(stage, "/World/RobotRef/Arm",        "local:painted-over-reference")
    probe(stage, "/World/SensorPayload/Probe", "payload:titanium-probe")
    probe(stage, "/World/Geometry/Floor",      "sublayer:blue-concrete")

    # Floor shows the sublayer ordering: "base_layout" (blue) is stronger than
    # "sim_overrides" (green) purely because it is FIRST in subLayerPaths.

    # Variant switching: flip the selection and watch the opinions change.
    # The variant carries BOTH radius and data:material opinions; switching
    # the selection re-composes them at runtime.
    print("\\n--- Variant switch demo (V is runtime-switchable) ---")
    sphere = stage.GetPrimAtPath("/World/VariantSphere")
    vs = sphere.GetVariantSets().GetVariantSet("finish")
    print("    selection=%-7s -> data:material=%s, radius=%.2f"
          % (vs.GetVariantSelection(),
             sphere.GetAttribute("data:material").Get(),
             sphere.GetAttribute("radius").Get()))
    vs.SetVariantSelection("matte")
    print("    selection=%-7s -> data:material=%s, radius=%.2f"
          % (vs.GetVariantSelection(),
             sphere.GetAttribute("data:material").Get(),
             sphere.GetAttribute("radius").Get()))


# ==============================================================================
# Main entry point
# ===============================================================================

def main():
    print("=" * 80)
    print("Tutorial 15: USD Composition Deep Dive - LIVRPS Strength Ordering")
    print("=" * 80)

    print("\\n--- Step 1: Building asset layers ---")
    build_asset_layers()

    print("\\n--- Step 2: Building main stage ---")
    build_main_stage()

    print("\\n--- Step 3: Verifying composition ---")
    verify_composition()

    print("\\n" + "=" * 80)
    print("Tutorial 15 complete!")
    print("USD output: %s" % USDA_PATH)
    print("=" * 80)


if __name__ == "__main__":
    main()
