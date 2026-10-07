# NVIDIA Omniverse Learning Guide

> **Location:** `E:\omniverse_env\`
> **Virtual Environment:** `E:\omniverse_env\` (Python 3.8 + usd-core 26.3)
> **Official Link:** https://www.nvidia.com/en-us/omniverse/

---

## 1. Overview

This guide is designed to help you learn **USD (Universal Scene Description)**, the core technology of NVIDIA Omniverse, using a virtual environment that does not affect other functionality on the E:\ drive. Following the same pattern as the existing PhysicsNeMo environment built at `E:\physicsnemo_env`, this provides an isolated virtual environment for learning USD/Omniverse concepts.

### Environment Diagram

```
:\
└── omniverse_env\            ← New Omniverse/USD learning environment (Python 3.8, usd-core)
    ├── Scripts\activate.bat  ← Virtual environment activation
    ├── tutorials\            ← 11 tutorial scripts + 3 manuals
    │   ├── 01_usd_basics.py
    │   ├── 02_usd_geometry.py
    │   ├── ...
    │   ├── 11_digital_twin.py
    │   ├── USD_Basics_Manual.md
    │   ├── Kit_API_Manual.md
    │   └── PhysicsNeMo_Integration_Manual.md
    ├── test_usd_import.py    ← Environment verification script
    ├── Omniverse_Learning_Guide_EN.md       ← This file
```

---

## 2. Learning Curriculum

### Tutorial Composition (11 tutorials, 3 sets)

| Set | Tutorial | Topic | Difficulty |
|-----|----------|-------|------------|
| **1. USD Basics** | 01 | USD Basics (Stage, Prim, Attribute) | ★☆☆ |
| | 02 | USD Geometry (shape creation, transforms) | ★☆☆ |
| | 03 | USD Materials (PBR shaders, materials) | ★★☆ |
| | 04 | USD Animation (time samples, keyframes) | ★★☆ |
| | 05 | Scene Assembly (references, variants, instancing) | ★★★ |
| **2. Kit API** | 06 | Kit Extensions (extension structure, lifecycle) | ★★☆ |
| | 07 | Data Connectors (CSV/JSON → USD) | ★★☆ |
| | 08 | Live Sync (collaborative editing, layer composition) | ★★★ |
| **3. PhysicsNeMo Integration** | 09 | PhysicsNeMo → USD (simulation → 3D) | ★★★ |
| | 10 | Simulation Visualization (animation) | ★★★ |
| | 11 | Digital Twin Pipeline (end-to-end pipeline) | ★★★ |

### Recommended Learning Order

```
Step 1: Activate and verify the virtual environment
   ↓
Step 2: Tutorials 01~05 (USD Basics)
   ↓
Step 3: Tutorials 06~08 (Kit API concepts)
   ↓
Step 4: Tutorials 09~11 (PhysicsNeMo integration)
   ↓
Step 5: Convert real PhysicsNeMo model outputs to USD
```

---

## 3. Quick Start

### 3.1 Activate the Virtual Environment

```batch
:: Open Command Prompt (cmd)
cd E:\omniverse_env
Scripts\activate
```

When the prompt changes to `(omniverse_env)`, activation is complete:
```
(omniverse_env) E:\omniverse_env>
```

### 3.2 Verify the Environment

```batch
python test_usd_import.py
```

### 3.3 Run the First Tutorial

```batch
python tutorials\01_usd_basics.py
```

### 3.4 Run All Tutorials Sequentially

```batch
python tutorials\01_usd_basics.py
python tutorials\02_usd_geometry.py
python tutorials\03_usd_materials.py
python tutorials\04_usd_animation.py
python tutorials\05_usd_assembly.py
python tutorials\06_kit_extensions.py
python tutorials\07_omniverse_connector.py
python tutorials\08_live_sync.py
python tutorials\09_physicsnemo_to_usd.py
python tutorials\10_simulation_visual.py
python tutorials\11_digital_twin.py
```

---

## 4. Learning Content Summary

### Set 1: USD Basics (01-05)

USD (Universal Scene Description) is a 3D scene description framework developed by Pixar and adopted by NVIDIA as the foundation of Omniverse.

- **Stage**: The top-level container for a scene
- **Prim**: An individual object in the scene (cube, sphere, camera, etc.)
- **Attribute**: A property of a prim (size, color, position, etc.)
- **Reference**: A link to another USD file for scene composition
- **Variant**: An alternate configuration for an object (e.g., red/blue/green)
- **Instance**: A memory-efficient copy of an object

### Set 2: Kit API (06-08)

Omniverse Kit is an application framework built on top of USD.

- **Extension**: A modular plugin that adds functionality to Kit
- **Connector**: A pipeline that converts external data (CSV, JSON, CAD) to USD
- **Live Sync**: Real-time collaborative editing via Nucleus server
- **Layer Composition**: Combining multiple layer opinions (stronger opinion wins)

> **Note:** The current system (Quadro P4000, Pascal architecture) does not have RT cores, so full Kit RTX rendering is not available. Tutorials 06-08 use USD-only APIs to simulate Kit concepts. In an RTX GPU environment, the same concepts apply directly using `omni.kit.*` APIs.

### Set 3: PhysicsNeMo Integration (09-11)

This set covers the pipeline for converting outputs from PhysicsNeMo models (learned in `E:\physicsnemo_env`) into USD 3D scenes.

- **Scalar field → point cloud**: Represent 2D simulation results as colored spheres
- **Height field**: Map scalar values to 3D heights for intuitive visualization
- **Animation**: Represent time-varying simulation results as USD time samples
- **Digital twin**: Build a virtual model of a physical system (heat exchanger)

### PhysicsNeMo ↔ Omniverse Data Exchange

```
E:\physicsnemo_env\              E:\omniverse_env\
  (Python 3.10, PyTorch)           (Python 3.8, USD)
        │                                │
        │  Model inference results (.npy/.json)
        └──────── file exchange ──────────┘
                                         │
                                         ▼
                                    USD scene (.usda)
```

---

## 5. Output Files

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

## 6. Manual List

| Manual | Location | Content |
|--------|----------|---------|
| USD Basics Manual | `tutorials/USD_Basics_Manual.md` | Detailed explanation of tutorials 01-05 |
| Kit API Manual | `tutorials/Kit_API_Manual.md` | Detailed explanation of tutorials 06-08 |
| PhysicsNeMo Integration Manual | `tutorials/PhysicsNeMo_Integration_Manual.md` | Detailed explanation of tutorials 09-11 |
| Virtual Environment Usage Guide | `Virtual_Environment_Usage_Guide_EN.md` | Virtual environment activation/usage |
| Omniverse Learning Guide | `Omniverse_Learning_Guide_EN.md` | This file (overall learning guide) |
| Omniverse Study Guide | `Omniverse_Study_Guide.md` | Learning order and practice guide |

---

## 7. Next Steps

After completing this tutorial set:

1. **Real PhysicsNeMo Model Integration**: Save inference results from models trained in `E:\physicsnemo_env` as `.npy` files, then load and convert them to USD in `E:\omniverse_env`
2. **Omniverse Installation**: Install Omniverse Kit on a system with an RTX GPU and open the learned USD files in Kit
3. **Nucleus Server**: Set up a Nucleus server to test Live Sync in practice
4. **Custom Extension Development**: Develop your own Kit extensions based on the patterns from tutorial 06

---

## 8. References

- [NVIDIA Omniverse Official Site](https://www.nvidia.com/en-us/omniverse/)
- [USD Official Documentation](https://openusd.org/release/index.html)
- [Pixar USD GitHub](https://github.com/PixarAnimationStudios/USD)
- [Omniverse Kit SDK Documentation](https://docs.omniverse.nvidia.com/kit/docs/kit-manual/latest/)
- [USD Cookbook](https://openusd.org/release/tutorials_usd_tutorials.html)
