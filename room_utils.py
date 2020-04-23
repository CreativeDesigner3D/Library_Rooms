import bpy
import os
from .bp_lib import bp_pointer_utils

def get_room_scene_props(context):
    return context.scene.room

def unwrap_obj(context,obj):
    context.view_layer.objects.active = obj
    for mod in obj.modifiers:
        if mod.type == 'HOOK':
            bpy.ops.object.modifier_apply(apply_as='DATA',modifier=mod.name)            

    mode = obj.mode
    if obj.mode == 'OBJECT':
        bpy.ops.object.editmode_toggle()
        
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=66, island_margin=0, user_area_weight=0)
    if mode == 'OBJECT':
        bpy.ops.object.editmode_toggle()

    bpy.ops.bp_assembly.connect_meshes_to_hooks_in_assembly(obj_name = obj.name)

def get_wall_bp(obj):
    if "IS_WALL_BP" in obj:
        return obj
    elif obj.parent:
        return get_wall_bp(obj.parent)

def get_room_bp(obj):
    if "IS_ROOM_BP" in obj:
        return obj
    elif obj.parent:
        return get_room_bp(obj.parent)

def get_material(category,material_name):
    if material_name in bpy.data.materials:
        return bpy.data.materials[material_name]

    material_path = os.path.join(get_material_path(),category,material_name + ".blend")

    if os.path.exists(material_path):

        with bpy.data.libraries.load(material_path, False, False) as (data_from, data_to):
            for mat in data_from.materials:
                if mat == material_name:
                    data_to.materials = [mat]
                    break    
        
        for mat in data_to.materials:
            return mat

def get_default_material_pointers():
    pointers = []
    pointers.append(("Wall Material","Wall Paint","-Textured Paint - Cream"))
    pointers.append(("Door Trim","Plastic","White Melamine"))
    pointers.append(("Door Panels","Plastic","White Melamine"))
    pointers.append(("Window Trim","Plastic","White Melamine"))
    pointers.append(("Window","Plastic","White Melamine"))
    pointers.append(("Pull Finish","Metal","Polished Chrome"))
    pointers.append(("Glass","Misc","Glass"))
    pointers.append(("Base Molding","Plastic","White Melamine"))
    pointers.append(("Crown Molding","Plastic","White Melamine"))
    return pointers

def get_default_handle_pointers():
    pointers = []
    pointers.append(("Door Handles","Decorative Pulls","Americana Handle"))
    pointers.append(("Window Handles","Decorative Pulls","Americana Handle"))
    return pointers

def get_material_pointer_xml_path():
    path = os.path.join(os.path.dirname(__file__),'pointers')
    return os.path.join(path,"material_pointers.xml")

def get_handle_pointer_xml_path():
    path = os.path.join(os.path.dirname(__file__),'pointers')
    return os.path.join(path,"handle_pointers.xml")

def get_material_path():
    return os.path.join(os.path.dirname(__file__),'assets','Materials') 

def write_pointer_files():
    bp_pointer_utils.write_xml_file(get_material_pointer_xml_path(),
                                    get_default_material_pointers())
    # bp_pointer_utils.write_xml_file(get_handle_pointer_xml_path(),
    #                                 get_default_handle_pointers())

def update_pointer_properties():
    props = get_room_scene_props(bpy.context)
    bp_pointer_utils.update_props_from_xml_file(get_material_pointer_xml_path(),
                                                props.material_pointers)
    # bp_pointer_utils.update_props_from_xml_file(get_handle_pointer_xml_path(),
    #                                             props.pull_pointers)