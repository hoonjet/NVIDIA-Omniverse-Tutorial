# Omniverse Study Guide - Learning Order and Practice Guide

> **Official Link:** https://www.nvidia.com/en-us/omniverse/

---

## 1. Document Reading Order

It is recommended to read the documents in the following order:

| Order | Document | Location | Purpose |
|-------|----------|----------|---------|
| 1 | **Omniverse_Learning_Guide.md** | `E:\omniverse_env\` | Understand the overall curriculum and environment overview |
| 2 | **Virtual_Environment_Usage_Guide.md** | `E:\omniverse_env\` | Learn virtual environment activation/usage |
| 3 | **USD_Basics_Manual.md** | `E:\omniverse_env\tutorials\` | Theoretical background for tutorials 01-05 |
| 4 | **Kit_API_Manual.md** | `E:\omniverse_env\tutorials\` | Theoretical background for tutorials 06-08 |
| 5 | **PhysicsNeMo_Integration_Manual.md** | `E:\omniverse_env\tutorials\` | Theoretical background for tutorials 09-11 |

---

## 2. Practice Progression

### Step 0: Environment Preparation (10 minutes)

```batch
:: Open Command Prompt (cmd)
cd E:\omniverse_env
Scripts\activate

:: Verify environment
python test_usd_import.py
```

> ✅ When the `(omniverse_env)` prompt appears and the USD version is displayed, the environment is ready

---

### Step 1: USD Basics (01-05) — Approximately 1~2 hours

This step covers the core concepts of USD (Universal Scene Description), the foundation of Omniverse.

| Order | Tutorial | Key Learning Content | Estimated Time |
|-------|----------|----------------------|----------------|
| ① | `01_usd_basics.py` | Basic structure of Stage, Prim, and Attribute | 15 min |
| ② | `02_usd_geometry.py` | Creating shapes (Cube, Sphere, Cone, Cylinder) and Transforms (translate/rotate/scale) | 20 min |
| ③ | `03_usd_materials.py` | Display Color, PBR Material (UsdPreviewSurface), Material Binding | 25 min |
| ④ | `04_usd_animation.py` | TimeCode, TimeSample, keyframe animation (translate/rotate/scale/color) | 25 min |
| ⑤ | `05_usd_assembly.py` | Reference (file referencing), Variant (alternate configurations), Instance (instancing) | 30 min |

**How to practice:**

```batch
:: Run each tutorial in order
python tutorials\01_usd_basics.py
python tutorials\02_usd_geometry.py
python tutorials\03_usd_materials.py
python tutorials\04_usd_animation.py
python tutorials\05_usd_assembly.py
```

**Practice tips:**

- After running each tutorial, open the generated `.usda` file in the `tutorials\output\` folder with Notepad:
  ```batch
  notepad tutorials\output\01_usd_basics.usda
  ```
- `.usda` files are in ASCII text format, so you can directly inspect the internal structure
- In tutorial 03, it is important to understand the meaning of PBR material properties (albedo, roughness, metalness)
- The Reference/Variant/Instance concepts in tutorial 05 are core to real production pipelines

---

### Step 2: Omniverse Kit API Concepts (06-08) — Approximately 1~1.5 hours

This step covers the concepts of the application framework that Omniverse builds on top of USD.

| Order | Tutorial | Key Learning Content | Estimated Time |
|-------|----------|----------------------|----------------|
| ⑥ | `06_kit_extensions.py` | Extension structure (extension.toml, lifecycle), Custom Schema | 20 min |
| ⑦ | `07_omniverse_connector.py` | CSV/JSON → USD conversion pipeline, reusable Connector class | 25 min |
| ⑧ | `08_live_sync.py` | Layer Composition, Multi-Client collaboration, Change Tracking, Conflict Resolution | 30 min |

**How to practice:**

```batch
python tutorials\06_kit_extensions.py
python tutorials\07_omniverse_connector.py
python tutorials\08_live_sync.py
```

**Practice tips:**

- After running tutorial 06, open the Extension template generated in `tutorials\output\my_extension\`:
  ```batch
  notepad tutorials\output\my_extension\extension.toml
  notepad tutorials\output\my_extension\extension.py
  ```
- In tutorial 07, CSV/JSON sample data is generated in `tutorials\output\connector_data\`. Try modifying it to convert different data to USD
- The Layer Composition concept (stronger opinion wins) in tutorial 08 is central to Omniverse collaboration

> ⚠️ **Note:** The current system (Quadro P4000, Pascal architecture) does not have RT cores, so full Kit RTX rendering is not available. These tutorials use USD-only APIs to simulate Kit concepts. In an RTX GPU environment, the same concepts apply directly using `omni.kit.*` APIs.

---

### Step 3: PhysicsNeMo Integration (09-11) — Approximately 1.5~2 hours

This step covers the pipeline for converting PhysicsNeMo model outputs (learned in `E:\physicsnemo_env`) into USD 3D scenes.

| Order | Tutorial | Key Learning Content | Estimated Time |
|-------|----------|----------------------|----------------|
| ⑨ | `09_physicsnemo_to_usd.py` | Scalar field → point cloud, height field, colormap | 30 min |
| ⑩ | `10_simulation_visual.py` | Time-varying animated colormaps, height fields, velocity vector fields | 35 min |
| ⑪ | `11_digital_twin.py` | End-to-end pipeline: geometry → simulation → visualization → metadata | 40 min |

**How to practice:**

```batch
python tutorials\09_physicsnemo_to_usd.py
python tutorials\10_simulation_visual.py
python tutorials\11_digital_twin.py
```

**Practice tips:**

- Tutorial 09 visualizes Darcy flow (Pressure, Velocity) data in 3D. Open `tutorials\output\physicsnemo_data\darcy_flow.json` to inspect the simulation data structure
- Tutorial 10 converts transient heat transfer data across 10 timesteps into USD animation
- Tutorial 11 builds a heat exchanger digital twin. After running, open `tutorials\output\digital_twin_report.txt` to review the simulation summary

---

### Step 4: Real PhysicsNeMo Model Integration (Optional, Advanced)

This step applies the patterns from tutorials 09-11 to convert actual inference results from models trained in `E:\physicsnemo_env` into USD.

```
E:\physicsnemo_env (Python 3.10)     E:\omniverse_env (Python 3.8)
   │                                      │
   │  1. Model inference → save .npy/.json  │
   └──── file exchange ─────────────────────┘
                                          │
                                          ▼
                                   2. Load .npy → convert to USD
                                      (using tutorial 09 pattern)
```

**Data exchange directory:**

```
E:\omniverse_env\tutorials\output\physicsnemo_data\
    ↑ Save .npy/.json from physicsnemo_env
    ↓ Load and convert to USD in omniverse_env
```

---

## 3. Overall Study Schedule Summary

| Step | Content | Estimated Time | Prerequisite |
|------|---------|-----------------|--------------|
| 0 | Environment preparation and verification | 10 min | None |
| 1 | USD Basics (01-05) | 1~2 hours | Step 0 completed |
| 2 | Kit API Concepts (06-08) | 1~1.5 hours | Step 1 completed |
| 3 | PhysicsNeMo Integration (09-11) | 1.5~2 hours | Steps 1 and 2 completed |
| 4 | Real model integration (advanced) | Self-paced | Step 3 + PhysicsNeMo study completed |

**Total estimated study time: approximately 4~6 hours**

---

## 4. Additional Study Tips

1. **Try modifying the tutorial scripts directly**: For example, in tutorial 02, change the shape colors, sizes, and positions, then run to see the results
2. **Compare generated .usda files**: Comparing .usda files before and after running tutorials helps deepen your understanding of USD structure
3. **Read the manuals alongside tutorials**: Each tutorial set has a detailed manual (USD_Basics_Manual.md, Kit_API_Manual.md, PhysicsNeMo_Integration_Manual.md) with theoretical explanations
4. **Refer to official documentation**:
   - [USD Official Documentation](https://openusd.org/release/index.html)
   - [Omniverse Kit SDK Documentation](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/)
   - [USD Cookbook](https://openusd.org/release/tutorials_usd_tutorials.html)

---

## 5. Tutorial Output Files

After running each tutorial, USD files are generated in the `tutorials\output\` directory:

```
tutorials\output\
├── 01_usd_basics.usda              ← Basic Stage (cube, sphere, cylinder, camera)
├── 02_usd_geometry.usda            ← 6 shapes + transforms
├── 03_usd_materials.usda           ← PBR materials + binding
├── 04_usd_animation.usda           ← Animation (translate, rotate, scale, color)
├── 05_usd_assembly.usda            ← Scene assembly (references, variants, instancing)
├── assets\                         ← Referenced asset files (table, chair, lamp)
├── 06_kit_extensions.usda          ← Extension structure demo
├── my_extension\                   ← Kit extension template
├── 07_omniverse_connector.usda    ← Data connector results
├── connector_data\                  ← CSV/JSON sample data
├── 08_live_sync\                    ← Live Sync demo files
├── 09_physicsnemo_to_usd.usda     ← Darcy flow visualization
├── physicsnemo_data\               ← Simulation data (JSON)
├── 10_simulation_visual.usda       ← Animated simulation
├── 11_digital_twin.usda            ← Digital twin (heat exchanger)
└── digital_twin_report.txt         ← Simulation summary report
```

### Viewing .usda files

`.usda` files are in ASCII text format and can be opened with Notepad:

```batch
notepad E:\omniverse_env\tutorials\output\01_usd_basics.usda
```

---

## 6. Troubleshooting

### Issue: `ModuleNotFoundError: No module named 'pxr'`

**Cause:** Virtual environment is not activated

**Solution:**
```batch
cd E:\omniverse_env
Scripts\activate
python -c "from pxr import Usd; print(Usd.GetVersion())"
```

### Issue: `FileExistsError` when creating USD stage

**Cause:** A file with the same name already exists

**Solution:** The tutorial scripts are designed to automatically delete existing files. To manually delete:
```batch
del E:\omniverse_env\tutorials\output\01_usd_basics.usda
```

### Issue: Error when running `Scripts\activate`

**Cause:** Execution policy restriction (PowerShell)

**Solution:**
```batch
:: Use Command Prompt (cmd) or
:: Change execution policy in PowerShell:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 7. Summary: Command Cheat Sheet

| Action | Command |
|--------|---------|
| Activate virtual environment | `cd E:\omniverse_env && Scripts\activate` |
| Deactivate virtual environment | `deactivate` |
| Verify environment | `python test_usd_import.py` |
| Run tutorial 01 | `python tutorials\01_usd_basics.py` |
| Run all tutorials sequentially | `python tutorials\01_usd_basics.py` through `python tutorials\11_digital_twin.py` |
| View USD file contents | `notepad tutorials\output\01_usd_basics.usda` |
| List installed packages | `pip list` |
| Check Python version | `python --version` |
| Check USD version | `python -c "from pxr import Usd; print(Usd.GetVersion())"` |
