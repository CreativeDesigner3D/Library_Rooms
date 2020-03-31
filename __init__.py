import bpy
import os
import inspect
from .bp_lib import bp_utils
from . import room_props
from . import data_doors
from . import data_parts
from . import data_walls
from . import data_windows
from . import room_ops
from . import room_ui

bl_info = {
    "name": "Room Library",
    "author": "Andrew Peel",
    "version": (0, 0, 1),
    "blender": (2, 80, 0),
    "location": "Asset Library",
    "description": "Library that adds the ability to create rooms",
    "warning": "",
    "wiki_url": "",
    "category": "Asset Library",
}

LIBRARY_PATH = os.path.join(os.path.dirname(__file__),"library")
PANEL_ID = 'ROOM_PT_library_settings'

def register():
    lib = bpy.context.window_manager.bp_lib.script_libraries.add()
    lib.name = "Room Library"
    lib.library_path = LIBRARY_PATH
    lib.panel_id = PANEL_ID

    bp_utils.load_library_items_from_module(lib,data_walls)
    bp_utils.load_library_items_from_module(lib,data_parts)
    bp_utils.load_library_items_from_module(lib,data_doors)
    bp_utils.load_library_items_from_module(lib,data_windows)

def unregister():
    for i, lib in enumerate(bpy.context.window_manager.bp_lib.script_libraries):
        if lib.name == "Room Library":
            bpy.context.window_manager.bp_lib.script_libraries.remove(i)

