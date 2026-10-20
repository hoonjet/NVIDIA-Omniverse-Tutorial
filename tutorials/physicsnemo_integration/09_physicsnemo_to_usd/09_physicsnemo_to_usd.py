"""
================================================================================
Tutorial 09: PhysicsNeMo to USD - Converting Simulation Results to 3D Scenes
================================================================================

This tutorial bridges the user's existing PhysicsNeMo knowledge with Omniverse
USD. It demonstrates how to convert PhysicsNeMo simulation results (e.g., Darcy
flow, heat conduction) into USD scenes for 3D visualization.

The user has already built PhysicsNeMo models in E:\physicsnemo_env. This
tutorial shows how to take simulation output and create a USD scene that
represents the results visually.

Topics covered:
  1. Generating synthetic simulation data (mimicking PhysicsNeMo output)
  2. Converting a 2D scalar field to a USD point cloud
  3. Mapping scalar values to colors (colormap)
  4. Creating a 3D height-field representation
  5. Storing simulation metadata in USD

Key Concepts:
  - Scalar Field:  A 2D grid of values (e.g., pressure, temperature, velocity)
  - Colormap:     A function mapping scalar values to RGB colors
  - Height Field:  A 3D surface where Z = scalar value (for visualization)
  - Metadata:      Simulation parameters stored as USD attributes

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\09_physicsnemo_to_usd.py
================================================================================
"""

import os
import math
import json
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf
import numpy as np


# ==============================================================================
# Part 1: Generating Synthetic Simulation Data
# ==============================================================================

def generate_darcy_flow_data(nx=20, ny=20):
    """
    Generate synthetic Darcy flow data that mimics PhysicsNeMo output.

    Darcy flow simulates fluid flow through a porous medium. The output
    is a 2D pressure field and a 2D velocity field (vx, vy).

    In a real workflow, this data would come from a PhysicsNeMo model
    inference. Here we generate synthetic data using an analytical solution
    for demonstration purposes.

    The Darcy equation: -∇·(K∇p) = f
    where K is permeability, p is pressure, f is source term.

    Args:
        nx (int): Number of grid points in X direction.
        ny (int): Number of grid points in Y direction.

    Returns:
        dict: Dictionary containing:
            - "x", "y": Grid coordinates (1D arrays)
            - "pressure": 2D pressure field (nx x ny)
            - "velocity_x": 2D X-velocity field (nx x ny)
            - "velocity_y": 2D Y-velocity field (nx x ny)
            - "metadata": Simulation parameters
    """
    # Create a regular grid
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)
    X, Y = np.meshgrid(x, y, indexing="ij")

    # Generate a synthetic pressure field
    # This mimics a Darcy flow solution: high pressure on left, low on right
    # with some sinusoidal variation
    pressure = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            # Pressure decreases from left to right (pressure gradient)
            # with sinusoidal perturbation
            pressure[i, j] = 1.0 - x[i] + 0.2 * math.sin(2 * math.pi * y[j])

    # Compute velocity from pressure gradient (Darcy's law: v = -K∇p)
    # For simplicity, K = 1 (unit permeability)
    velocity_x = np.zeros((nx, ny))
    velocity_y = np.zeros((nx, ny))
    for i in range(nx):
        for j in range(ny):
            # Numerical gradient (central difference)
            if i > 0 and i < nx - 1:
                dp_dx = (pressure[i + 1, j] - pressure[i - 1, j]) / (2 * (x[1] - x[0]))
            else:
                dp_dx = 0.0

            if j > 0 and j < ny - 1:
                dp_dy = (pressure[i, j + 1] - pressure[i, j - 1]) / (2 * (y[1] - y[0]))
            else:
                dp_dy = 0.0

            # v = -∇p (Darcy's law with K=1)
            velocity_x[i, j] = -dp_dx
            velocity_y[i, j] = -dp_dy

    # Compute velocity magnitude for visualization
    velocity_mag = np.sqrt(velocity_x**2 + velocity_y**2)

    # Metadata (mimicking PhysicsNeMo model parameters)
    metadata = {
        "simulation_type": "darcy_flow",
        "equation": "-div(K * grad(p)) = f",
        "permeability": 1.0,
        "domain": [0.0, 1.0, 0.0, 1.0],  # [xmin, xmax, ymin, ymax]
        "grid_size": [nx, ny],
        "source": "synthetic_analytical",
        "model": "PhysicsNeMo (simulated)",
    }

    print(f"  [+] Generated Darcy flow data: {nx}x{ny} grid")
    print(f"      Pressure range: {pressure.min():.4f} to {pressure.max():.4f}")
    print(f"      Velocity magnitude range: {velocity_mag.min():.4f} to {velocity_mag.max():.4f}")

    return {
        "x": x,
        "y": y,
        "pressure": pressure,
        "velocity_x": velocity_x,
        "velocity_y": velocity_y,
        "velocity_mag": velocity_mag,
        "metadata": metadata,
    }


# ==============================================================================
# Part 2: Colormap Function
# ==============================================================================

def scalar_to_color(value, vmin, vmax):
    """
    Map a scalar value to an RGB color using a jet-like colormap.

    The jet colormap goes:
      Blue -> Cyan -> Green -> Yellow -> Red

    This is commonly used for scientific visualization (e.g., temperature,
    pressure, velocity fields).

    Args:
        value (float): The scalar value to map.
        vmin (float): Minimum value of the range.
        vmax (float): Maximum value of the range.

    Returns:
        tuple: (R, G, B) color values in [0.0, 1.0].
    """
    # Normalize to [0, 1]
    if vmax > vmin:
        t = (value - vmin) / (vmax - vmin)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))  # Clamp to [0, 1]

    # Jet colormap interpolation
    if t < 0.25:
        # Blue to Cyan
        r = 0.0
        g = t * 4.0
        b = 1.0
    elif t < 0.5:
        # Cyan to Green
        r = 0.0
        g = 1.0
        b = 1.0 - (t - 0.25) * 4.0
    elif t < 0.75:
        # Green to Yellow
        r = (t - 0.5) * 4.0
        g = 1.0
        b = 0.0
    else:
        # Yellow to Red
        r = 1.0
        g = 1.0 - (t - 0.75) * 4.0
        b = 0.0

    return (r, g, b)


# ==============================================================================
# Part 3: Converting Scalar Field to USD Point Cloud
# ==============================================================================

def scalar_field_to_usd_points(data, stage, field_name="pressure"):
    """
    Convert a 2D scalar field to a USD point cloud.

    Each grid point becomes a small sphere in USD space, colored according
    to the scalar value using the jet colormap.

    This is the simplest visualization: a flat 2D grid of colored points.

    Args:
        data (dict): The simulation data dictionary.
        stage (Usd.Stage): The USD stage to create prims on.
        field_name (str): Which field to visualize ("pressure" or "velocity_mag").
    """
    # Get the field data
    field = data[field_name]
    x_coords = data["x"]
    y_coords = data["y"]

    # Get value range for colormap
    vmin = field.min()
    vmax = field.max()

    # Create a parent Xform for the point cloud
    parent_path = f"/World/DarcyFlow/{field_name}_points"
    parent = UsdGeom.Xform.Define(stage, parent_path)

    # Scale factor: map [0,1] domain to [0,10] in USD space
    scale = 10.0

    nx = len(x_coords)
    ny = len(y_coords)

    # Create a point for each grid cell
    for i in range(nx):
        for j in range(ny):
            value = field[i, j]
            color = scalar_to_color(value, vmin, vmax)

            # Position in USD space
            x_pos = x_coords[i] * scale
            y_pos = 0.0  # Flat on the ground plane
            z_pos = y_coords[j] * scale

            # Create a small sphere
            point_path = f"{parent_path}/P_{i:03d}_{j:03d}"
            sphere = UsdGeom.Sphere.Define(stage, point_path)
            sphere.GetRadiusAttr().Set(0.15)
            sphere.GetDisplayColorAttr().Set([color])
            UsdGeom.Xformable(sphere).AddTranslateOp().Set(
                Gf.Vec3d(x_pos, y_pos, z_pos)
            )

            # Store the scalar value as a custom attribute
            sphere.GetPrim().CreateAttribute(
                f"data:{field_name}",
                Sdf.ValueTypeNames.Float
            ).Set(float(value))

    print(f"  [+] Created {nx * ny} colored points for '{field_name}'")
    print(f"      Value range: {vmin:.4f} to {vmax:.4f}")


# ==============================================================================
# Part 4: Creating a 3D Height Field
# ==============================================================================

def scalar_field_to_height_field(data, stage, field_name="pressure"):
    """
    Convert a 2D scalar field to a 3D height field.

    A height field is a 3D surface where the height (Y) represents the
    scalar value. This gives a more intuitive visualization of the field's
    magnitude.

    Each grid point becomes a column (cylinder) whose height is proportional
    to the scalar value.

    Args:
        data (dict): The simulation data dictionary.
        stage (Usd.Stage): The USD stage to create prims on.
        field_name (str): Which field to visualize.
    """
    field = data[field_name]
    x_coords = data["x"]
    y_coords = data["y"]

    vmin = field.min()
    vmax = field.max()
    vrange = vmax - vmin if vmax > vmin else 1.0

    # Create a parent Xform for the height field
    parent_path = f"/World/DarcyFlow/{field_name}_heightfield"
    parent = UsdGeom.Xform.Define(stage, parent_path)

    scale = 10.0
    height_scale = 5.0  # Scale factor for height

    nx = len(x_coords)
    ny = len(y_coords)

    for i in range(nx):
        for j in range(ny):
            value = field[i, j]
            color = scalar_to_color(value, vmin, vmax)

            # Normalize value to [0, 1] and scale to height
            normalized = (value - vmin) / vrange
            height = normalized * height_scale

            # Position in USD space
            x_pos = x_coords[i] * scale
            z_pos = y_coords[j] * scale

            # Create a cylinder whose height represents the value
            col_path = f"{parent_path}/H_{i:03d}_{j:03d}"
            cylinder = UsdGeom.Cylinder.Define(stage, col_path)
            cylinder.GetHeightAttr().Set(max(height, 0.01))  # Min height
            cylinder.GetRadiusAttr().Set(0.2)
            cylinder.GetDisplayColorAttr().Set([color])

            # Position: center the cylinder on the ground
            UsdGeom.Xformable(cylinder).AddTranslateOp().Set(
                Gf.Vec3d(x_pos, height / 2.0, z_pos)
            )

            # Store the scalar value
            cylinder.GetPrim().CreateAttribute(
                f"data:{field_name}",
                Sdf.ValueTypeNames.Float
            ).Set(float(value))

    print(f"  [+] Created height field with {nx * ny} columns for '{field_name}'")
    print(f"      Height range: 0 to {height_scale:.1f} (representing {vmin:.4f} to {vmax:.4f})")


# ==============================================================================
# Part 5: Storing Simulation Metadata
# ==============================================================================

def store_simulation_metadata(stage, data):
    """
    Store simulation metadata as USD attributes on a dedicated prim.

    This allows the simulation parameters to be saved with the USD scene
    and retrieved later for reproducibility.

    Args:
        stage (Usd.Stage): The USD stage.
        data (dict): The simulation data dictionary.
    """
    # Create a metadata prim
    meta_prim = stage.DefinePrim("/World/DarcyFlow/SimulationMetadata", "Xform")

    metadata = data["metadata"]

    # Store each metadata field as a custom attribute
    for key, value in metadata.items():
        # Determine the SDF type based on the Python type
        if isinstance(value, str):
            sdf_type = Sdf.ValueTypeNames.String
        elif isinstance(value, (int, float)):
            sdf_type = Sdf.ValueTypeNames.Float if isinstance(value, float) else Sdf.ValueTypeNames.Int
        elif isinstance(value, list):
            # Store lists as string for simplicity
            sdf_type = Sdf.ValueTypeNames.String
            value = json.dumps(value)
        else:
            sdf_type = Sdf.ValueTypeNames.String
            value = str(value)

        meta_prim.CreateAttribute(f"sim:{key}", sdf_type).Set(value)

    print(f"  [+] Stored {len(metadata)} metadata fields on SimulationMetadata prim")


# ==============================================================================
# Part 6: Exporting Data as JSON (for external tools)
# ==============================================================================

def export_data_as_json(data, filepath):
    """
    Export the simulation data as a JSON file.

    This allows the data to be loaded by external tools or by the
    connector tutorial (07) for conversion to USD.

    Args:
        data (dict): The simulation data dictionary.
        filepath (str): Path to save the JSON file.
    """
    # Convert numpy arrays to lists for JSON serialization
    export_data = {
        "x": data["x"].tolist(),
        "y": data["y"].tolist(),
        "pressure": data["pressure"].tolist(),
        "velocity_x": data["velocity_x"].tolist(),
        "velocity_y": data["velocity_y"].tolist(),
        "velocity_mag": data["velocity_mag"].tolist(),
        "metadata": data["metadata"],
    }

    with open(filepath, "w") as f:
        json.dump(export_data, f, indent=2)

    print(f"  [+] Exported simulation data to JSON: {filepath}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 09: PhysicsNeMo to USD - Converting Simulation Results to 3D Scenes")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    data_dir = os.path.join(output_dir, "physicsnemo_data")
    os.makedirs(data_dir, exist_ok=True)

    # Step 1: Generate synthetic Darcy flow data
    print("\n--- Step 1: Generating Simulation Data ---")
    data = generate_darcy_flow_data(nx=15, ny=15)

    # Export as JSON for external use
    json_path = os.path.join(data_dir, "darcy_flow.json")
    export_data_as_json(data, json_path)

    # Step 2: Create USD stage
    print("\n--- Step 2: Creating USD Scene ---")
    usd_file = os.path.join(output_dir, "09_physicsnemo_to_usd.usda")
    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Create a parent for all Darcy flow visualization
    UsdGeom.Xform.Define(stage, "/World/DarcyFlow")

    # Step 3: Convert pressure field to colored point cloud
    print("\n--- Step 3: Creating Pressure Point Cloud ---")
    scalar_field_to_usd_points(data, stage, field_name="pressure")

    # Step 4: Convert pressure field to 3D height field
    print("\n--- Step 4: Creating Pressure Height Field ---")
    scalar_field_to_height_field(data, stage, field_name="pressure")

    # Step 5: Convert velocity magnitude to colored point cloud
    print("\n--- Step 5: Creating Velocity Point Cloud ---")
    scalar_field_to_usd_points(data, stage, field_name="velocity_mag")

    # Step 6: Store simulation metadata
    print("\n--- Step 6: Storing Simulation Metadata ---")
    store_simulation_metadata(stage, data)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    print("\n" + "=" * 80)
    print("Tutorial 09 complete!")
    print(f"USD output: {usd_file}")
    print(f"JSON data:  {json_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()
