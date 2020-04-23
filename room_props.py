import bpy
import os
from bpy.types import (
        Operator,
        Panel,
        PropertyGroup,
        UIList,
        )
from bpy.props import (
        BoolProperty,
        FloatProperty,
        IntProperty,
        PointerProperty,
        StringProperty,
        CollectionProperty,
        EnumProperty,
        )
from .bp_lib import bp_types, bp_unit, bp_utils, bp_pointer_utils
from . import room_utils
preview_collections = {}
preview_collections["material_categories"] = bp_pointer_utils.create_image_preview_collection()
preview_collections["material_items"] = bp_pointer_utils.create_image_preview_collection()

def enum_material_categories(self,context):
    if context is None:
        return []
    
    icon_dir = room_utils.get_material_path()
    pcoll = preview_collections["material_categories"]
    return bp_pointer_utils.get_folder_enum_previews(icon_dir,pcoll)

def enum_material_names(self,context):
    if context is None:
        return []
    
    icon_dir = os.path.join(room_utils.get_material_path(),self.material_category)
    pcoll = preview_collections["material_items"]
    return bp_pointer_utils.get_image_enum_previews(icon_dir,pcoll)

def update_material_category(self,context):
    if preview_collections["material_items"]:
        bpy.utils.previews.remove(preview_collections["material_items"])
        preview_collections["material_items"] = bp_pointer_utils.create_image_preview_collection()     
        
    enum_material_names(self,context)

class Pointer(PropertyGroup):
    category: bpy.props.StringProperty(name="Category")
    item_name: bpy.props.StringProperty(name="Item Name")


class Room_Scene_Props(PropertyGroup):
    room_tabs: EnumProperty(name="Room Tabs",
                            items=[('ROOM_SIZES',"Room Sizes","Show the Room Sizes"),
                                   ('MATERIALS',"Room Materials","Show the Room Materials"),
                                   ('ROOM_TOOLS',"Room Tools","Show the Room Tools")],
                            default='ROOM_SIZES')

    material_pointers: bpy.props.CollectionProperty(name="Material Pointers",type=Pointer)

    material_category: bpy.props.EnumProperty(name="Material Category",items=enum_material_categories,update=update_material_category)
    material_name: bpy.props.EnumProperty(name="Material Name",items=enum_material_names)

    wall_height: FloatProperty(name="Wall Height",default=bp_unit.inch(96),subtype='DISTANCE')
    wall_thickness: FloatProperty(name="Wall Thickness",default=bp_unit.inch(6),subtype='DISTANCE')

    def draw_room_sizes(self,layout):
        box = layout.box()
        box.label(text="Default Wall Size",icon='MOD_BUILD')

        row = box.row()
        row.label(text="Default Wall Height")
        row.prop(self,'wall_height',text="")

        row = box.row()
        row.label(text="Default Wall Thickness")
        row.prop(self,'wall_thickness',text="")

    def draw_materials(self,layout):
        split = layout.split(factor=.25)
        left_col = split.column()
        right_col = split.column()

        material_box = left_col.box()
        row = material_box.row()
        row.label(text="Material Selections:")

        material_box.prop(self,'material_category',text="",icon='FILE_FOLDER')  
        if len(self.material_name) > 0:
            material_box.template_icon_view(self,"material_name",show_labels=True)  

        right_row = right_col.row()
        right_row.scale_y = 1.3
        right_row.operator('room.update_scene_materials',text="Update Materials",icon='FILE_REFRESH')

        box = right_col.box()
        col = box.column(align=True)
        for mat in self.material_pointers:
            row = col.row()
            row.operator('room.update_material_pointer',text=mat.name,icon='FORWARD').pointer_name = mat.name
            row.label(text=mat.category + " - " + mat.item_name,icon='MATERIAL')

    def draw_room_tools(self,layout):
        box = layout.box()
        box.label(text="General Room Tools",icon='MOD_BUILD')   
        box.operator('room.draw_molding',text="Auto Add Base Molding")
        box.operator('room.draw_molding',text="Auto Add Crown Molding")              
        box.operator('room.draw_floor_plane',text="Add Floor")

        box = layout.box()
        box.label(text="Room Lighting Tools",icon='MOD_BUILD')  
        box.operator('room.add_room_light',text="Add Room Light")

        box = layout.box()
        box.label(text="2D Drawing Tools",icon='MOD_BUILD')  
        box.operator('room.draw_molding',text="Generate 2D View Scenes")      
        box.operator('room.draw_molding',text="Show Dimensions")

    def draw(self,layout):
        col = layout.column(align=True)

        row = col.row(align=True)
        row.scale_y = 1.3        
        row.prop_enum(self, "room_tabs", 'ROOM_SIZES', icon='PROPERTIES', text="Settings") 
        row.prop_enum(self, "room_tabs", 'MATERIALS', icon='COLOR', text="Materials") 
        row.prop_enum(self, "room_tabs", 'ROOM_TOOLS', icon='MODIFIER_ON', text="Tools") 

        box = col.box()

        if self.room_tabs == 'ROOM_SIZES':
            self.draw_room_sizes(box)

        if self.room_tabs == 'MATERIALS':
            self.draw_materials(box)

        if self.room_tabs == 'ROOM_TOOLS':
            self.draw_room_tools(box)

    @classmethod
    def register(cls):
        bpy.types.Scene.room = PointerProperty(
            name="Room Props",
            description="Room Props",
            type=cls,
        )
        
    @classmethod
    def unregister(cls):
        del bpy.types.Scene.room

# def register():
#     bpy.utils.register_class(Room_Scene_Props)

classes = (
    Pointer,
    Room_Scene_Props,
)

register, unregister = bpy.utils.register_classes_factory(classes)        