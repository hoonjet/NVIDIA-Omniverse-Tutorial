"""
================================================================================
Tutorial 08: Omniverse Live Sync - Collaborative Scene Editing Concepts
================================================================================

This tutorial covers the concepts behind Omniverse's Live Sync (live editing)
feature. In Omniverse, multiple users can edit the same USD scene simultaneously,
with changes propagating in real-time to all connected clients.

NOTE: Full Live Sync requires an Omniverse Nucleus server. This tutorial
demonstrates the CONCEPTS using local file-based simulation that works
in our virtual environment.

Topics covered:
  1. The Live Sync architecture (Nucleus server, clients, layers)
  2. Simulating multi-client scene editing
  3. Layer composition (how multiple edits combine)
  4. Conflict resolution patterns
  5. Change notification and tracking

Key Concepts:
  - Nucleus Server: The central server that stores USD files and manages
                     concurrent access by multiple clients.
  - Live Layer:     A special USD layer that supports real-time updates.
                     Changes are immediately visible to all connected clients.
  - Composition:    USD's system for combining multiple layers (opinions)
                     into a single scene. Stronger opinions override weaker ones.
  - Change Batch:   A group of edits sent together to minimize network traffic.

Run:
  cd E:\omniverse_env
  Scripts\activate
  python tutorials\08_live_sync.py
================================================================================
"""

import os
import time
import threading
from pxr import Usd, UsdGeom, Sdf
from pxr import Gf


# ==============================================================================
# Part 1: Layer Composition (How USD Combines Edits)
# ==============================================================================

def demonstrate_layer_composition(output_dir):
    """
    Demonstrate how USD's layer composition system works.

    USD uses a "stronger opinion wins" system for combining layers.
    When multiple layers define the same attribute, the stronger layer's
    value takes precedence.

    Layer strength (from strongest to weakest):
      1. Session layer (strongest - per-client overrides)
      2. Root layer (the main scene file)
      3. Sublayers (weaker layers included in the root)
      4. References (weakest - external file references)

    This function creates two layers and shows how they compose.

    Args:
        output_dir (str): Directory to save layer files.
    """
    print("--- Layer Composition Demo ---")

    # --- Create the base layer (weaker opinion) ---
    # This represents the "base" scene that everyone starts with
    base_path = os.path.join(output_dir, "base_layer.usda")
    if os.path.exists(base_path):
        os.remove(base_path)

    base_stage = Usd.Stage.CreateNew(base_path)
    UsdGeom.SetStageUpAxis(base_stage, UsdGeom.Tokens.y)

    # Create a cube with size 2.0 and red color
    cube = UsdGeom.Cube.Define(base_stage, "/World/Cube")
    cube.GetSizeAttr().Set(2.0)
    cube.GetDisplayColorAttr().Set([(1.0, 0.0, 0.0)])  # Red
    base_stage.SetDefaultPrim(cube.GetPrim())
    base_stage.GetRootLayer().Save()
    print(f"  [+] Base layer: size=2.0, color=red")

    # --- Create the override layer (stronger opinion) ---
    # This represents a client's local edits that override the base
    override_path = os.path.join(output_dir, "override_layer.usda")
    if os.path.exists(override_path):
        os.remove(override_path)

    # Create a new stage that references the base layer
    override_stage = Usd.Stage.CreateNew(override_path)
    UsdGeom.SetStageUpAxis(override_stage, UsdGeom.Tokens.y)

    # Reference the base layer
    world = UsdGeom.Xform.Define(override_stage, "/World")
    override_stage.SetDefaultPrim(world.GetPrim())

    world_prim = override_stage.GetPrimAtPath("/World")
    world_prim.GetReferences().AddReference(base_path)

    # Now OVERRIDE the cube's size and color
    # The override layer has a STRONGER opinion, so its values win
    override_cube = override_stage.OverridePrim("/World/Cube")
    # Use CreateAttribute with explicit type to avoid empty typeName error
    override_cube.CreateAttribute("size", Sdf.ValueTypeNames.Double).Set(5.0)
    override_cube.CreateAttribute("primvars:displayColor", Sdf.ValueTypeNames.Color3fArray).Set([(0.0, 0.0, 1.0)])

    override_stage.GetRootLayer().Save()
    print(f"  [+] Override layer: size=5.0, color=blue")

    # --- Open the composed stage and verify ---
    composed_stage = Usd.Stage.Open(override_path)
    composed_cube = composed_stage.GetPrimAtPath("/World/Cube")

    final_size = composed_cube.GetAttribute("size").Get()
    final_color = composed_cube.GetAttribute("primvars:displayColor").Get()

    print(f"\n  Composed result (override wins):")
    print(f"    size = {final_size} (base: 2.0, override: 5.0)")
    print(f"    color = {final_color} (base: red, override: blue)")

    return base_path, override_path


# ==============================================================================
# Part 2: Simulating Multi-Client Editing
# ==============================================================================

class SimulatedClient:
    """
    Simulates a client connected to a shared USD scene.

    In real Omniverse Live Sync, each client has its own session layer
    for local overrides, and all clients share the root layer via Nucleus.

    This class simulates that behavior:
      - Each client has a name and a "session layer" (local overrides)
      - Clients can make edits to the shared scene
      - Edits are "published" to the shared layer

    Attributes:
        name (str): The client's display name.
        session_layer (Sdf.Layer): The client's local session layer.
        edits (list): A log of edits made by this client.
    """

    def __init__(self, name, shared_stage_path):
        """
        Initialize a simulated client.

        Args:
            name (str): The client's display name.
            shared_stage_path (str): Path to the shared USD file.
        """
        self.name = name
        self.shared_stage_path = shared_stage_path
        self.edits = []  # Log of edits made by this client

        # Open the shared stage
        # In real Live Sync, this would connect to Nucleus
        self.stage = Usd.Stage.Open(shared_stage_path)

        # Create a session layer for this client's local overrides
        # The session layer is the STRONGEST layer - it overrides everything
        self.session_layer = Sdf.Layer.CreateAnonymous(f"session_{name}")
        self.stage.GetSessionLayer().subLayerPaths.append(self.session_layer.identifier)

        print(f"  [+] Client '{name}' connected to scene")

    def edit_attribute(self, prim_path, attr_name, value):
        """
        Edit an attribute on a prim.

        In real Live Sync, this edit would be:
          1. Written to the client's session layer (immediate local view)
          2. Published to the Nucleus server (propagated to other clients)

        Args:
            prim_path (str): The path of the prim to edit.
            attr_name (str): The name of the attribute to change.
            value: The new value for the attribute.
        """
        # Get or create the prim in the session layer
        # This creates an "override" opinion in the session layer
        prim = self.stage.GetPrimAtPath(prim_path)
        if not prim.IsValid():
            print(f"  [{self.name}] WARNING: Prim not found: {prim_path}")
            return

        # Set the attribute value
        # This goes into the session layer (strongest opinion)
        attr = prim.GetAttribute(attr_name)
        if not attr:
            attr = prim.CreateAttribute(attr_name, Sdf.ValueTypeNames.Float)

        attr.Set(value)

        # Log the edit
        edit = {
            "client": self.name,
            "prim": prim_path,
            "attribute": attr_name,
            "value": value,
            "timestamp": time.time(),
        }
        self.edits.append(edit)
        print(f"  [{self.name}] Edit: {prim_path}.{attr_name} = {value}")

    def publish_edits(self):
        """
        Publish session layer edits to the shared root layer.

        In real Live Sync, this would send the edits to the Nucleus server,
        which would then propagate them to all connected clients.

        Here, we save the stage to simulate publishing.
        """
        self.stage.GetRootLayer().Save()
        print(f"  [{self.name}] Published {len(self.edits)} edits to shared scene")

    def get_edit_log(self):
        """
        Return the log of edits made by this client.

        Returns:
            list: A list of edit dictionaries.
        """
        return self.edits.copy()


# ==============================================================================
# Part 3: Multi-Client Collaboration Demo
# ==============================================================================

def multi_client_demo(output_dir):
    """
    Demonstrate multiple clients editing the same scene simultaneously.

    This simulates two users (Alice and Bob) editing a shared scene:
      1. Alice changes the cube's size
      2. Bob changes the cube's color
      3. Both publish their changes
      4. The final scene reflects both edits

    Args:
        output_dir (str): Directory for output files.
    """
    print("\n--- Multi-Client Collaboration Demo ---")

    # Create the shared scene file
    shared_path = os.path.join(output_dir, "shared_scene.usda")
    if os.path.exists(shared_path):
        os.remove(shared_path)

    # Create the base scene
    stage = Usd.Stage.CreateNew(shared_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 0.01)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # Create a shared cube
    cube = UsdGeom.Cube.Define(stage, "/World/SharedCube")
    cube.GetSizeAttr().Set(2.0)
    cube.GetDisplayColorAttr().Set([(0.5, 0.5, 0.5)])  # Gray
    stage.GetRootLayer().Save()
    print("  [+] Created shared scene with a gray cube (size=2.0)")

    # --- Alice connects and edits the size ---
    print("\n  Alice connects:")
    alice = SimulatedClient("Alice", shared_path)
    alice.edit_attribute("/World/SharedCube", "size", 4.0)

    # --- Bob connects and edits the color ---
    print("\n  Bob connects:")
    bob = SimulatedClient("Bob", shared_path)
    bob.edit_attribute("/World/SharedCube", "primvars:displayColor", [(0.0, 1.0, 0.0)])

    # --- Both publish their changes ---
    print("\n  Publishing changes:")
    alice.publish_edits()
    bob.publish_edits()

    # --- Verify the final state ---
    print("\n  Final scene state:")
    final_stage = Usd.Stage.Open(shared_path)
    final_cube = final_stage.GetPrimAtPath("/World/SharedCube")
    final_size = final_cube.GetAttribute("size").Get()
    final_color = final_cube.GetAttribute("primvars:displayColor").Get()
    print(f"    size = {final_size} (Alice set this to 4.0)")
    print(f"    color = {final_color} (Bob set this to green)")

    # --- Print edit logs ---
    print("\n  Edit logs:")
    print(f"    Alice's edits: {len(alice.get_edit_log())}")
    print(f"    Bob's edits: {len(bob.get_edit_log())}")


# ==============================================================================
# Part 4: Change Tracking
# ==============================================================================

def demonstrate_change_tracking(output_dir):
    """
    Demonstrate how to track changes to a USD stage.

    In Omniverse Live Sync, clients receive notifications when other
    clients make changes. This function shows how to track changes
    using USD's notification system.

    USD provides Tf.Notice for change notifications. We can register
    a listener that gets called whenever the stage changes.

    Args:
        output_dir (str): Directory for output files.
    """
    from pxr import Tf

    print("\n--- Change Tracking Demo ---")

    # Create a stage
    stage_path = os.path.join(output_dir, "change_tracking.usda")
    if os.path.exists(stage_path):
        os.remove(stage_path)

    stage = Usd.Stage.CreateNew(stage_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    # --- Set up a change tracker ---
    # We'll use a simple list to record changes
    # In real Omniverse, you'd use omni.usd's stage event stream
    changes = []

    def on_stage_changed(notice, sender):
        """
        Callback function called when the stage changes.

        Args:
            notice: The notice object containing change details.
            sender: The object that sent the notice (the stage).
        """
        # Check if this is a "objects changed" notice
        if isinstance(notice, Usd.Notice.ObjectsChanged):
            # Get the paths of changed prims
            # GetResyncedPaths: prims that were added/removed/structurally changed
            # GetChangedInfoOnlyPaths: prims whose attributes/metadata changed
            resynced = notice.GetResyncedPaths()
            changed_info = notice.GetChangedInfoOnlyPaths()

            for path in resynced:
                changes.append({
                    "type": "resync",
                    "path": str(path),
                })

            for path in changed_info:
                changes.append({
                    "type": "field_change",
                    "path": str(path),
                })

    # Register the listener
    # Tf.Notice.Register() sets up a callback for stage change notices
    listener = Tf.Notice.Register(Usd.Notice.ObjectsChanged, on_stage_changed, stage)

    # --- Make some changes ---
    print("  Making changes to the stage...")

    # Change 1: Create a cube
    cube = UsdGeom.Cube.Define(stage, "/World/Cube")
    cube.GetSizeAttr().Set(2.0)
    print(f"  [+] Created cube at /World/Cube")

    # Change 2: Create a sphere
    sphere = UsdGeom.Sphere.Define(stage, "/World/Sphere")
    sphere.GetRadiusAttr().Set(1.0)
    print(f"  [+] Created sphere at /World/Sphere")

    # Change 3: Modify the cube's size
    cube.GetSizeAttr().Set(5.0)
    print(f"  [~] Modified cube size to 5.0")

    # --- Report tracked changes ---
    print(f"\n  Tracked {len(changes)} change events:")
    for i, change in enumerate(changes[:10]):  # Show first 10
        print(f"    {i+1}. {change['type']}: {change['path']}")
    if len(changes) > 10:
        print(f"    ... and {len(changes) - 10} more")

    # Clean up the listener
    listener.Revoke()

    # Save
    stage.GetRootLayer().Save()
    print(f"\n  [OK] Stage saved to: {stage_path}")


# ==============================================================================
# Part 5: Conflict Resolution Pattern
# ==============================================================================

def demonstrate_conflict_resolution(output_dir):
    """
    Demonstrate how USD handles conflicting edits from multiple clients.

    When two clients edit the same attribute, USD's composition system
    resolves the conflict based on layer strength:
      - Session layer (strongest) wins over root layer
      - Root layer wins over sublayers
      - Sublayers win over references

    In real Live Sync, the Nucleus server uses a "last writer wins" policy
    for the root layer, but each client's session layer always takes
    precedence locally.

    Args:
        output_dir (str): Directory for output files.
    """
    print("\n--- Conflict Resolution Demo ---")

    # Create a shared scene
    shared_path = os.path.join(output_dir, "conflict_scene.usda")
    if os.path.exists(shared_path):
        os.remove(shared_path)

    stage = Usd.Stage.CreateNew(shared_path)
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)

    world = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(world.GetPrim())

    cube = UsdGeom.Cube.Define(stage, "/World/ContestedCube")
    cube.GetSizeAttr().Set(1.0)  # Initial value
    stage.GetRootLayer().Save()
    print("  [+] Initial scene: cube size = 1.0")

    # Simulate two clients with different session layers
    # Both try to set the cube's size to different values

    # Client A's session layer (sets size to 3.0)
    client_a_layer = Sdf.Layer.CreateAnonymous("client_a")
    client_a_layer.subLayerPaths.clear()

    # Client B's session layer (sets size to 7.0)
    client_b_layer = Sdf.Layer.CreateAnonymous("client_b")
    client_b_layer.subLayerPaths.clear()

    # Open the stage with Client A's session layer
    stage_a = Usd.Stage.Open(shared_path)
    stage_a.GetSessionLayer().subLayerPaths.append(client_a_layer.identifier)

    # Client A sets size to 3.0 in their session layer
    prim_a = stage_a.OverridePrim("/World/ContestedCube")
    prim_a.GetAttribute("size").Set(3.0)
    print("  [Client A] Set cube size to 3.0 (in session layer)")

    # Open the stage with Client B's session layer
    stage_b = Usd.Stage.Open(shared_path)
    stage_b.GetSessionLayer().subLayerPaths.append(client_b_layer.identifier)

    # Client B sets size to 7.0 in their session layer
    prim_b = stage_b.OverridePrim("/World/ContestedCube")
    prim_b.GetAttribute("size").Set(7.0)
    print("  [Client B] Set cube size to 7.0 (in session layer)")

    # Each client sees their OWN value (session layer is strongest)
    size_a = stage_a.GetPrimAtPath("/World/ContestedCube").GetAttribute("size").Get()
    size_b = stage_b.GetPrimAtPath("/World/ContestedCube").GetAttribute("size").Get()
    root_size = stage.GetPrimAtPath("/World/ContestedCube").GetAttribute("size").Get()

    print(f"\n  What each client sees:")
    print(f"    Client A sees: size = {size_a} (their session layer wins)")
    print(f"    Client B sees: size = {size_b} (their session layer wins)")
    print(f"    Root layer:     size = {root_size} (unchanged, no publish yet)")

    print("\n  Conflict resolution: Each client's session layer takes precedence locally.")
    print("  When published to root, 'last writer wins' on the Nucleus server.")


# ==============================================================================
# Main Entry Point
# ==============================================================================

def main():
    """Main function that runs all tutorial steps in sequence."""
    print("=" * 80)
    print("Tutorial 08: Omniverse Live Sync - Collaborative Scene Editing Concepts")
    print("=" * 80)

    # Define paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    live_sync_dir = os.path.join(output_dir, "live_sync")
    os.makedirs(live_sync_dir, exist_ok=True)

    # Step 1: Layer composition
    print("\n--- Step 1: Layer Composition ---")
    demonstrate_layer_composition(live_sync_dir)

    # Step 2: Multi-client collaboration
    print("\n--- Step 2: Multi-Client Collaboration ---")
    multi_client_demo(live_sync_dir)

    # Step 3: Change tracking
    print("\n--- Step 3: Change Tracking ---")
    demonstrate_change_tracking(live_sync_dir)

    # Step 4: Conflict resolution
    print("\n--- Step 4: Conflict Resolution ---")
    demonstrate_conflict_resolution(live_sync_dir)

    print("\n" + "=" * 80)
    print("Tutorial 08 complete!")
    print(f"Output files: {live_sync_dir}")
    print("=" * 80)


if __name__ == "__main__":
    main()
