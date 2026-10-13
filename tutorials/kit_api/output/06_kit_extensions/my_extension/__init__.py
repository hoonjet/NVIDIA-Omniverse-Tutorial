# Extension package init
# This file makes the directory a Python package.
# Kit imports this package and calls extension.on_startup/on_shutdown.

from .extension import on_startup, on_shutdown, get_extension_state
