# Tutorial 16: Custom Schemas - Codeless API Schema + Convention Wrapper

## Overview

USD lets you attach domain-specific data to prims. This tutorial shows the
two standard no-C++ approaches:

1. **Codeless schema** - a JSON plugin + a `generatedSchema.usda` file that
   registers `SimulationDataAPI` with the `UsdSchemaRegistry`. After
   registration, `prim.ApplyAPI("SimulationDataAPI")` works, and the schema's
   attributes (with their default values) appear in the prim definition as
   **fallbacks** - before anything is authored.
2. **Convention wrapper** - a small Python class (`SimulationData`) that
   authors/reads `simulation:*` namespaced properties. Zero registration,
   works everywhere, and reads data authored by either path because both use
   the same property names.

## Files

- `16_custom_schemas.py` - the tutorial script
- `output/16_custom_schemas.usda` - generated stage
- `output/schema_plugin/plugInfo.json` - the codeless-schema plugin manifest
- `output/schema_plugin/resources/generatedSchema.usda` - schema definition

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\16_custom_schemas\16_custom_schemas.py
```

## How the codeless schema works

The plugin is a `"Type": "resource"` plugin (no compiled library). Inside
`plugInfo.json`, the `Info.Types` map registers the schema class:

```json
"SimulationDataAPI": {
    "bases": ["UsdAPISchemaBase"],
    "schemaIdentifier": "SimulationDataAPI",
    "schemaKind": "singleApplyAPI"
}
```

- `schemaKind` - what kind of schema this is. Valid values include
  `singleApplyAPI`, `multipleApplyAPI`, `nonAppliedAPI`, `abstractBase`,
  `concreteTyped`. (Names differ across USD versions; this build uses the
  `*API` suffix form for applied API schemas.)
- `bases` - the registry parent. API schemas derive from `UsdAPISchemaBase`.
- The `resources/generatedSchema.usda` file declares the class and its
  properties with default values:

```
class SimulationDataAPI "SimulationDataAPI"
{
    custom double simulation:timeStep = 0.016
    custom string simulation:solverType = "darcy"
    custom int simulation:maxIterations = 500
    custom point3f[] simulation:initialVelocity = []
}
```

**Critical import-order rule**: the plug registry is populated when the pxr
modules load, so the script sets `PXR_PLUGINPATH_NAME` to the plugin folder
BEFORE `from pxr import ...`. This is why the pxr import appears late in the
script (with a `noqa` comment).

## Sample output

```
ApplyAPI(SimulationDataAPI) -> True
HasAPI -> True
Prim definition now contains schema: True
attr.Get() before authoring = 0.016  <- schema fallback

wrapper.get_time_step() = 0.004  (authored above)

/apiSchemas on reload: ['SimulationDataAPI']
simulation:timeStep = 0.004
```

The saved stage shows the applied schema metadata on the prim:

```
def Sphere "PorousDomain" (
    prepend apiSchemas = ["SimulationDataAPI"]
)
{
    double radius = 1.5
    point3f[] simulation:initialVelocity = [(0, 0, 0.1), (0, 0, 0.2)]
    int simulation:maxIterations = 250
    string simulation:solverType = "brinkman"
    double simulation:timeStep = 0.004
}
```

## Key concepts

- **API schema** - a bolt-on bundle of properties (`apiSchemas` list op).
  Composable: many API schemas can attach to one prim. In contrast, an
  *is-a* schema (typed schema like `Sphere`) replaces the prim's type.
- **Fallback values** - declared in the schema definition, returned by
  `attr.Get()` even when nothing is authored on the prim. Excellent for
  sane defaults (time step 0.016 = 1/60 s).
- **Namespacing** - properties are prefixed (`simulation:`) so data from
  different tools coexists on one prim without collisions.
- **singleApply vs multipleApply** - `singleApplyAPI` attaches once per
  prim; `multipleApplyAPI` (like `CollectionAPI`) attaches once per
  instance name (`CollectionAPI:lights`).

## Exercises

1. Add `simulation:convergenceTol` (double, default 1e-6) to the schema
   definition and print its fallback value.
2. Author the schema data on a prim WITHOUT calling ApplyAPI (wrapper only)
   and inspect what differs in the saved .usda.
3. Convert the schema to `multipleApplyAPI` named `SimSourceAPI` so a prim
   can carry several sim sources (`SimSourceAPI:thermal`, `SimSourceAPI:flow`).
