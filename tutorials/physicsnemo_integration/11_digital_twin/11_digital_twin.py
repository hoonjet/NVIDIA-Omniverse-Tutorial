"""
================================================================================
Tutorial 11: Digital Twin Pipeline - End-to-End Simulation to Visualization
================================================================================

This is the capstone tutorial that combines everything learned in previous
tutorials into a complete digital twin pipeline. A digital twin is a virtual
representation of a physical system that is kept in sync with real-time data.

This tutorial builds a digital twin of a heat exchanger:
  1. Define the physical geometry (the "twin" of the real system)
  2. Run a simulation (mimicking PhysicsNeMo inference)
  3. Convert results to USD visualization
  4. Animate the results over time
  5. Store all metadata for reproducibility

The pipeline demonstrates:
  PhysicsNeMo Model → Simulation Output → USD Scene → 3D Visualization

Key Concepts:
  - Digital Twin:  A virtual model of a physical system, updated with real data
  - Pipeline:      A sequence of data processing steps
  - Geometry:      The physical shape of the system (pipes, tanks, etc.)
  - Sensor Data:   Measurements from the physical system
  - Visualization: 3D representation of the system state

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\11_digital_twin.py
================================================================================
"""

import os
import math
import json
from pxr import Usd, UsdGeom, UsdShade, Sdf
from pxr import Gf
import numpy as np


# ==============================================================================
# Part 1: Define the Physical Geometry (Heat Exchanger)
# ==============================================================================

def create_heat_exchanger_geometry(stage):
    """
    Create the 3D geometry of a heat exchanger.

    A heat exchanger transfers heat between two fluids. This simple model
    has:
      - A cylindrical shell (outer container)
      - An inlet pipe (cold fluid in)
      - An outlet pipe (hot fluid out)
      - Internal tube bundle (where heat transfer occurs)

    This geometry represents the "physical" system that the digital twin
    mirrors.

    Args:
        stage (Usd.Stage): The USD stage.

    Returns:
        str: The path of the heat exchanger root prim.
    """
    root_path = "/World/HeatExchanger"
    root = UsdGeom.Xform.Define(stage, root_path)

    # --- Shell (outer cylinder) ---
    # The shell contains the fluid and the tube bundle
    shell = UsdGeom.Cylinder.Define(stage, f"{root_path}/Shell")
    shell.GetHeightAttr().Set(8.0)
    shell.GetRadiusAttr().Set(2.0)
    shell.GetDisplayColorAttr().Set([(0.5, 0.5, 0.5)])  # Gray
    UsdGeom.Xformable(shell).AddTranslateOp().Set(Gf.Vec3d(0.0, 4.0, 0.0))
    print("  [+] Created shell (cylinder, height=8.0, radius=2.0)")

    # --- Inlet pipe (cold fluid enters) ---
    inlet = UsdGeom.Cylinder.Define(stage, f"{root_path}/InletPipe")
    inlet.GetHeightAttr().Set(3.0)
    inlet.GetRadiusAttr().Set(0.3)
    inlet.GetDisplayColorAttr().Set([(0.0, 0.0, 1.0)])  # Blue (cold)
    # Rotate to be horizontal and position at the bottom
    inlet_xform = UsdGeom.Xformable(inlet)
    inlet_xform.AddTranslateOp().Set(Gf.Vec3d(-2.5, 1.0, 0.0))
    inlet_xform.AddRotateZOp().Set(90.0)
    print("  [+] Created inlet pipe (blue, cold fluid)")

    # --- Outlet pipe (hot fluid exits) ---
    outlet = UsdGeom.Cylinder.Define(stage, f"{root_path}/OutletPipe")
    outlet.GetHeightAttr().Set(3.0)
    outlet.GetRadiusAttr().Set(0.3)
    outlet.GetDisplayColorAttr().Set([(1.0, 0.0, 0.0)])  # Red (hot)
    outlet_xform = UsdGeom.Xformable(outlet)
    outlet_xform.AddTranslateOp().Set(Gf.Vec3d(2.5, 7.0, 0.0))
    outlet_xform.AddRotateZOp().Set(90.0)
    print("  [+] Created outlet pipe (red, hot fluid)")

    # --- Internal tube bundle ---
    # Create a grid of small tubes inside the shell
    tube_parent = UsdGeom.Xform.Define(stage, f"{root_path}/TubeBundle")

    num_tubes_x = 3
    num_tubes_z = 3
    tube_spacing = 0.8

    for i in range(num_tubes_x):
        for j in range(num_tubes_z):
            tube_path = f"{root_path}/TubeBundle/Tube_{i}_{j}"
            tube = UsdGeom.Cylinder.Define(stage, tube_path)
            tube.GetHeightAttr().Set(7.0)  # Slightly shorter than shell
            tube.GetRadiusAttr().Set(0.15)
            tube.GetDisplayColorAttr().Set([(0.7, 0.7, 0.3)])  # Brass color

            # Position tubes in a grid inside the shell
            x = (i - (num_tubes_x - 1) / 2) * tube_spacing
            z = (j - (num_tubes_z - 1) / 2) * tube_spacing
            UsdGeom.Xformable(tube).AddTranslateOp().Set(Gf.Vec3d(x, 4.0, z))

    print(f"  [+] Created tube bundle: {num_tubes_x}x{num_tubes_z} = {num_tubes_x * num_tubes_z} tubes")

    return root_path


# ==============================================================================
# Part 2: Simulate Heat Transfer (Mimicking PhysicsNeMo)
# ==============================================================================

def simulate_heat_transfer(num_timesteps=20):
    """
    Simulate heat transfer in the heat exchanger over time.

    This mimics a PhysicsNeMo model inference. In a real pipeline, this
    would call the trained model to predict temperature distribution.

    The simulation models:
      - Cold fluid entering at the bottom (20°C)
      - Hot fluid exiting at the top (80°C)
      - Temperature gradient along the shell height
      - Tube bundle heating up over time

    Args:
        num_timesteps (int): Number of simulation timesteps.

    Returns:
        dict: Simulation results including:
            - shell_temps: Temperature at each height over time
            - tube_temps: Temperature of each tube over time
            - inlet_temp: Inlet temperature (constant)
            - outlet_temp: Outlet temperature (changes over time)
            - metadata: Simulation parameters
    """
    # Shell temperature profile (along height, over time)
    # The shell has 10 measurement points along its height
    num_height_points = 10
    shell_temps = np.zeros((num_timesteps, num_height_points))

    # Tube temperatures (3x3 grid, over time)
    num_tubes_x = 3
    num_tubes_z = 3
    tube_temps = np.zeros((num_timesteps, num_tubes_x, num_tubes_z))

    # Inlet and outlet temperatures
    inlet_temp = 20.0  # Cold fluid enters at 20°C
    outlet_temps = np.zeros(num_timesteps)

    for t in range(num_timesteps):
        time = t / (num_timesteps - 1)  # Normalized time [0, 1]

        # Shell temperature: linear gradient from bottom (cold) to top (hot)
        # The gradient steepens over time as the system reaches steady state
        for h in range(num_height_points):
            height_frac = h / (num_height_points - 1)
            # Temperature increases with height, and with time
            steady_state = inlet_temp + (80.0 - inlet_temp) * height_frac
            transient_factor = 1.0 - math.exp(-3.0 * time)  # Exponential approach
            shell_temps[t, h] = inlet_temp + (steady_state - inlet_temp) * transient_factor

        # Tube temperatures: average of surrounding shell temperature
        for i in range(num_tubes_x):
            for j in range(num_tubes_z):
                # Tubes are at mid-height, so use the middle shell temperature
                mid_h = num_height_points // 2
                tube_temps[t, i, j] = shell_temps[t, mid_h]

        # Outlet temperature: temperature at the top of the shell
        outlet_temps[t] = shell_temps[t, -1]

    print(f"  [+] Simulated heat transfer: {num_timesteps} timesteps")
    print(f"      Inlet temp: {inlet_temp:.1f}°C (constant)")
    print(f"      Outlet temp: {outlet_temps[0]:.1f}°C → {outlet_temps[-1]:.1f}°C")

    return {
        "shell_temps": shell_temps,
        "tube_temps": tube_temps,
        "inlet_temp": inlet_temp,
        "outlet_temps": outlet_temps,
        "num_timesteps": num_timesteps,
        "num_height_points": num_height_points,
        "metadata": {
            "system": "heat_exchanger",
            "model": "PhysicsNeMo (simulated)",
            "inlet_temperature": inlet_temp,
            "target_outlet_temperature": 80.0,
            "num_timesteps": num_timesteps,
            "fluid": "water",
            "material": "stainless_steel",
        },
    }


# ==============================================================================
# Part 3: Colormap
# ==============================================================================

def temp_to_color(temp, tmin=20.0, tmax=80.0):
    """
    Map temperature to color: blue (cold) → red (hot).

    Args:
        temp (float): Temperature in °C.
        tmin (float): Minimum temperature for colormap.
        tmax (float): Maximum temperature for colormap.

    Returns:
        tuple: (R, G, B) color.
    """
    if tmax > tmin:
        t = (temp - tmin) / (tmax - tmin)
    else:
        t = 0.5
    t = max(0.0, min(1.0, t))

    if t < 0.5:
        # Blue to Green
        t2 = t * 2.0
        return (0.0, t2, 1.0 - t2 * 0.5)
    else:
        # Green to Red
        t2 = (t - 0.5) * 2.0
        return (t2, 1.0 - t2, 0.0)


# ==============================================================================
# Part 4: Animate the Heat Exchanger with Simulation Results
# ==============================================================================

def animate_with_simulation(stage, sim_data, start_frame=1, fps=6):
    """
    Animate the heat exchanger geometry with simulation results.

    This creates sensor point prims along the shell height and animates
    their color based on the simulated temperature at each timestep.

    Args:
        stage (Usd.Stage): The USD stage.
        sim_data (dict): Simulation results from simulate_heat_transfer().
        start_frame (int): First frame number.
        fps (int): Frames per timestep.
    """
    shell_temps = sim_data["shell_temps"]
    num_timesteps = sim_data["num_timesteps"]
    num_height_points = sim_data["num_height_points"]

    # Create sensor points along the shell height
    sensor_parent = UsdGeom.Xform.Define(stage, "/World/HeatExchanger/Sensors")

    for h in range(num_height_points):
        height_frac = h / (num_height_points - 1)
        y_pos = height_frac * 8.0  # Shell height is 8.0

        # Create a sensor sphere on the side of the shell
        sensor_path = f"/World/HeatExchanger/Sensors/Sensor_{h:02d}"
        sensor = UsdGeom.Sphere.Define(stage, sensor_path)
        sensor.GetRadiusAttr().Set(0.3)

        # Position on the side of the shell (radius = 2.0)
        UsdGeom.Xformable(sensor).AddTranslateOp().Set(
            Gf.Vec3d(2.5, y_pos, 0.0)  # Outside the shell
        )

        # Animate color based on temperature
        color_attr = sensor.GetDisplayColorAttr()
        temp_attr = sensor.GetPrim().CreateAttribute(
            "data:temperature",
            Sdf.ValueTypeNames.Float
        )

        for t in range(num_timesteps):
            frame = start_frame + t * fps
            temp = shell_temps[t, h]
            color = temp_to_color(temp)
            color_attr.Set([color], frame)
            temp_attr.Set(float(temp), frame)

    # Animate tube colors
    tube_temps = sim_data["tube_temps"]
    for i in range(3):
        for j in range(3):
            tube_path = f"/World/HeatExchanger/TubeBundle/Tube_{i}_{j}"
            tube_prim = stage.GetPrimAtPath(tube_path)
            if tube_prim.IsValid():
                color_attr = tube_prim.GetAttribute("primvars:displayColor")
                for t in range(num_timesteps):
                    frame = start_frame + t * fps
                    temp = tube_temps[t, i, j]
                    color = temp_to_color(temp)
                    color_attr.Set([color], frame)

    # Set timeline
    end_frame = start_frame + (num_timesteps - 1) * fps
    stage.SetStartTimeCode(start_frame)
    stage.SetEndTimeCode(end_frame)
    stage.SetTimeCodesPerSecond(24.0)

    print(f"  [+] Animated {num_height_points} sensors and 9 tubes over {num_timesteps} timesteps")
    print(f"      Timeline: frames {start_frame} to {end_frame}")


# ==============================================================================
# Part 5: Store Digital Twin Metadata
# ==============================================================================

def store_digital_twin_metadata(stage, sim_data):
    """
    Store all digital twin metadata in the USD scene.

    This includes:
      - System description
      - Simulation parameters
      - Sensor configuration
      - Model information

    Args:
        stage (Usd.Stage): The USD stage.
        sim_data (dict): Simulation data.
    """
    meta_prim = stage.DefinePrim("/World/HeatExchanger/DigitalTwinMetadata", "Xform")

    metadata = sim_data["metadata"]

    for key, value in metadata.items():
        if isinstance(value, str):
            sdf_type = Sdf.ValueTypeNames.String
        elif isinstance(value, float):
            sdf_type = Sdf.ValueTypeNames.Float
        elif isinstance(value, int):
            sdf_type = Sdf.ValueTypeNames.Int
        else:
            sdf_type = Sdf.ValueTypeNames.String
            value = str(value)

        meta_prim.CreateAttribute(f"twin:{key}", sdf_type).Set(value)

    # Store final outlet temperature
    meta_prim.CreateAttribute(
        "twin:final_outlet_temp",
        Sdf.ValueTypeNames.Float
    ).Set(float(sim_data["outlet_temps"][-1]))

    print(f"  [+] Stored {len(metadata) + 1} metadata fields")


# ==============================================================================
# Part 6: Generate Summary Report
# ==============================================================================

def generate_summary(sim_data, output_dir):
    """
    Generate a text summary of the digital twin simulation.

    Args:
        sim_data (dict): Simulation data.
        output_dir (str): Directory to save the report.
    """
    report_path = os.path.join(output_dir, "digital_twin_report.txt")

    with open(report_path, "w") as f:
        f.write("=" * 60 + "\n")
        f.write("Digital Twin Simulation Report\n")
        f.write("Heat Exchanger System\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"System: {sim_data['metadata']['system']}\n")
        f.write(f"Model: {sim_data['metadata']['model']}\n")
        f.write(f"Fluid: {sim_data['metadata']['fluid']}\n")
        f.write(f"Material: {sim_data['metadata']['material']}\n\n")

        f.write(f"Inlet Temperature: {sim_data['inlet_temp']:.1f} C\n")
        f.write(f"Target Outlet Temperature: {sim_data['metadata']['target_outlet_temperature']:.1f} C\n")
        f.write(f"Final Outlet Temperature: {sim_data['outlet_temps'][-1]:.1f} C\n\n")

        f.write("Temperature Profile Over Time:\n")
        f.write(f"{'Timestep':>8} | {'Outlet Temp':>12} | {'Shell Bottom':>12} | {'Shell Top':>10}\n")
        f.write("-" * 50 + "\n")

        for t in range(sim_data["num_timesteps"]):
            f.write(f"{t:>8} | {sim_data['outlet_temps'][t]:>10.1f}C | "
                    f"{sim_data['shell_temps'][t, 0]:>10.1f}C | "
                    f"{sim_data['shell_temps'][t, -1]:>8.1f}C\n")

        f.write("\n" + "=" * 60 + "\n")
        f.write("End of Report\n")

    print(f"  [+] Generated report: {report_path}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs the complete digital twin pipeline."""
    print("=" * 80)
    print("Tutorial 11: Digital Twin Pipeline - End-to-End Simulation to Visualization")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # --- Pipeline Step 1: Create USD Stage ---
    print("\n--- Step 1: Creating USD Stage ---")
    usd_file = os.path.join(output_dir, "11_digital_twin.usda")
    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- Pipeline Step 2: Create Physical Geometry ---
    print("\n--- Step 2: Creating Heat Exchanger Geometry ---")
    create_heat_exchanger_geometry(stage)

    # --- Pipeline Step 3: Run Simulation ---
    print("\n--- Step 3: Running Heat Transfer Simulation ---")
    sim_data = simulate_heat_transfer(num_timesteps=20)

    # --- Pipeline Step 4: Animate with Simulation Results ---
    print("\n--- Step 4: Animating with Simulation Results ---")
    animate_with_simulation(stage, sim_data, start_frame=1, fps=6)

    # --- Pipeline Step 5: Store Metadata ---
    print("\n--- Step 5: Storing Digital Twin Metadata ---")
    store_digital_twin_metadata(stage, sim_data)

    # --- Pipeline Step 6: Generate Report ---
    print("\n--- Step 6: Generating Summary Report ---")
    generate_summary(sim_data, output_dir)

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Digital twin scene saved to: {usd_file}")

    print("\n" + "=" * 80)
    print("Tutorial 11 complete! Digital Twin Pipeline finished.")
    print(f"USD scene:    {usd_file}")
    print(f"Report:       {os.path.join(output_dir, 'digital_twin_report.txt')}")
    print("=" * 80)
    print("\nPipeline Summary:")
    print("  Geometry → Simulation → USD Visualization → Animation → Metadata")
    print("\nAll 11 tutorials complete! You now have a comprehensive understanding")
    print("of USD and Omniverse concepts, ready for PhysicsNeMo integration.")


if __name__ == "__main__":
    main()
