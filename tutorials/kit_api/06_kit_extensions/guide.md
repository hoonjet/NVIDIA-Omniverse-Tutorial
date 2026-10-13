# Tutorial 06: Kit Extensions

> **Category:** Kit API · **Script:** `06_kit_extensions.py`

## Overview

Introduces the **Omniverse Kit extension** model — the modular plugin
architecture that sits on top of USD. This tutorial generates a real extension
file structure (`extension.toml`, `extension.py`, `__init__.py`), simulates the
Kit load/unload lifecycle, and demonstrates custom (namespaced) attributes on
USD prims.

> **Note:** These tutorials use USD-only APIs to *simulate* Kit concepts. Full
> Kit with RTX rendering requires an RTX GPU. The patterns learned here apply
> directly to real `omni.kit.*` extensions.

## Prerequisites

- Complete the **USD Basics Tutorial Set (01–05)** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\kit_api\06_kit_extensions\06_kit_extensions.py
```

## What It Does

1. **Creates an Extension Template** — generates the file structure of a real
   Kit extension:
   - `extension.toml` — configuration with metadata and dependencies
   - `extension.py` — Python module with `on_startup()` / `on_shutdown()` lifecycle
   - `__init__.py` — package init
2. **Simulates the Extension Lifecycle** — imports the module and calls the
   lifecycle functions, mimicking how Kit loads/unloads extensions.
3. **Demonstrates Custom Schemas** — defines domain-specific data on USD prims
   using namespaced attributes (e.g. `simulation:type`, `simulation:timeStep`).
4. **Stores Extension Configuration** — persists extension settings as USD data
   on the stage.

## Extension File Structure

```
my_extension/
├── extension.toml    # Metadata, dependencies, entry points
├── __init__.py       # Package init (imports lifecycle functions)
└── extension.py      # on_startup() and on_shutdown() functions
```

## Key API / Concepts

```python
def on_startup(ext_obj):
    """Called when Kit loads the extension."""
    # Initialize resources, register UI, set up listeners
    ...

def on_shutdown(ext_obj):
    """Called when Kit unloads the extension."""
    # Clean up resources, unregister UI, remove listeners
    ...

# Custom namespaced attribute
prim.CreateAttribute("simulation:temperature", Sdf.ValueTypeNames.Float).Set(25.0)
prim.CreateAttribute("simulation:velocity", Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(1,0,0))
```

## Output

```
tutorials\kit_api\06_kit_extensions\output\
├── 06_kit_extensions.usda   # Stage with custom extension attributes
└── my_extension\
    ├── extension.toml       # Extension config (metadata + dependencies)
    ├── __init__.py          # Package init
    └── extension.py         # on_startup() / on_shutdown() lifecycle
```

## Notes

- **Safe to re-run:** The script removes an existing `.usda` before creating a
  new one, so it can be run repeatedly without manual cleanup.
- The script adds the output directory to `sys.path` so it can import
  `my_extension`.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `ImportError: No module named 'my_extension'` | Output dir not on `sys.path` | The script adds it automatically; manually: `sys.path.insert(0, ".../output")` |
| Lifecycle functions not called | Ran the file directly without importing | The script simulates loading by importing and calling `on_startup`/`on_shutdown` |

## Next Steps

Continue to **Tutorial 07: Omniverse Data Connectors**.
