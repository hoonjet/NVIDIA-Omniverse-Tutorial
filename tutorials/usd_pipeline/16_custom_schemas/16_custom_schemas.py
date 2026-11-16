#!/usr/bin/env python
"""
================================================================================
Tutorial 16: Custom Schemas - Codeless API Schema + Python Convention Wrapper
================================================================================

USD ships with built-in schemas (Xform, Sphere, Mesh, ...). Real pipelines
need domain-specific data on prims (sim parameters, renderer settings...).
Two standard ways to do that:

1. COMPILED schema  - C++ plugin with generated classes (out of scope here,
   requires a C++ toolchain).

2. CODELESS schema  - a JSON plugin + a .usda "generated schema" file that
   registers the schema with the UsdSchemaRegistry WITHOUT any C++ code.
   Prim definition gains fallback values, and Usd.PrismSpec-level API
   validation (ApplyAPI / HasAPI) works with the schema name.

This tutorial builds a codeless **single-apply API schema** named
`SimulationDataAPI` that attaches solver parameters (time step, solver type,
iteration budget, initial velocity field) to any prim.

We then demonstrate BOTH access patterns:
  a. Schema-registry style:  prim.ApplyAPI("SimulationDataAPI"),
     prim.GetAttribute("simulation:timeStep"), plus SCHEMA FALLBACK values
     coming straight from the registered prim definition (0.016 etc. even
     before anything is authored).
  b. Convention-wrapper style: a small Python class that authors/reads the
     SAME namespaced properties (the classic pre-codeless pattern; still
     widely used because it needs no plugin registration at all).

IMPORTANT PLUGIN-REGISTRATION DETAIL: plug-registry scanning happens when
the pxr modules load, so PXR_PLUGINPATH_NAME must be set BEFORE
`from pxr import ...`. That is why this file imports pxr late.

Run:
  cd E:/omniverse_env
  Scripts/activate
  python tutorials/usd_pipeline/16_custom_schemas/16_custom_schemas.py
================================================================================
"""

import json
import os

# Output locations. The plugin lives NEXT TO the generated stage so the
# whole folder is self-contained and inspectable.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "output")
PLUGIN_DIR = os.path.join(OUTPUT_DIR, "schema_plugin")
PLUGIN_RESOURCES = os.path.join(PLUGIN_DIR, "resources")
USDA_PATH = os.path.join(OUTPUT_DIR, "16_custom_schemas.usda")

SCHEMA_NAME = "SimulationDataAPI"

# ------------------------------------------------------------------------------
# Part 0: write the codeless-schema plugin (plugInfo.json + generatedSchema.usda)
# ------------------------------------------------------------------------------

PLUG_INFO = {
    "Plugins": [
        {
            "Info": {
                "Types": {
                    # One registry entry per schema class. "schemaKind" tells
                    # UsdSchemaRegistry what kind of schema this is; a
                    # "singleApply" API schema attaches to one prim at a time.
                    SCHEMA_NAME: {
                        "bases": ["UsdAPISchemaBase"],
                        "schemaIdentifier": SCHEMA_NAME,
                        "schemaKind": "singleApplyAPI",
                    }
                }
            },
            # "resource" plugin type = data only, no compiled library.
            "LibraryPath": "",
            "Name": "usdSimulationSchema",
            "ResourcePath": "resources",
            "Type": "resource",
        }
    ]
}

GENERATED_SCHEMA = """\
#usda 1.0
(
    rootLayerDocumentType = "Schema"
)

class SimulationDataAPI "SimulationDataAPI" (
)
{
    custom double simulation:timeStep = 0.016
    custom string simulation:solverType = "darcy"
    custom int simulation:maxIterations = 500
    custom point3f[] simulation:initialVelocity = []
}
"""


def write_plugin_files():
    """Write plugInfo.json + resources/generatedSchema.usda to the plugin dir."""
    if not os.path.isdir(PLUGIN_RESOURCES):
        os.makedirs(PLUGIN_RESOURCES)
    with open(os.path.join(PLUGIN_DIR, "plugInfo.json"), "w") as f:
        json.dump(PLUG_INFO, f, indent=4)
    with open(os.path.join(PLUGIN_RESOURCES, "generatedSchema.usda"), "w") as f:
        f.write(GENERATED_SCHEMA)
    print("  [+] Wrote codeless schema plugin to: %s"
          % os.path.relpath(PLUGIN_DIR, SCRIPT_DIR))


# Plugin dir must be on the plug-registry search path BEFORE pxr loads.
write_plugin_files()
os.environ["PXR_PLUGINPATH_NAME"] = PLUGIN_DIR

from pxr import Usd, UsdGeom, Sdf, Gf  # noqa: E402  (late import is the point)


# ==============================================================================
# Part 1: Convention-wrapper style - a Python class over namespaced properties
# ==============================================================================

class SimulationData(object):
    """Python 'convention schema' wrapping simulation:* properties.

    Before codeless schemas existed this wrapper pattern was THE way to add
    custom prim data. It is still useful: zero registration, easy to ship,
    easy to subclass. It uses the exact same property names as the codeless
    schema above, so data authored by either path is read by both.
    """

    NAMESPACE = "simulation"

    def __init__(self, prim):
        self.prim = prim

    def _attr(self, name, ttype):
        """Get-or-create a namespaced attribute on the wrapped prim."""
        full = "%s:%s" % (self.NAMESPACE, name)
        attr = self.prim.GetAttribute(full)
        if not attr:
            attr = self.prim.CreateAttribute(full, ttype)
        return attr

    # -- typed accessors --------------------------------------------------
    def set_time_step(self, value):
        self._attr("timeStep", Sdf.ValueTypeNames.Double).Set(value)

    def get_time_step(self):
        attr = self.prim.GetAttribute("simulation:timeStep")
        return attr.Get() if attr else None

    def set_solver_type(self, value):
        self._attr("solverType", Sdf.ValueTypeNames.String).Set(value)

    def get_solver_type(self):
        attr = self.prim.GetAttribute("simulation:solverType")
        return attr.Get() if attr else None

    def set_max_iterations(self, value):
        self._attr("maxIterations", Sdf.ValueTypeNames.Int).Set(value)

    def get_max_iterations(self):
        attr = self.prim.GetAttribute("simulation:maxIterations")
        return attr.Get() if attr else None

    def set_initial_velocity(self, vectors):
        self._attr("initialVelocity", Sdf.ValueTypeNames.Point3fArray).Set(vectors)

    def is_valid(self):
        return all(self.prim.GetAttribute("simulation:%s" % k)
                   for k in ("timeStep", "solverType", "maxIterations"))


# ==============================================================================
# Part 2: Build a stage that uses BOTH access patterns
# ==============================================================================

def build_stage():
    """Author a domain prim with schema data and save the stage."""
    if os.path.exists(USDA_PATH):
        os.remove(USDA_PATH)

    stage = Usd.Stage.CreateNew(USDA_PATH)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # The prim carrying the simulation parameters (e.g. a porous-media domain).
    domain = UsdGeom.Sphere.Define(stage, "/World/PorousDomain")
    domain.GetRadiusAttr().Set(1.5)

    print("\n--- Step 2a: ApplyAPI via the registered codeless schema ---")
    prim = domain.GetPrim()

    # Does the plug registry know our schema? If yes, ApplyAPI works and the
    # prim definition gains typed attributes with FALLBACK values.
    registered = prim.ApplyAPI(SCHEMA_NAME)
    print("    ApplyAPI(%s) -> %s" % (SCHEMA_NAME, registered))
    print("    HasAPI -> %s" % prim.HasAPI(SCHEMA_NAME))

    if registered:
        prim_def = prim.GetPrimDefinition()
        applied = prim_def.GetAppliedAPISchemas() or []
        print("    Prim definition now contains schema: %s" % (SCHEMA_NAME in applied))
        # FALLBACK value: resolves 0.016 from generatedSchema.usda defaults
        # even though nothing has been authored on this prim yet.
        attr = prim.GetAttribute("simulation:timeStep")
        print("    attr.Get() before authoring = %s  <- schema fallback" % attr.Get())

    # Author real values on the schema attributes.
    prim.CreateAttribute("simulation:timeStep", Sdf.ValueTypeNames.Double).Set(0.004)
    prim.CreateAttribute("simulation:solverType", Sdf.ValueTypeNames.String).Set("brinkman")
    prim.CreateAttribute("simulation:maxIterations", Sdf.ValueTypeNames.Int).Set(250)
    prim.CreateAttribute("simulation:initialVelocity",
                         Sdf.ValueTypeNames.Point3fArray).Set(
        [Gf.Vec3f(0.0, 0.0, 0.1), Gf.Vec3f(0.0, 0.0, 0.2)])

    print("\n--- Step 2b: Read the same data via the convention wrapper ---")
    sim = SimulationData(prim)
    print("    wrapper.is_valid()      = %s" % sim.is_valid())
    print("    wrapper.get_time_step() = %s  (authored above)" % sim.get_time_step())
    print("    wrapper.get_solver_type() = %s" % sim.get_solver_type())
    print("    wrapper.get_max_iterations() = %s" % sim.get_max_iterations())

    # The wrapper can ALSO attach the data to a prim that never used ApplyAPI.
    second = UsdGeom.Cube.Define(stage, "/World/SecondDomain").GetPrim()
    sim2 = SimulationData(second)
    sim2.set_time_step(0.008)
    sim2.set_solver_type("darcy")
    sim2.set_max_iterations(1000)
    print("    SecondDomain via wrapper only: timeStep=%s solver=%s iters=%s"
          % (sim2.get_time_step(), sim2.get_solver_type(), sim2.get_max_iterations()))

    stage.GetRootLayer().Save()
    print("  [+] Saved stage: %s" % os.path.basename(USDA_PATH))
    return stage



# ==============================================================================
# Part 3: Reload the saved stage and verify persistence
# ===============================================================================

def verify_saved_stage():
    """Reopen the stage and read schema data back from disk."""
    print("\\n--- Step 3: Reload from disk ---")
    stage = Usd.Stage.Open(USDA_PATH)
    for path in ("/World/PorousDomain", "/World/SecondDomain"):
        prim = stage.GetPrimAtPath(path)
        print("    %s" % path)
        api = prim.GetMetadata("apiSchemas")
        items = api.GetAddedOrExplicitItems() if api else []
        print("        apiSchemas: %s" % list(items))
        for name in ("timeStep", "solverType", "maxIterations"):
            attr = prim.GetAttribute("simulation:%s" % name)
            print("        simulation:%-13s = %s" % (name, attr.Get()))


def main():
    print("=" * 80)
    print("Tutorial 16: Custom Schemas - Codeless API Schema + Convention Wrapper")
    print("=" * 80)

    stage = build_stage()
    verify_saved_stage()

    print("\\n" + "=" * 80)
    print("Tutorial 16 complete!")
    print("USD output:  %s" % USDA_PATH)
    print("Plugin dir:  %s" % PLUGIN_DIR)
    print("=" * 80)


if __name__ == "__main__":
    main()



