"""
================================================================================
Tutorial 07: Omniverse Data Connectors - External Data to USD Pipeline
================================================================================

This tutorial covers the data connector pattern used in Omniverse to convert
external data formats into USD scenes. Connectors are a key part of the
Omniverse ecosystem, enabling data from CAD tools, simulation software, and
sensors to be brought into USD.

Topics covered:
  1. The connector pattern (source data -> intermediate representation -> USD)
  2. Converting CSV data to USD geometry
  3. Converting JSON data to USD scene hierarchy
  4. Creating a reusable connector class
  5. Batch processing multiple data sources

Key Concepts:
  - Connector:    A module that reads external data and creates USD prims
  - Source Data:  External data in formats like CSV, JSON, HDF5, etc.
  - Mapping:      Rules for converting source data fields to USD attributes
  - Batch Mode:   Processing multiple files in one run

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\07_omniverse_connector.py
================================================================================
"""

import os
import json
import csv
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf


# ==============================================================================
# Part 1: CSV to USD Connector (Point Cloud Data)
# ==============================================================================

def create_sample_csv(filepath):
    """
    Create a sample CSV file with point cloud data.

    This simulates data from a 3D scanner or simulation output.
    Each row contains: x, y, z coordinates and a scalar value (e.g., temperature).

    Args:
        filepath (str): Path to save the CSV file.
    """
    # Generate a spiral point cloud with temperature values
    import math

    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        # Write header
        writer.writerow(["x", "y", "z", "temperature"])

        # Generate 20 points in a spiral pattern
        for i in range(20):
            t = i * 0.5  # Parameter (wider step for 20 points)
            x = 5.0 * math.cos(t)
            z = 5.0 * math.sin(t)
            y = t * 0.3  # Spiral upward
            # Temperature varies with height (simulating heat rising)
            temp = 20.0 + y * 5.0
            writer.writerow([f"{x:.4f}", f"{y:.4f}", f"{z:.4f}", f"{temp:.2f}"])

    print(f"  [+] Created sample CSV: {filepath} (20 points)")


def csv_to_usd_connector(csv_filepath, stage, parent_path="/World/PointCloud"):
    """
    Convert CSV point cloud data to USD geometry.

    This is a simple connector that:
      1. Reads CSV data (x, y, z, temperature)
      2. Creates USD points (small spheres) at each position
      3. Colors each point based on its temperature value
      4. Stores the temperature as a custom attribute

    In a real connector, you might use UsdGeom.Points instead of individual
    spheres for better performance with large datasets.

    Args:
        csv_filepath (str): Path to the CSV file.
        stage (Usd.Stage): The USD stage to create prims on.
        parent_path (str): The prim path for the point cloud parent.
    """
    # Create a parent Xform for the point cloud
    parent = UsdGeom.Xform.Define(stage, parent_path)

    # Read the CSV file
    points_data = []
    with open(csv_filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            points_data.append({
                "x": float(row["x"]),
                "y": float(row["y"]),
                "z": float(row["z"]),
                "temperature": float(row["temperature"]),
            })

    print(f"  [+] Read {len(points_data)} points from CSV")

    # Find min and max temperature for color mapping
    temps = [p["temperature"] for p in points_data]
    min_temp = min(temps)
    max_temp = max(temps)
    temp_range = max_temp - min_temp if max_temp > min_temp else 1.0

    # Create a point prim for each data point
    # Using small spheres to represent points
    for i, point in enumerate(points_data):
        point_path = f"{parent_path}/Point_{i:04d}"

        # Create a small sphere at the point's position
        sphere = UsdGeom.Sphere.Define(stage, point_path)
        sphere.GetRadiusAttr().Set(0.1)  # Small radius

        # Set position
        UsdGeom.Xformable(sphere).AddTranslateOp().Set(
            Gf.Vec3d(point["x"], point["y"], point["z"])
        )

        # Map temperature to color (blue=cold, red=hot)
        # Normalize temperature to [0, 1]
        normalized_temp = (point["temperature"] - min_temp) / temp_range
        # Blue (0,0,1) -> Green (0,1,0) -> Red (1,0,0)
        if normalized_temp < 0.5:
            # Blue to Green
            t = normalized_temp * 2.0
            color = (0.0, t, 1.0 - t)
        else:
            # Green to Red
            t = (normalized_temp - 0.5) * 2.0
            color = (t, 1.0 - t, 0.0)

        sphere.GetDisplayColorAttr().Set([color])

        # Store the temperature as a custom attribute
        sphere.GetPrim().CreateAttribute(
            "data:temperature",
            Sdf.ValueTypeNames.Float
        ).Set(point["temperature"])

    print(f"  [+] Created {len(points_data)} point prims with temperature-based coloring")
    print(f"      Temperature range: {min_temp:.2f} to {max_temp:.2f}")


# ==============================================================================
# Part 2: JSON to USD Connector (Scene Hierarchy)
# ==============================================================================

def create_sample_json(filepath):
    """
    Create a sample JSON file describing a scene hierarchy.

    This simulates configuration data from a CAD tool or scene description.
    The JSON contains a tree of objects with positions, sizes, and types.

    Args:
        filepath (str): Path to save the JSON file.
    """
    scene_data = {
        "name": "FactoryFloor",
        "type": "Xform",
        "children": [
            {
                "name": "Machine1",
                "type": "Cube",
                "position": [0.0, 0.0, 0.0],
                "size": 3.0,
                "color": [0.8, 0.2, 0.2],
                "metadata": {"manufacturer": "ACME", "model": "X-100"}
            },
            {
                "name": "Machine2",
                "type": "Cube",
                "position": [5.0, 0.0, 0.0],
                "size": 2.5,
                "color": [0.2, 0.8, 0.2],
                "metadata": {"manufacturer": "ACME", "model": "X-200"}
            },
            {
                "name": "StorageTank",
                "type": "Cylinder",
                "position": [-5.0, 0.0, 0.0],
                "height": 4.0,
                "radius": 1.5,
                "color": [0.2, 0.2, 0.8],
                "metadata": {"capacity_liters": 5000, "contents": "Water"}
            },
            {
                "name": "ControlRoom",
                "type": "Xform",
                "position": [0.0, 0.0, 8.0],
                "children": [
                    {
                        "name": "Desk",
                        "type": "Cube",
                        "position": [0.0, 0.5, 0.0],
                        "size": 1.5,
                        "color": [0.6, 0.4, 0.2]
                    },
                    {
                        "name": "Monitor",
                        "type": "Cube",
                        "position": [0.0, 1.2, 0.0],
                        "size": 0.5,
                        "color": [0.1, 0.1, 0.1]
                    }
                ]
            }
        ]
    }

    with open(filepath, "w") as f:
        json.dump(scene_data, f, indent=2)

    print(f"  [+] Created sample JSON: {filepath}")


def json_to_usd_connector(json_filepath, stage, parent_path="/World"):
    """
    Convert JSON scene description to USD prims.

    This connector recursively traverses the JSON tree and creates
    corresponding USD prims. It handles:
      - Xform (groups/containers)
      - Cube (with size, position, color)
      - Cylinder (with height, radius, position, color)
      - Custom metadata (stored as attributes)

    Args:
        json_filepath (str): Path to the JSON file.
        stage (Usd.Stage): The USD stage to create prims on.
        parent_path (str): The parent prim path.

    Returns:
        str: The path of the root prim created.
    """
    # Read the JSON file
    with open(json_filepath, "r") as f:
        data = json.load(f)

    def create_prim_from_data(data, parent_path):
        """
        Recursively create USD prims from JSON data.

        Args:
            data (dict): The JSON data for this prim.
            parent_path (str): The parent prim path.

        Returns:
            str: The path of the created prim.
        """
        name = data["name"]
        prim_type = data.get("type", "Xform")
        position = data.get("position", [0.0, 0.0, 0.0])
        color = data.get("color")
        prim_path = f"{parent_path}/{name}"

        # Create the appropriate USD prim based on type
        if prim_type == "Cube":
            prim = UsdGeom.Cube.Define(stage, prim_path)
            prim.GetSizeAttr().Set(data.get("size", 1.0))
        elif prim_type == "Cylinder":
            prim = UsdGeom.Cylinder.Define(stage, prim_path)
            prim.GetHeightAttr().Set(data.get("height", 1.0))
            prim.GetRadiusAttr().Set(data.get("radius", 0.5))
        elif prim_type == "Sphere":
            prim = UsdGeom.Sphere.Define(stage, prim_path)
            prim.GetRadiusAttr().Set(data.get("radius", 0.5))
        else:  # Xform or unknown
            prim = UsdGeom.Xform.Define(stage, prim_path)

        # Set position
        UsdGeom.Xformable(prim).AddTranslateOp().Set(
            Gf.Vec3d(position[0], position[1], position[2])
        )

        # Set color if provided
        if color:
            prim.GetDisplayColorAttr().Set([(color[0], color[1], color[2])])

        # Store metadata as custom attributes
        metadata = data.get("metadata", {})
        for key, value in metadata.items():
            # Determine the SDF type based on the Python type
            if isinstance(value, str):
                sdf_type = Sdf.ValueTypeNames.String
            elif isinstance(value, int):
                sdf_type = Sdf.ValueTypeNames.Int
            elif isinstance(value, float):
                sdf_type = Sdf.ValueTypeNames.Float
            else:
                sdf_type = Sdf.ValueTypeNames.String
                value = str(value)

            prim.GetPrim().CreateAttribute(f"meta:{key}", sdf_type).Set(value)

        # Recursively create children
        children = data.get("children", [])
        for child in children:
            create_prim_from_data(child, prim_path)

        return prim_path

    root_path = create_prim_from_data(data, parent_path)
    print(f"  [+] Converted JSON to USD: root prim at {root_path}")
    return root_path


# ==============================================================================
# Part 3: Reusable Connector Class
# ==============================================================================

class DataConnector:
    """
    A reusable data connector class that converts external data to USD.

    This class demonstrates the connector pattern used in Omniverse:
      1. Initialize with a USD stage
      2. Register data source handlers
      3. Process data sources and create USD prims

    In a real Omniverse connector, this would be more sophisticated,
    handling streaming data, incremental updates, and error recovery.
    """

    def __init__(self, stage):
        """
        Initialize the connector with a USD stage.

        Args:
            stage (Usd.Stage): The USD stage to write data to.
        """
        self.stage = stage
        self.handlers = {}  # Mapping of data type to handler function
        self.processed_count = 0

    def register_handler(self, data_type, handler_func):
        """
        Register a handler function for a specific data type.

        Args:
            data_type (str): A string identifying the data type (e.g., "csv", "json").
            handler_func (callable): A function that takes (filepath, stage, parent_path)
                                     and creates USD prims.
        """
        self.handlers[data_type] = handler_func
        print(f"  [+] Registered handler for data type: {data_type}")

    def process(self, filepath, data_type, parent_path="/World"):
        """
        Process a data file using the registered handler.

        Args:
            filepath (str): Path to the data file.
            data_type (str): The data type (must have a registered handler).
            parent_path (str): The parent prim path.

        Returns:
            str: The path of the created root prim, or None on failure.
        """
        if data_type not in self.handlers:
            print(f"  [ERROR] No handler registered for type: {data_type}")
            return None

        handler = self.handlers[data_type]
        result = handler(filepath, self.stage, parent_path)
        self.processed_count += 1
        print(f"  [+] Processed {filepath} as {data_type} (total: {self.processed_count})")
        return result

    def get_stats(self):
        """
        Return processing statistics.

        Returns:
            dict: Statistics about processed data.
        """
        return {
            "total_processed": self.processed_count,
            "registered_types": list(self.handlers.keys()),
        }


# ==============================================================================
# Part 4: Batch Processing
# ==============================================================================

def batch_process_demo(stage, output_dir):
    """
    Demonstrate batch processing of multiple data sources.

    This shows how a connector can process multiple files in one run,
    creating a unified USD scene from diverse data sources.

    Args:
        stage (Usd.Stage): The USD stage to write to.
        output_dir (str): Directory containing data files.
    """
    # Create the connector
    connector = DataConnector(stage)

    # Register handlers
    connector.register_handler("csv", csv_to_usd_connector)
    connector.register_handler("json", json_to_usd_connector)

    # Create sample data files
    csv_file = os.path.join(output_dir, "sample_data.csv")
    json_file = os.path.join(output_dir, "sample_scene.json")
    create_sample_csv(csv_file)
    create_sample_json(json_file)

    # Process each file
    print("\n  --- Batch Processing ---")
    connector.process(csv_file, "csv", parent_path="/World/SensorData")
    connector.process(json_file, "json", parent_path="/World/FactoryLayout")

    # Print stats
    stats = connector.get_stats()
    print(f"\n  Connector stats: {stats}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 07: Omniverse Data Connectors - External Data to USD Pipeline")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    data_dir = os.path.join(output_dir, "connector_data")
    os.makedirs(data_dir, exist_ok=True)

    # Create the USD stage
    usd_file = os.path.join(output_dir, "07_omniverse_connector.usda")
    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Step 1: CSV to USD connector
    print("\n--- Step 1: CSV to USD Connector ---")
    csv_file = os.path.join(data_dir, "sample_data.csv")
    create_sample_csv(csv_file)
    csv_to_usd_connector(csv_file, stage, "/World/CSV_Points")

    # Step 2: JSON to USD connector
    print("\n--- Step 2: JSON to USD Connector ---")
    json_file = os.path.join(data_dir, "sample_scene.json")
    create_sample_json(json_file)
    json_to_usd_connector(json_file, stage, "/World/JSON_Scene")

    # Step 3: Reusable connector class with batch processing
    print("\n--- Step 3: Reusable Connector Class ---")
    batch_process_demo(stage, data_dir)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    print("\n" + "=" * 80)
    print("Tutorial 07 complete!")
    print(f"USD output: {usd_file}")
    print(f"Data files: {data_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
