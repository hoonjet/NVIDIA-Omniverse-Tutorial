# Omniverse Environment — Tutorials

A hands-on, progressively-structured learning path for **NVIDIA Omniverse**,
built on **USD (Universal Scene Description)** 
Each tutorial is self-contained and writes its output into its own `output\` folder.

---

## Directory Structure

```
E:\omniverse_env\
├── tutorials\                       # All 14 tutorials, grouped by category
│   ├── usd_basics\                  # Tutorial Set 1: USD fundamentals
│   │   ├── 01_usd_basics\
│   │   │   ├── 01_usd_basics.py
│   │   │   ├── guide.md
│   │   │   └── output\
│   │   ├── 02_usd_geometry\   …
│   │   ├── 03_usd_materials\  …
│   │   ├── 04_usd_animation\  …
│   │   └── 05_usd_assembly\   …
│   ├── kit_api\                     # Tutorial Set 2: Omniverse Kit API
│   │   ├── 06_kit_extensions\  …
│   │   ├── 07_omniverse_connector\ …
│   │   └── 08_live_sync\  …
│   ├── physicsnemo_integration\     # Tutorial Set 3: PhysicsNeMo → USD
│   │   ├── 09_physicsnemo_to_usd\  …
│   │   ├── 10_simulation_visual\   …
│   │   └── 11_digital_twin\        …
│   └── usd_advanced\                # Tutorial Set 4: Advanced USD authoring
│       ├── 12_usd_lighting\         …
│       ├── 13_usd_physics\          …
│       └── 14_skeletal_animation\   …
├── docs\                            # Reference manuals
│   ├── USD_Basics_Manual.md
│   ├── Kit_API_Manual.md
│   └── PhysicsNeMo_Integration_Manual.md
├── tools\                           # Visualization & inspection tools
│   ├── scene_inspector.py           # Text-based prim tree (no deps)
│   ├── visualize.py                 # 3D matplotlib visualizer (needs matplotlib)
│   ├── verify_all_tutorials.py      # Programmatic verification (193 checks)
│   ├── verification_report.md       # Detailed verification report
│   └── guide.md                     # Tool usage guide
├── Include\                         # Python headers (venv)
├── Lib\                             # Python packages (venv)
├── Scripts\                         # venv executables (activate, python.exe)
├── test_usd_import.py               # Quick USD import sanity check
└── pyvenv.cfg                       # Virtual environment config
```

Each tutorial folder follows the same layout:

```
<tutorial>\
├── <tutorial>.py     # The runnable tutorial script
├── guide.md          # English how-to guide for this tutorial
└── output\           # Generated USD files & data (created on first run)
```

---

## Quick Start

### 1. Activate the virtual environment

```batch
cd YOUR_DIRECTORY\
Scripts\activate
```

### 2. Verify USD is available

```batch
python -c "from pxr import Usd; print(Usd.GetVersion())"
```

Or run the bundled sanity check:

```batch
python test_usd_import.py
```

### 3. Run a tutorial

```batch
python tutorials\usd_basics\01_usd_basics\01_usd_basics.py
```

Open the generated `.usda` in a text editor or a USD viewer (e.g. USDView,
Omniverse USD Composer) to inspect the scene.

### 4. Visually verify the output

Since USDView is not available in this environment, two tools are provided in
`tools\` for visual verification:

**Text-based scene inspector** (no extra dependencies):

```batch
python tools\scene_inspector.py tutorials\usd_basics\01_usd_basics\output\01_usd_basics.usda
```

**3D matplotlib visualizer** (requires `pip install matplotlib`):

```batch
# Interactive 3D window (rotate with mouse):
python tools\visualize.py tutorials\usd_advanced\12_usd_lighting\output\12_usd_lighting.usda

# Save as PNG:
python tools\visualize.py tutorials\usd_advanced\13_usd_physics\output\13_usd_physics.usda --save --no-show

# Visualize all tutorials at once:
python tools\visualize.py --all --save --no-show
```

See `tools\guide.md` for full details.

### 5. Programmatically verify all tutorials

To confirm that every tutorial produced correct USD output (prims, schemas,
attributes, relationships, time-sampled values), run the verification script:

```batch
python tools\verify_all_tutorials.py
```

This runs **193 automated checks** across all 14 tutorials — no GPU or RTX
required. Expected output:

```
SUMMARY: 193 passed, 0 failed, 193 total
All 14 tutorials verified successfully!
```

See `tools\verification_report.md` for a detailed per-tutorial breakdown.

---

## Tutorial Index

### Set 1 — USD Basics (`tutorials\usd_basics\`)

Foundational USD concepts: stages, prims, attributes, geometry, materials,
animation, and scene composition.

| # | Tutorial | Key Topics | Output |
|---|----------|------------|-------|
| 01 | [USD Basics](tutorials/usd_basics/01_usd_basics/guide.md) | Stage, Prim, Attribute, Schema | `01_usd_basics.usda` |
| 02 | [USD Geometry](tutorials/usd_basics/02_usd_geometry/guide.md) | Xformable, translate/rotate/scale order | `02_usd_geometry.usda` |
| 03 | [USD Materials](tutorials/usd_basics/03_usd_materials/guide.md) | PBR materials, UsdPreviewSurface, binding | `03_usd_materials.usda` |
| 04 | [USD Animation](tutorials/usd_basics/04_usd_animation/guide.md) | Time samples, keyframes, timeline | `04_usd_animation.usda` |
| 05 | [USD Assembly](tutorials/usd_basics/05_usd_assembly/guide.md) | References, variants, instancing, payloads | `05_usd_assembly.usda` + `assets\` |

### Set 2 — Kit API (`tutorials\kit_api\`)

The Omniverse Kit extension model, data connectors, and live collaboration.

| # | Tutorial | Key Topics | Output |
|---|----------|------------|-------|
| 06 | [Kit Extensions](tutorials/kit_api/06_kit_extensions/guide.md) | extension.toml, lifecycle, custom schemas | `06_kit_extensions.usda` + `my_extension\` |
| 07 | [Data Connectors](tutorials/kit_api/07_omniverse_connector/guide.md) | CSV→USD, JSON→USD, connector pattern | `07_omniverse_connector.usda` + `connector_data\` |
| 08 | [Live Sync](tutorials/kit_api/08_live_sync/guide.md) | Layer composition, session layers, change tracking | `live_sync\` (5 `.usda` layers) |

### Set 3 — PhysicsNeMo Integration (`tutorials\physicsnemo_integration\`)

Connecting NVIDIA PhysicsNeMo simulation data to USD for visualization.

| # | Tutorial | Key Topics | Output |
|---|----------|------------|-------|
| 09 | [PhysicsNeMo to USD](tutorials/physicsnemo_integration/09_physicsnemo_to_usd/guide.md) | Darcy flow, point clouds, height fields | `09_physicsnemo_to_usd.usda` + `physicsnemo_data\` |
| 10 | [Simulation Visualization](tutorials/physicsnemo_integration/10_simulation_visual/guide.md) | Transient data, animated color maps, vector fields | `10_simulation_visual.usda` |
| 11 | [Digital Twin](tutorials/physicsnemo_integration/11_digital_twin/guide.md) | End-to-end pipeline, time-sampled sim data, report | `11_digital_twin.usda` + `digital_twin_report.txt` |

### Set 4 — USD Advanced (`tutorials\usd_advanced\`)

Advanced USD authoring: lighting, physics, skeletal animation, and other schema
sets beyond geometry and materials. These run on pure USD authoring APIs — no
GPU, no renderer, no Kit runtime required.

| # | Tutorial | Key Topics | Output |
|---|----------|------------|--------|
| 12 | [USD Lighting](tutorials/usd_advanced/12_usd_lighting/guide.md) | UsdLux, DistantLight, DomeLight, RectLight, SphereLight, LightFilter, ShadowAPI | `12_usd_lighting.usda` |
| 13 | [USD Physics](tutorials/usd_advanced/13_usd_physics/guide.md) | UsdPhysics, RigidBodyAPI, CollisionAPI, MassAPI, MeshCollisionAPI, joints, DriveAPI | `13_usd_physics.usda` |
| 14 | [Skeletal Animation](tutorials/usd_advanced/14_skeletal_animation/guide.md) | UsdSkel, Skeleton, Animation, BindingAPI, BlendShape, LBS skinning | `14_skeletal_animation.usda` |

---

## How to Read a Tutorial

Each tutorial folder contains a `guide.md` with: **Overview**, **Prerequisites**,
**How to Run**, **What It Does**, **Key API / Concepts**, **Output**, **Notes**,
and **Troubleshooting**. For deeper background, see the reference manuals in
`docs\`.

---

## Re-running Tutorials

| Tutorials | Existing-file behavior | Action before re-run |
|-----------|------------------------|----------------------|
| 01–05 | **Fail** with `FileExistsError` if output exists | Delete the existing `.usda` (see each guide's Notes) |
| 06–12 | **Auto-remove** existing output before regenerating | None — safe to re-run directly |

---

## Reference Documentation

| Manual | Covers |
|--------|--------|
| [USD Basics Manual](docs/USD_Basics_Manual.md) | Stages, prims, attributes, composition |
| [Kit API Manual](docs/Kit_API_Manual.md) | Extensions, connectors, live sync, Nucleus |
| [PhysicsNeMo Integration Manual](docs/PhysicsNeMo_Integration_Manual.md) | Simulation data → USD, visualization, digital twins |

---

## Environment

- **Python:** 3.x virtual environment at `E:\omniverse_env`
- **USD:** 26.x via `usd-core` (`pip install usd-core`)
- **PhysicsNeMo:** optional — tutorials 09–11 auto-detect and fall back to
  synthetic data when unavailable
- **GPU:** an RTX GPU is required only for full Kit/RTX rendering; the tutorials
  here run on USD APIs and work without a GPU
