# Omniverse Kit API Tutorial Set - Manual

> **Location:** `E:\omniverse_env\tutorials\`
> **Prerequisites:** Complete the USD Basics Tutorial Set (01-05) first
> **Note:** These tutorials use USD-only APIs to simulate Kit concepts. Full Kit functionality requires an Omniverse installation with RTX GPU.

---

## Table of Contents

1. [Overview](#1-overview)
2. [Tutorial 06: Kit Extensions](#2-tutorial-06-kit-extensions)
3. [Tutorial 07: Data Connectors](#3-tutorial-07-data-connectors)
4. [Tutorial 08: Live Sync](#4-tutorial-08-live-sync)
5. [Architecture Diagram](#5-architecture-diagram)
6. [Troubleshooting](#6-troubleshooting)

---

## 1. Overview

This tutorial set covers the **Omniverse Kit API** layer — the application framework that sits on top of USD. While the USD Basics set covered the 3D scene description format, this set covers how Omniverse extends USD with:

- **Extensions**: Modular plugins that add functionality to Kit
- **Connectors**: Data pipelines that convert external formats to USD
- **Live Sync**: Real-time collaborative editing of USD scenes

### Important Note on GPU Limitations

Since the current system has a **Quadro P4000** (Pascal architecture, no RT cores), full Omniverse Kit with RTX rendering is not available. These tutorials are designed to work with **USD-only APIs** that simulate Kit concepts, so you can learn the patterns and architecture without a full Omniverse installation.

When you later have access to an RTX GPU, the same concepts apply directly — you would just use `omni.kit.*` APIs instead of the simulated versions.

---

## 2. Tutorial 06: Kit Extensions

**File:** `06_kit_extensions.py`
**Output:** `tutorials/output/my_extension/` (extension template) + `tutorials/output/06_kit_extensions.usda`

### What It Does

1. **Creates an Extension Template** - Generates the file structure of a real Kit extension:
   - `extension.toml` - Configuration file with metadata and dependencies
   - `extension.py` - Python module with `on_startup()` / `on_shutdown()` lifecycle
   - `__init__.py` - Package init

2. **Simulates Extension Lifecycle** - Imports the extension module and calls the lifecycle functions, mimicking how Kit loads/unloads extensions

3. **Demonstrates Custom Schemas** - Shows how extensions define custom data on USD prims using namespaced attributes (e.g., `simulation:type`, `simulation:timeStep`)

4. **Extension Configuration Pattern** - Shows how extensions store their settings as USD data on the stage

### Extension File Structure

```
my_extension/
├── extension.toml    # Metadata, dependencies, entry points
├── __init__.py       # Package init (imports lifecycle functions)
└── extension.py      # on_startup() and on_shutdown() functions
```

### Key Concept: Extension Lifecycle

```python
def on_startup(ext_obj):
    """Called when Kit loads the extension."""
    # Initialize resources, register UI, set up listeners
    pass

def on_shutdown(ext_obj):
    """Called when Kit unloads the extension."""
    # Clean up resources, unregister UI, remove listeners
    pass
```

### Key Concept: Custom Attributes

Extensions often define domain-specific data using namespaced attributes:

```python
# Create a custom attribute with a namespace prefix
prim.CreateAttribute("simulation:temperature", Sdf.ValueTypeNames.Float).Set(25.0)
prim.CreateAttribute("simulation:velocity", Sdf.ValueTypeNames.Float3).Set(Gf.Vec3f(1.0, 0.0, 0.0))
```

---

## 3. Tutorial 07: Data Connectors

**File:** `07_omniverse_connector.py`
**Output:** `tutorials/output/07_omniverse_connector.usda` + data files in `tutorials/output/connector_data/`

### What It Does

1. **CSV to USD Connector** - Reads point cloud data from CSV and creates colored USD spheres:
   - Generates a spiral point cloud with temperature values
   - Maps temperature to color (blue=cold → green → red=hot)
   - Stores temperature as a custom attribute on each point

2. **JSON to USD Connector** - Recursively converts a JSON scene description to USD prims:
   - Handles Cube, Cylinder, Sphere, and Xform types
   - Preserves hierarchy (parent-child relationships)
   - Stores metadata as custom attributes

3. **Reusable Connector Class** - A `DataConnector` class that:
   - Registers handlers for different data types
   - Processes files through registered handlers
   - Tracks processing statistics

4. **Batch Processing** - Demonstrates processing multiple data sources in one run

### Connector Architecture

```
External Data          Connector Module           USD Scene
┌──────────┐         ┌──────────────────┐      ┌──────────┐
│ CSV file │ ──────► │ CSV Handler      │ ───► │ USD Prims│
│ JSON file│ ──────► │ JSON Handler     │ ───► │ USD Prims│
│ HDF5 file│ ──────► │ HDF5 Handler     │ ───► │ USD Prims│
└──────────┘         └──────────────────┘      └──────────┘
```

### Key API: DataConnector Class

```python
connector = DataConnector(stage)
connector.register_handler("csv", csv_to_usd_connector)
connector.register_handler("json", json_to_usd_connector)
connector.process("data.csv", "csv", parent_path="/World/SensorData")
```

### Color Mapping Pattern

The CSV connector maps scalar values to RGB colors:

```
Temperature:  20°C (min)  ──────►  35°C (mid)  ──────►  50°C (max)
Color:        Blue (0,0,1)  ───►  Green (0,1,0)  ───►  Red (1,0,0)
```

---

## 4. Tutorial 08: Live Sync

**File:** `08_live_sync.py`
**Output:** `tutorials/output/live_sync/` (multiple USD files)

### What It Does

1. **Layer Composition Demo** - Shows how USD combines multiple layers:
   - Creates a base layer (cube: size=2.0, color=red)
   - Creates an override layer (cube: size=5.0, color=blue)
   - Shows that the override (stronger opinion) wins

2. **Multi-Client Collaboration** - Simulates two clients (Alice and Bob) editing the same scene:
   - Alice changes the cube's size
   - Bob changes the cube's color
   - Both publish their changes
   - Final scene reflects both edits

3. **Change Tracking** - Uses `Tf.Notice` to track stage changes:
   - Registers a listener for `Usd.Notice.ObjectsChanged`
   - Logs all prim creations and attribute modifications
   - Shows how real-time change notification works

4. **Conflict Resolution** - Demonstrates how conflicting edits are resolved:
   - Two clients set the same attribute to different values
   - Each client's session layer takes precedence locally
   - When published, "last writer wins" on the shared layer

### Layer Strength Hierarchy

```
Strongest ──────────────────────────────────────► Weakest

Session Layer  >  Root Layer  >  Sublayers  >  References
(per-client)      (shared)       (included)     (external)
```

### Key Concept: Session Layer

Each client has a **session layer** — the strongest layer — for local overrides:

```python
# Create a session layer for this client
session_layer = Sdf.Layer.CreateAnonymous("session_alice")
stage.GetSessionLayer().subLayerPaths.append(session_layer.identifier)

# Edits go into the session layer (strongest opinion)
prim.GetAttribute("size").Set(4.0)  # Only Alice sees this until published
```

### Key Concept: Change Notification

```python
from pxr import Tf

def on_stage_changed(notice, sender):
    if isinstance(notice, Usd.Notice.ObjectsChanged):
        for path in notice.GetResyncedPaths():
            print(f"Prim changed: {path}")

# Register the listener
listener = Tf.Notice.Register(
    Usd.Notice.ObjectsChanged, on_stage_changed, stage
)

# ... make changes ...

# Clean up
listener.Revoke()
```

---

## 5. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Omniverse Kit Application                     │
├─────────────────────────────────────────────────────────────────┤
│  Extensions (Tutorial 06)                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                         │
│  │ Ext A    │ │ Ext B    │ │ Ext C    │                         │
│  │ (UI)     │ │ (Tools)  │ │ (Import) │                         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                         │
│       │            │            │                                │
├───────┴────────────┴────────────┴────────────────────────────────┤
│  Connectors (Tutorial 07)                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                         │
│  │ CSV → USD│ │ JSON→USD │ │ CAD→USD  │                         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘                         │
│       │            │            │                                │
├───────┴────────────┴────────────┴────────────────────────────────┤
│  Live Sync (Tutorial 08)                                        │
│  ┌──────────┐                    ┌──────────┐                    │
│  │ Client A │◄─── Nucleus ────►│ Client B │                    │
│  │ Session  │     Server         │ Session  │                    │
│  └──────────┘                    └──────────┘                    │
├─────────────────────────────────────────────────────────────────┤
│  USD Core (Tutorials 01-05)                                     │
│  Stage → Prims → Attributes → References → Variants             │
└─────────────────────────────────────────────────────────────────┘
```

---

## 6. Troubleshooting

### Problem: `ImportError: No module named 'my_extension'`

**Cause:** The extension directory is not on the Python path.

**Solution:** The tutorial script adds the parent directory to `sys.path` automatically. If running manually:

```python
import sys
sys.path.insert(0, "E:/omniverse_env/tutorials/output")
import my_extension
```

### Problem: `Tf.Notice.Register` not receiving callbacks

**Cause:** The listener must be registered BEFORE making changes, and the stage must be modified through the same stage object.

**Solution:**
```python
# Register listener FIRST
listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, callback, stage)

# THEN make changes
cube = UsdGeom.Cube.Define(stage, "/World/Cube")  # This triggers the callback
```

### Problem: Session layer edits not visible

**Cause:** The session layer must be properly added to the stage's session layer sublayers.

**Solution:**
```python
# Create an anonymous session layer
session = Sdf.Layer.CreateAnonymous("my_session")

# Add it to the stage's session layer
stage.GetSessionLayer().subLayerPaths.append(session.identifier)

# Now edits go through the session layer
```

---

## Next Steps

After completing this tutorial set, proceed to:
- **Tutorial Set 3: PhysicsNeMo Integration** (tutorials 09-11)
  - Convert PhysicsNeMo simulation results to USD scenes
  - Visualize simulation data in 3D
  - Build a digital twin pipeline
