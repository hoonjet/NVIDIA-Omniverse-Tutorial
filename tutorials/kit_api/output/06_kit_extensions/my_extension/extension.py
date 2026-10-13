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
