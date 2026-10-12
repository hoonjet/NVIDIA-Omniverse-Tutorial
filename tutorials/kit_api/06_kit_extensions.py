"""
================================================================================
Tutorial 06: Omniverse Kit Extensions - Structure and Registration
================================================================================

This tutorial covers the structure and concepts of Omniverse Kit Extensions.

NOTE: Omniverse Kit requires a full Omniverse installation (RTX GPU recommended).
This tutorial focuses on the CONCEPTS and STRUCTURE of extensions, using
USD-only APIs that work in our virtual environment. The extension patterns
shown here mirror what you would use in a real Omniverse Kit extension.

Topics covered:
  1. What is a Kit Extension?
  2. Extension file structure (extension.toml + Python scripts)
  3. Extension lifecycle (on_startup, on_shutdown)
  4. Creating a USD-based "extension-like" module
  5. Registering and using custom USD schemas

Key Concepts:
  - Extension:  A modular plugin for Omniverse Kit. Extensions add functionality
                like tools, UI panels, importers/exporters, etc.
  - extension.toml: Configuration file that declares the extension's metadata
                and entry points.
  - on_startup:  Called when the extension is loaded. Initialize resources here.
  - on_shutdown: Called when the extension is unloaded. Clean up resources here.

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\06_kit_extensions.py
================================================================================
"""

import os
import sys
import textwrap
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf


# ==============================================================================
# Part 1: Extension File Structure
# ==============================================================================

def create_extension_structure(output_dir):
    """
    Create the file structure of a typical Omniverse Kit extension.

    A Kit extension has this structure:

    ```
    my_extension/
    ├── extension.toml       # Extension metadata and config
    ├── __init__.py          # Python entry point
    ├── extension.py         # Extension class with lifecycle methods
    └── config/
        └── extension.toml   # (alternative config location)
    ```

    This function creates these files as templates for learning.

    Args:
        output_dir (str): Directory to create the extension structure in.
    """
    ext_dir = os.path.join(output_dir, "my_extension")
    os.makedirs(ext_dir, exist_ok=True)

    # --- Create extension.toml ---
    # This is the configuration file that Kit reads to understand the extension.
    # It declares the extension's name, version, dependencies, and entry points.
    toml_content = textwrap.dedent("""\
        # ============================================================================
        # extension.toml - Omniverse Kit Extension Configuration
        # ============================================================================
        # This file declares the extension's metadata and entry points.
        # Kit reads this file to load and manage the extension.
        # ============================================================================

        # Unique extension identifier (org.module.name format)
        [package]
        version = "1.0.0"
        description = "A sample extension for learning Omniverse Kit"

        # Core extension settings
        [core]
        reloadable = true  # Whether the extension can be hot-reloaded

        # Python module settings
        # Kit will import this module and call its lifecycle functions
        [[python.module]]
        name = "my_extension"

        # Extension dependencies
        # These extensions must be loaded before this one
        [[dependencies]]
        name = "omni.usd"
        version = "*"  # Any version

        [[dependencies]]
        name = "omni.kit.app"
        version = "*"
    """)

    with open(os.path.join(ext_dir, "extension.toml"), "w") as f:
        f.write(toml_content)
    print(f"  [+] Created extension.toml")

    # --- Create extension.py ---
    # This is the main Python file that implements the extension lifecycle.
    # In a real Kit extension, Kit calls these functions automatically.
    ext_py_content = textwrap.dedent('''\
        """
        Extension Main Module - Lifecycle Management

        In Omniverse Kit, the extension lifecycle is managed by two functions:
          - on_startup(): Called when the extension is loaded
          - on_shutdown(): Called when the extension is unloaded

        These functions receive an "ext_obj" (extension object) that provides
        access to Kit's extension management API.
        """

        # Extension state - stored globally for simplicity
        # In production, use a proper class-based approach
        _extension_state = {}


        def on_startup(ext_obj):
            """
            Called when the extension is loaded by Kit.

            Use this function to:
              - Initialize resources (USD stages, data structures)
              - Register UI elements (menus, toolbars, panels)
              - Set up event listeners
              - Load configuration

            Args:
                ext_obj: The extension object provided by Kit.
                         Contains the extension ID and management API.
            """
            print(f"[my_extension] Starting up (id: {ext_obj.id})")

            # Store the extension ID for later use
            _extension_state["id"] = ext_obj.id
            _extension_state["is_running"] = True

            # In a real extension, you would:
            # 1. Register UI elements:
            #    import omni.kit.ui
            #    omni.kit.ui.create_menu_item("Window/My Tool", show_my_tool)

            # 2. Register USD callbacks:
            #    import omni.usd
            #    stage_event = omni.usd.get_context().get_stage_event_stream()
            #    stage_event_sub = stage_event.create_subscription_to_pop(
            #        on_stage_event
            #    )

            print("[my_extension] Startup complete")


        def on_shutdown(ext_obj):
            """
            Called when the extension is unloaded by Kit.

            Use this function to:
              - Clean up resources
              - Unregister UI elements
              - Remove event listeners
              - Save state if needed

            Args:
                ext_obj: The extension object provided by Kit.
            """
            print(f"[my_extension] Shutting down (id: {ext_obj.id})")

            # Clean up state
            _extension_state["is_running"] = False
            _extension_state.clear()

            print("[my_extension] Shutdown complete")


        def get_extension_state():
            """
            Utility function to check the extension's current state.

            Returns:
                dict: The current extension state.
            """
            return _extension_state.copy()
    ''')

    with open(os.path.join(ext_dir, "extension.py"), "w") as f:
        f.write(ext_py_content)
    print(f"  [+] Created extension.py")

    # --- Create __init__.py ---
    init_content = textwrap.dedent("""\
        # Extension package init
        # This file makes the directory a Python package.
        # Kit imports this package and calls extension.on_startup/on_shutdown.

        from .extension import on_startup, on_shutdown, get_extension_state
    """)

    with open(os.path.join(ext_dir, "__init__.py"), "w") as f:
        f.write(init_content)
    print(f"  [+] Created __init__.py")

    return ext_dir


# ==============================================================================
# Part 2: Simulating Extension Lifecycle
# ==============================================================================

class MockExtensionObject:
    """
    A mock extension object that simulates what Kit provides.

    In a real Kit environment, the extension object (ext_obj) contains:
      - id: A unique string identifier for the extension
      - manager: The extension manager API
      - path: The filesystem path to the extension

    We create a simple mock to demonstrate the lifecycle.
    """

    def __init__(self, ext_id="my.extension.sample"):
        """Initialize the mock extension object with an ID."""
        self.id = ext_id
        self.path = ""


def simulate_extension_lifecycle(ext_dir):
    """
    Simulate the Kit extension lifecycle by importing and calling the
    on_startup/on_shutdown functions.

    This demonstrates how Kit loads and manages extensions:
      1. Add the extension directory to Python path
      2. Import the extension module
      3. Call on_startup() with the extension object
      4. ... extension runs ...
      5. Call on_shutdown() to clean up

    Args:
        ext_dir (str): Path to the extension directory.
    """
    print("\n--- Simulating Extension Lifecycle ---")

    # Add the extension's parent directory to Python path
    # so we can import the extension as a module
    parent_dir = os.path.dirname(ext_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    # Import the extension module
    # In Kit, this is done automatically based on extension.toml
    import my_extension

    # Create a mock extension object
    ext_obj = MockExtensionObject("my.extension.sample")

    # --- Call on_startup ---
    # Kit calls this when the extension is loaded
    print("\n  [Kit] Loading extension 'my_extension'...")
    my_extension.on_startup(ext_obj)

    # --- Check extension state ---
    state = my_extension.get_extension_state()
    print(f"\n  Extension state after startup: {state}")

    # --- Simulate extension doing work ---
    print("\n  [Kit] Extension is running... (doing work)")

    # --- Call on_shutdown ---
    # Kit calls this when the extension is unloaded
    print("\n  [Kit] Unloading extension 'my_extension'...")
    my_extension.on_shutdown(ext_obj)

    # --- Verify cleanup ---
    state = my_extension.get_extension_state()
    print(f"\n  Extension state after shutdown: {state}")


# ==============================================================================
# Part 3: Custom USD Schema Definition
# ==============================================================================

def create_custom_schema_demo(stage):
    """
    Demonstrate a pattern similar to Kit extensions: defining custom
    data on USD prims using "applied API schemas" and custom attributes.

    In Omniverse, extensions often define custom schemas to represent
    domain-specific data (e.g., simulation parameters, robot joints, etc.).

    This function demonstrates:
      1. Creating a prim with custom attributes
      2. Applying an API schema to a prim
      3. Reading custom data back

    Args:
        stage (Usd.Stage): The stage to work on.
    """
    # Create a prim that represents a "simulation object"
    # In a real extension, this might be a robot, a sensor, etc.
    sim_obj = UsdGeom.Xform.Define(stage, "/World/SimulationObject")

    # Add custom attributes that represent simulation parameters
    # These are not part of the standard USD schema - they are custom
    # data that our "extension" defines and uses

    # Create a custom "simulationType" attribute
    # This could represent the type of physics simulation
    sim_type_attr = sim_obj.GetPrim().CreateAttribute(
        "simulation:type",
        Sdf.ValueTypeNames.String
    )
    sim_type_attr.Set("fluid_dynamics")

    # Create a custom "timeStep" attribute
    # This represents the simulation time step in seconds
    timestep_attr = sim_obj.GetPrim().CreateAttribute(
        "simulation:timeStep",
        Sdf.ValueTypeNames.Float
    )
    timestep_attr.Set(0.016)  # ~60 FPS

    # Create a custom "maxIterations" attribute
    max_iter_attr = sim_obj.GetPrim().CreateAttribute(
        "simulation:maxIterations",
        Sdf.ValueTypeNames.Int
    )
    max_iter_attr.Set(1000)

    # Create a custom "velocity" attribute (array of 3 floats)
    velocity_attr = sim_obj.GetPrim().CreateAttribute(
        "simulation:velocity",
        Sdf.ValueTypeNames.Float3
    )
    velocity_attr.Set(Gf.Vec3f(1.0, 0.5, 0.0))

    print("  [+] Created simulation object with custom attributes:")
    print(f"      simulation:type = {sim_type_attr.Get()}")
    print(f"      simulation:timeStep = {timestep_attr.Get()}")
    print(f"      simulation:maxIterations = {max_iter_attr.Get()}")
    print(f"      simulation:velocity = {velocity_attr.Get()}")

    # Read back all custom attributes
    print("\n  Reading back all custom attributes:")
    for attr in sim_obj.GetPrim().GetAttributes():
        name = attr.GetName()
        if name.startswith("simulation:"):
            print(f"    {name} = {attr.Get()}")


# ==============================================================================
# Part 4: Extension Configuration Pattern
# ==============================================================================

def create_config_pattern(stage):
    """
    Demonstrate the configuration pattern used by Kit extensions.

    Extensions often store their configuration as USD data on the stage.
    This allows the configuration to be saved with the scene and shared
    between users.

    This function creates a "configuration" prim that stores settings
    for our hypothetical extension.

    Args:
        stage (Usd.Stage): The stage to store configuration on.
    """
    # Create a configuration prim under a special "/Extension" namespace
    # This is a common pattern: extensions store their data under a
    # dedicated prim path to avoid conflicts
    config_prim = stage.DefinePrim("/ExtensionConfig/MyExtension", "Xform")

    # Store configuration as custom attributes
    config_prim.CreateAttribute("enabled", Sdf.ValueTypeNames.Bool).Set(True)
    config_prim.CreateAttribute("autoUpdate", Sdf.ValueTypeNames.Bool).Set(False)
    config_prim.CreateAttribute("updateInterval", Sdf.ValueTypeNames.Float).Set(1.0)
    config_prim.CreateAttribute("logLevel", Sdf.ValueTypeNames.String).Set("INFO")

    # Store a list of target prims (as a string array)
    config_prim.CreateAttribute("targetPrims", Sdf.ValueTypeNames.StringArray).Set(
        ["/World/SimulationObject", "/World/AnotherObject"]
    )

    print("  [+] Created extension configuration:")
    for attr in config_prim.GetAttributes():
        name = attr.GetName()
        value = attr.Get()
        if name not in ("xformOpOrder",):
            print(f"      {name} = {value}")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 06: Omniverse Kit Extensions - Structure and Registration")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Create extension file structure
    print("\n--- Step 1: Creating Extension File Structure ---")
    ext_dir = create_extension_structure(output_dir)
    print(f"  Extension directory: {ext_dir}")

    # Step 2: Simulate extension lifecycle
    print("\n--- Step 2: Simulating Extension Lifecycle ---")
    simulate_extension_lifecycle(ext_dir)

    # Step 3: Create a USD stage with custom schema demo
    print("\n--- Step 3: Custom USD Schema Demo ---")
    usd_file = os.path.join(output_dir, "06_kit_extensions.usda")
    if os.path.exists(usd_file):
        os.remove(usd_file)

    stage = Usd.Stage.CreateNew(usd_file)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    create_custom_schema_demo(stage)
    create_config_pattern(stage)

    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {usd_file}")

    print("\n" + "=" * 80)
    print("Tutorial 06 complete!")
    print(f"Extension template: {ext_dir}")
    print(f"USD output: {usd_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
