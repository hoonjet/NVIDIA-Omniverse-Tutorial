# Tutorial 15: USD Composition Deep Dive - LIVRPS Strength Ordering

## Overview

USD scenes are composed from many layers and many composition "arcs".
When the same property is authored in more than one place, USD must pick a
winner. It does so with a fixed strength ordering called **LIVRPS**
(strongest first):

| Letter | Mechanism  | Strength role                                            |
|--------|------------|----------------------------------------------------------|
| L      | Local      | Direct opinions on the prim (root layer edits) - strongest |
| I      | Inherits   | Opinions broadcast from a class prim                      |
| V      | Variants   | Opinions inside the selected variant                      |
| R      | References | Opinions grafted from referenced asset layers             |
| P      | Payloads   | Same as references but lazily loadable/unloadable         |
| S      | SubLayers  | Whole-layer opinions from the layer stack - weakest       |

This tutorial builds one stage that uses **all six mechanisms at once**,
authors the same custom attribute (`data:material`) through each one, and
then reads the composed result back **together with the layer that won**,
proving the ordering programmatically.

## Files

- `15_composition_livrps.py` - the tutorial script
- `output/15_composition_livrps.usda` - composed root stage
- `output/assets/base_layout.usda` - sublayer A (defines the Floor)
- `output/assets/sim_overrides.usda` - sublayer B (re-authors the Floor)
- `output/assets/robot.usda` - grafted via a reference
- `output/assets/sensor.usda` - grafted via a payload

## Running

```bat
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_pipeline\15_composition_livrps\15_composition_livrps.py
```

## What the script demonstrates

1. **Local wins over everything** - `/World/RobotRef/Arm` carries a
   `reference:alloy-arm` opinion from `robot.usda`, but the local
   `local:painted-over-reference` opinion wins because L precedes R.
2. **Inherits** - `InheritedSphere` inherits `/_class_SharedMaterial`; the
   class opinion `inherit:shared-steel` composes in through an Inherit arc.
3. **Variants are runtime-switchable** - the script flips the `finish`
   variant between `glossy` and `matte`; both `data:material` AND `radius`
   change because opinions live inside the variant.
4. **Payloads** - the `Sensor/Probe` content comes from `sensor.usda`
   through a Payload arc (identical to a reference, but unloadable).
5. **SubLayers** - the Floor is defined in `base_layout.usda` and
   re-authored in `sim_overrides.usda`. The composed value is **blue**
   because the sublayer list is strong-to-weak: the FIRST sublayer wins.

### Sample output

```
OK  LocalSphere     -> local:red-anodized       [arc: Root    | layer: 15_composition_livrps.usda]
OK  InheritedSphere -> inherit:shared-steel     [arc: Inherit | layer: 15_composition_livrps.usda (via /_class_SharedMaterial)]
OK  VariantSphere   -> variant:glossy-ceramic   [arc: Variant | layer: 15_composition_livrps.usda (via /World/VariantSphere{finish=glossy})]
OK  Arm             -> local:painted-over-reference [arc: Root | layer: 15_composition_livrps.usda]
OK  Probe           -> payload:titanium-probe   [arc: Payload | layer: (asset: sensor.usda)]
OK  Floor           -> sublayer:blue-concrete   [arc: Root    | layer: base_layout.usda]

selection=glossy -> data:material=variant:glossy-ceramic, radius=0.40
selection=matte  -> data:material=variant:matte-plastic, radius=0.25
```

The `[arc: ... | layer: ...]` columns are produced by walking
`UsdResolveInfo.GetNode()` (a `PcpNodeRef`). Its `arcType` names the LIVRPS
mechanism that won and its `site.layerStack.layers` lets the script locate
the exact layer file that carried the winning opinion.

## Key concepts

- **Opinions** - a single authored statement about a property in a single
  layer. Composition merges opinions into one resolved value.
- **Strong-to-weak sublayer order** - contrary to intuition, the first
  sublayer in `subLayers` is the strongest sublayer (try swapping the two
  `subLayerPaths` entries and re-running: the Floor turns green).
- **Classes and inherits** - `class _class_SharedMaterial` is never rendered;
  it is a recipe that other prims pull in via `inherits`.
- **Payload unload** - call `prim.Unload()` on a payload prim to drop its
  content from the composed stage (deferred loading for heavy sims).

## Exercises

1. Swap the two entries in `subLayerPaths` and confirm the Floor value
   flips to `sublayer:green-painted`.
2. Delete the local override on `/World/RobotRef/Arm` and confirm the
   reference opinion `reference:alloy-arm` surfaces.
3. Add a second variant (`brushed`) that authors a different radius.
4. Call `stage.GetPrimAtPath('/World/SensorPayload').Unload()` and print
   `stage.ExportToString()` to see what an unloaded payload looks like.
