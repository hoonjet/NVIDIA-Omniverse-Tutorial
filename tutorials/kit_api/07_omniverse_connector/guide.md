# Tutorial 07: Omniverse Data Connectors

> **Category:** Kit API · **Script:** `07_omniverse_connector.py`

## Overview

Demonstrates **data connectors** — the pipelines that convert external data
formats into USD scenes. This tutorial generates sample CSV and JSON data,
then converts each into USD geometry, showing the pattern Omniverse connectors
use to ingest real-world data.

## Prerequisites

- Complete **Tutorials 01–06** first.
- Activate the virtual environment:
  ```batch
  cd E:\omniverse_env
  Scripts\activate
  ```

## How to Run

```batch
cd E:\omniverse_env
Scripts\activate
python tutorials\kit_api\07_omniverse_connector\07_omniverse_connector.py
```

## What It Does

1. **Generates Sample Data** — creates `sample_data.csv` (tabular) and
   `sample_scene.json` (structured) under `output\connector_data\`.
2. **CSV → USD** — parses the CSV rows and converts each record into USD prims
   with attributes.
3. **JSON → USD** — parses the JSON structure and builds a corresponding USD
   scene hierarchy.
4. **Demonstrates the Connector Pattern** — shows how a connector reads a source
   format, maps fields to USD prims/attributes, and writes a stage.

## Key API / Concepts

```python
import csv, json

# CSV -> USD: each row becomes a prim with attributes
with open(csv_path) as f:
    for row in csv.DictReader(f):
        prim = stage.DefinePrim(f"/World/Row_{i}")
        prim.CreateAttribute("value", Sdf.ValueTypeNames.Float).Set(float(row["value"]))

# JSON -> USD: nested objects become a prim hierarchy
data = json.load(open(json_path))
# ... recurse the structure, defining prims and attributes
```

- **Connector** — a pipeline that reads an external format and emits USD.
- Common real-world connectors: CAD → USD, FBX → USD, point clouds → USD.

## Output

```
tutorials\kit_api\07_omniverse_connector\output\
├── 07_omniverse_connector.usda   # Converted USD scene
└── connector_data\
    ├── sample_data.csv            # Sample tabular data (input)
    └── sample_scene.json          # Sample structured data (input)
```

## Notes

- **Safe to re-run:** The script removes an existing `.usda` before creating a
  new one.
- The connector creates its own sample input data, so it is self-contained —
  no external files required.

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| CSV rows not appearing as prims | Header mismatch or wrong column name | Check the CSV header matches the field the script reads |
| JSON conversion incomplete | Nested structure not recursed | Ensure the recursion handles dicts and lists at every level |

## Next Steps

Continue to **Tutorial 08: Live Sync**.
