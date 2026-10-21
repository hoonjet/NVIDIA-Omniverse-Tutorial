"""
================================================================================
Tutorial 10: Simulation Visualization - Animated 3D Color Maps
================================================================================

This tutorial builds on Tutorial 09 by adding animation to simulation
visualization. It creates time-varying simulation data and animates the
USD scene to show how results evolve over time.

Topics covered:
  1. Generating time-varying simulation data (transient simulation)
  2. Creating animated color maps (color changes over time)
  3. Creating animated height fields (height changes over time)
  4. Visualizing vector fields (velocity arrows)
  5. Creating a time-synchronized visualization

Key Concepts:
  - Transient Simulation: A simulation that changes over time
  - Time-Varying Field: A scalar/vector field that changes at each timestep
  - Vector Field Visualization: Showing direction and magnitude of vectors
  - Synchronized Animation: Multiple visualizations driven by the same timeline

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\10_simulation_visual.py
================================================================================
"""

import os
import math
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf
import numpy as np


# ==============================================================================
# Part 1: Generating Time-Varying Simulation Data
# ==============================================================================

def generate_transient_data(nx=3, ny=2, num_timesteps=3):
    """
    Generate time-varying (transient) simulation data.

    This simulates a heat diffusion problem where temperature changes
    over time. The heat equation: ∂T/∂t = α∇²T

    We generate synthetic data that mimics a PhysicsNeMo transient
    simulation output.

    Args:
        nx (int): Grid points in X direction.
        ny (int): Grid points in Y direction.
        num_timesteps (int): Number of time steps.

    Returns:
        dict: Contains time-varying fields and metadata.
    """
    x = np.linspace(0, 1, nx)
    y = np.linspace(0, 1, ny)

    # Create a 3D array: [timestep, x, y]
    temperature = np.zeros((num_timesteps, nx, ny))
    velocity_x = np.zeros((num_timesteps, nx, ny))
    velocity_y = np.zeros((num_timesteps, nx, ny))

    for t in range(num_timesteps):
        time = t / (num_timesteps - 1)  # Normalized time [0, 1]

        for i in range(nx):
            for j in range(ny):
                # Temperature: hot spot in center that diffuses over time
                # Initial: Gaussian peak at center
                # Over time: spreads out and cools
                cx, cy = 0.5, 0.5  # Center
                dist_sq = (x[i] - cx)**2 + (y[j] - cy)**2
                sigma = 0.1 + time * 0.3  # Spreads over time
                amplitude = 1.0 * (1.0 - 0.5 * time)  # Cools over time

                temperature[t, i, j] = amplitude * math.exp(-dist_sq / (2 * sigma**2))

                # Velocity: circular flow around the hot spot
                dx = x[i] - cx
                dy = y[j] - cy
                r = math.sqrt(dx**2 + dy**2) + 1e-6
                # Tangential velocity (rotates around center)
                v_mag = 0.5 * temperature[t, i, j]
                velocity_x[t, i, j] = -dy / r * v_mag
                velocity_y[t, i, j] = dx / r * v_mag

    print(f"  [+] Generated transient data: {nx}x{ny} grid, {num_timesteps} timesteps")
    print(f"      Temperature range: {temperature.min():.4f} to {temperature.max():.4f}")

    return {
        "x": x,
        "y": y,
        "temperature": temperature,
        "velocity_x": velocity_x,
        "velocity_y": velocity_y,
        "num_timesteps": num_timesteps,
    }


# ==============================================================================
# Part 2: Colormap (reused from Tutorial 09)
# ==============================================================================

def scalar_to_color(value, vmin, vmax):
    """
    Map a scalar value to an RGB color using a jet-like colormap.

    Blue -> Cyan -> Green -> Yellow -> Red

    Args:
        value (float): The scalar value to map.
        vmin (float): Minimum value of the range.
        vmax (float): Maximum value of the range.

    Returns:
        tuple: (R, G, B) color values in [0.0, 1.0].
    """
    if vmax > vmin:
        t = (value - vmin) / (vmax - vmin)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))

    if t < 0.25:
        return (0.0, t * 4.0, 1.0)
    elif t < 0.5:
        return (0.0, 1.0, 1.0 - (t - 0.25) * 4.0)
    elif t < 0.75:
        return ((t - 0.5) * 4.0, 1.0, 0.0)
    else:
        return (1.0, 1.0 - (t - 0.75) * 4.0, 0.0)


# ==============================================================================
# Part 3: Animated Color Map (Temperature Field)
# ==============================================================================

def create_animated_colormap(data, stage, start_frame=1, fps=12):
    """
    Create an animated color map showing temperature evolution over time.

    Each grid point is a sphere whose color changes at each timestep.
    USD time samples are used to store the color at each frame.

    Args:
        data (dict): The transient simulation data.
        stage (Usd.Stage): The USD stage.
        start_frame (int): The first frame number.
        fps (int): Frames per timestep.
    """
    x_coords = data["x"]
    y_coords = data["y"]
    temperature = data["temperature"]
    num_timesteps = data["num_timesteps"]

    # Global min/max for consistent colormap across all timesteps
    vmin = temperature.min()
    vmax = temperature.max()

    # Create parent
    parent_path = "/World/TransientSim/TemperatureMap"
    UsdGeom.Xform.Define(stage, parent_path)

    scale = 10.0
    nx = len(x_coords)
    ny = len(y_coords)

    for i in range(nx):
        for j in range(ny):
            point_path = f"{parent_path}/T_{i:03d}_{j:03d}"
            sphere = UsdGeom.Sphere.Define(stage, point_path)
            sphere.GetRadiusAttr().Set(0.2)

            # Position
            UsdGeom.Xformable(sphere).AddTranslateOp().Set(
                Gf.Vec3d(x_coords[i] * scale, 0.0, y_coords[j] * scale)
            )

            # Get the display color attribute
            color_attr = sphere.GetDisplayColorAttr()

            # Set color at each timestep (animated)
            for t in range(num_timesteps):
                frame = start_frame + t * fps
                value = temperature[t, i, j]
                color = scalar_to_color(value, vmin, vmax)
                color_attr.Set([color], frame)

            # Also store temperature value as animated attribute
            temp_attr = sphere.GetPrim().CreateAttribute(
                "data:temperature",
                Sdf.ValueTypeNames.Float
            )
            for t in range(num_timesteps):
                frame = start_frame + t * fps
                temp_attr.Set(float(temperature[t, i, j]), frame)

    # Set timeline
    end_frame = start_frame + (num_timesteps - 1) * fps
    stage.SetStartTimeCode(start_frame)
    stage.SetEndTimeCode(end_frame)
    stage.SetTimeCodesPerSecond(24.0)

    print(f"  [+] Created animated color map: {nx * ny} points, {num_timesteps} timesteps")
    print(f"      Timeline: frames {start_frame} to {end_frame} at 24 FPS")


# ==============================================================================
# Part 4: Animated Height Field
# ==============================================================================

def create_animated_height_field(data, stage, start_frame=1, fps=12):
    """
    Create an animated height field where column heights change over time.

    Each grid point is a cylinder whose height and color change at each
    timestep, showing the temperature evolution as a 3D surface.

    Args:
        data (dict): The transient simulation data.
        stage (Usd.Stage): The USD stage.
        start_frame (int): The first frame number.
        fps (int): Frames per timestep.
    """
    x_coords = data["x"]
    y_coords = data["y"]
    temperature = data["temperature"]
    num_timesteps = data["num_timesteps"]

    vmin = temperature.min()
    vmax = temperature.max()
    vrange = vmax - vmin if vmax > vmin else 1.0

    parent_path = "/World/TransientSim/HeightField"
    UsdGeom.Xform.Define(stage, parent_path)

    scale = 10.0
    height_scale = 5.0
    nx = len(x_coords)
    ny = len(y_coords)

    for i in range(nx):
        for j in range(ny):
            col_path = f"{parent_path}/H_{i:03d}_{j:03d}"
            cylinder = UsdGeom.Cylinder.Define(stage, col_path)
            cylinder.GetRadiusAttr().Set(0.25)

            # Base position (X, Z are fixed; Y changes with height)
            x_pos = x_coords[i] * scale
            z_pos = y_coords[j] * scale

            # We need to animate both height AND position (Y)
            # because the cylinder should sit on the ground

            # Get the height attribute
            height_attr = cylinder.GetHeightAttr()
            color_attr = cylinder.GetDisplayColorAttr()

            # Get or create translate op for Y animation
            xformable = UsdGeom.Xformable(cylinder)
            translate_op = xformable.AddTranslateOp()

            # Set height, color, and position at each timestep
            for t in range(num_timesteps):
                frame = start_frame + t * fps
                value = temperature[t, i, j]
                normalized = (value - vmin) / vrange
                height = max(normalized * height_scale, 0.01)

                # Set height at this frame
                height_attr.Set(height, frame)

                # Set color at this frame
                color = scalar_to_color(value, vmin, vmax)
                color_attr.Set([color], frame)

                # Set position (Y = height/2 so cylinder sits on ground)
                translate_op.Set(Gf.Vec3d(x_pos, height / 2.0, z_pos), frame)

    print(f"  [+] Created animated height field: {nx * ny} columns, {num_timesteps} timesteps")


# ==============================================================================
# Part 5: Vector Field Visualization (Velocity Arrows)
# ==============================================================================

def create_vector_field(data, stage, timestep=0, start_frame=1, fps=12):
    """
    Create velocity vector arrows at the final timestep.

    Each arrow shows the direction and magnitude of the velocity at that
    grid point. The arrows are colored by magnitude.

    In USD, we represent arrows as thin cylinders (shaft) + cones (tip).

    Args:
        data (dict): The transient simulation data.
        stage (Usd.Stage): The USD stage.
        timestep (int): Which timestep to visualize.
        start_frame (int): First frame number.
        fps (int): Frames per timestep.
    """
    x_coords = data["x"]
    y_coords = data["y"]
    vx = data["velocity_x"][timestep]
    vy = data["velocity_y"][timestep]
    vmag = np.sqrt(vx**2 + vy**2)

    vmin = vmag.min()
    vmax = vmag.max()

    parent_path = "/World/TransientSim/VelocityField"
    UsdGeom.Xform.Define(stage, parent_path)

    scale = 10.0
    arrow_scale = 3.0  # Scale for arrow length
    nx = len(x_coords)
    ny = len(y_coords)

    for i in range(nx):
        for j in range(ny):
            # Skip near-zero velocity points
            if vmag[i, j] < 0.01:
                continue

            # Arrow position (base point)
            x_pos = x_coords[i] * scale
            z_pos = y_coords[j] * scale

            # Arrow direction and length
            dx = vx[i, j] * arrow_scale
            dy = 0.0  # 2D simulation, no Y velocity
            dz = vy[i, j] * arrow_scale
            length = math.sqrt(dx**2 + dy**2 + dz**2)

            if length < 0.01:
                continue

            # Create a thin cylinder as the arrow shaft
            arrow_path = f"{parent_path}/V_{i:03d}_{j:03d}"
            shaft = UsdGeom.Cylinder.Define(stage, arrow_path)
            shaft.GetHeightAttr().Set(length)
            shaft.GetRadiusAttr().Set(0.05)

            # Color by magnitude
            color = scalar_to_color(vmag[i, j], vmin, vmax)
            shaft.GetDisplayColorAttr().Set([color])

            # Position the shaft: center it at the midpoint
            xformable = UsdGeom.Xformable(shaft)
            translate_op = xformable.AddTranslateOp().Set(
                Gf.Vec3d(x_pos + dx / 2.0, 0.5, z_pos + dz / 2.0)
            )

            # Rotate the cylinder to point in the velocity direction
            # Default cylinder axis is Y; we need to rotate it
            # Compute rotation from Y axis to (dx, dy, dz) direction
            # Using rotation that maps Y to the velocity direction
            if abs(dx) > 0.001 or abs(dz) > 0.001:
                # Angle in XZ plane
                angle_y = math.degrees(math.atan2(dx, dz))
                # Rotate around Y to align with XZ direction
                xformable.AddRotateYOp().Set(-angle_y)
                # Then rotate around X to lay flat (from Y to XZ plane)
                xformable.AddRotateXOp().Set(90.0)

    print(f"  [+] Created velocity vector field at timestep {timestep}")


# ==============================================================================
# Part 6: Reading Animated Values
# ==============================================================================

def verify_animation(stage, data, start_frame=1, fps=12):
    """
    Verify the animation by reading back values at specific frames.

    Args:
        stage (Usd.Stage): The USD stage.
        data (dict): The simulation data.
        start_frame (int): First frame.
        fps (int): Frames per timestep.
    """
    print("\n--- Verifying Animation ---")

    # Read temperature at a central grid point across all timesteps
    nx_mid = len(data["x"]) // 2
    ny_mid = len(data["y"]) // 2
    point_path = f"/World/TransientSim/TemperatureMap/T_{nx_mid:03d}_{ny_mid:03d}"
    prim = stage.GetPrimAtPath(point_path)

    if prim.IsValid():
        color_attr = prim.GetAttribute("primvars:displayColor")
        temp_attr = prim.GetAttribute("data:temperature")

        print(f"  Grid point ({nx_mid},{ny_mid}) across timesteps:")
        for t in range(data["num_timesteps"]):
            frame = start_frame + t * fps
            color = color_attr.Get(frame)
            temp = temp_attr.Get(frame) if temp_attr else "N/A"
            print(f"    Frame {frame:3d} (t={t}): temp={temp:.4f}, color={color}")
    else:
        print(f"  [WARNING] Prim not found: {point_path}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 10: Simulation Visualization - Animated 3D Color Maps")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")

    # Step 1: Generate transient data
    print("\n--- Step 1: Generating Transient Data ---")
    data = generate_transient_data(nx=3, ny=2, num_timesteps=3)

    # Step 2: Create USD stage
    print("\n--- Step 2: Creating USD Scene ---")
    usd_file = os.path.join(output_dir, "10_simulation_visual.usda")
    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())
    UsdGeom.Xform.Define(stage, "/World/TransientSim")

    # Step 3: Create animated color map
    print("\n--- Step 3: Creating Animated Color Map ---")
    create_animated_colormap(data, stage, start_frame=1, fps=12)

    # Step 4: Create animated height field
    print("\n--- Step 4: Creating Animated Height Field ---")
    create_animated_height_field(data, stage, start_frame=1, fps=12)

    # Step 5: Create vector field at final timestep
    print("\n--- Step 5: Creating Velocity Vector Field ---")
    create_vector_field(data, stage, timestep=-1, start_frame=1, fps=12)

    # Step 6: Verify animation
    verify_animation(stage, data, start_frame=1, fps=12)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    print("\n" + "=" * 80)
    print("Tutorial 10 complete!")
    print(f"USD output: {usd_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
