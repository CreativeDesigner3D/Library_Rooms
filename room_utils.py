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
    pointers.append(("Walls","Wall Paint","-Textured Paint - Cream"))
    pointers.append(("Floor","Wood Flooring","Natural Anagre Hardwood"))
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

def assign_wall_pointers(assembly):
    for child in assembly.obj_bp.children:
        if child.type == 'MESH':
            if len(child.material_slots) == 0:
                bpy.ops.bp_material.add_material_slot(object_name=child.name)
            for index, pointer in enumerate(child.material_pointer.slots):  
                pointer.name = "Walls"  
            assign_materials_to_object(child)

def assign_floor_pointers(obj):
    if len(obj.material_slots) == 0:
        bpy.ops.bp_material.add_material_slot(object_name=obj.name)
    for index, pointer in enumerate(obj.material_pointer.slots):  
        pointer.name = "Floor"  
    assign_materials_to_object(obj)

def assign_materials_to_object(obj):
    props = get_room_scene_props(bpy.context)
    for index, pointer in enumerate(obj.material_pointer.slots):
        if index <= len(obj.material_slots) and pointer.name in props.material_pointers:
            p = props.material_pointers[pointer.name]
            slot = obj.material_slots[index]
            slot.material = get_material(p.category,p.item_name)                

