# Tutorial 05: USD Scene Assembly

> **Category:** USD Basics · **Script:** `05_usd_assembly.py`

## Overview

Brings together the USD composition features that make large scenes practical:
**references**, **variants**, and **instancing**. Builds a small "room" scene by
referencing reusable asset files, switching their look with variants, and
sharing geometry via instancing.

## Prerequisites

- Complete **Tutorials 01–04** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\usd_basics\05_usd_assembly\05_usd_assembly.py
```

## What It Does

1. **Creates Reusable Asset Files** — generates `table.usda`, `chair.usda`, and
   `lamp.usda` under `output\assets\`.
2. **Assembles with References** — composes a room scene that references each
   asset by file path.
3. **Uses Variants** — creates a `Color` variant set so the same asset can
   switch between Red/Green/Blue looks.
4. **Uses Instancing** — marks prims as instanceable so shared geometry is
   stored once and reused.

## Key API Calls

```python
# Add a reference to an external USD file
prim.GetReferences().AddReference("path/to/asset.usda")

# Create a variant set and a variant
variant_set = prim.GetVariantSets().AddVariantSet("Color")
variant_set.AddVariant("Red")
variant_set.SetVariantSelection("Red")

# Edit within a variant context
with variant_set.GetVariantEditContext():
    cube.GetDisplayColorAttr().Set([(1.0, 0.0, 0.0)])

# Mark a prim as instanceable
prim.SetInstanceable(True)
```

## Key Concepts

| Feature | Reference | Payload |
|---------|-----------|---------|
| Loading | Immediate | Deferred (lazy) |
| Use case | Small assets | Large assets |
| Memory | Always loaded | Only when needed |

- **Variant** — an alternative configuration for a prim (e.g. different colors).
- **Instance** — a shared copy of a prim that reduces memory usage.

## Output

```
tutorials\usd_basics\05_usd_assembly\output\
├── 05_usd_assembly.usda   # Assembled room scene (references + variants + instances)
└── assets\
    ├── table.usda         # Table asset (referenced by main scene)
    ├── chair.usda          # Chair asset (referenced by main scene)
    └── lamp.usda           # Lamp asset (referenced by main scene)
```

## Notes

- **Self-contained:** The script creates the `assets\` files itself before
  referencing them — no external dependencies.
- **Re-running:** Uses `Usd.Stage.CreateNew()` — delete the existing output
  before re-running:
  ```batch
  del tutorials\usd_basics\05_usd_assembly\output\05_usd_assembly.usda
  del tutorials\usd_basics\05_usd_assembly\output\assets\*.usda
  ```

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Referenced asset not loading | Wrong file path in `AddReference` | Use the absolute or correct relative path to the `.usda` |
| Variant edits affect all variants | Edited outside variant context | Edit inside `with variant_set.GetVariantEditContext():` |
| Instancing not reducing memory | Prim not marked instanceable | Call `prim.SetInstanceable(True)` |

## Next Steps

USD Basics complete! Proceed to **Tutorial Set 2: Omniverse Kit API**
(Tutorials 06–08).
