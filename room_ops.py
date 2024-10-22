import bpy
import os
import math
from .bp_lib import bp_types, bp_unit, bp_utils
from . import room_utils
from . import data_walls
from . import data_doors

class ROOM_OT_draw_molding(bpy.types.Operator):
    bl_idname = "room.draw_molding"
    bl_label = "Draw Molding"

    def execute(self, context):
        pass

class ROOM_OT_draw_multiple_walls(bpy.types.Operator):
    bl_idname = "room.draw_multiple_walls"
    bl_label = "Draw Multiple Walls"
    
    filepath: bpy.props.StringProperty(name="Filepath",default="Error")

    obj_bp_name: bpy.props.StringProperty(name="Obj Base Point Name")
    
    drawing_plane = None

    current_wall = None
    previous_wall = None

    starting_point = ()

    assembly = None
    obj = None
    exclude_objects = []

    class_name = ""

    obj_wall_meshes = []

    def reset_properties(self):
        self.drawing_plane = None
        self.current_wall = None
        self.previous_wall = None
        self.starting_point = ()
        self.assembly = None
        self.obj = None
        self.exclude_objects = []
        self.class_name = ""
        self.obj_wall_meshes = []        

    def execute(self, context):
        self.reset_properties()
        self.get_class_name()
        self.create_drawing_plane(context)
        self.create_wall()
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def get_class_name(self):
        name, ext = os.path.splitext(os.path.basename(self.filepath))
        self.class_name = name

    def create_wall(self):
        props = room_utils.get_room_scene_props(bpy.context)
        wall = eval("data_walls." + self.class_name + "()")
        wall.draw_wall()
        wall.set_name("Wall")
        room_utils.assign_wall_pointers(wall)
        if self.current_wall:
            self.previous_wall = self.current_wall
        self.current_wall = wall
        self.current_wall.obj_x.location.x = 0
        self.current_wall.obj_y.location.y = props.wall_thickness
        self.current_wall.obj_z.location.z = props.wall_height
        self.set_child_properties(self.current_wall.obj_bp)

    def connect_walls(self):
        constraint_obj = self.previous_wall.obj_x
        constraint = self.current_wall.obj_bp.constraints.new('COPY_LOCATION')
        constraint.target = constraint_obj
        constraint.use_x = True
        constraint.use_y = True
        constraint.use_z = True

        #I NEED A BETTER WAY TO FIND THE CONSTRAINT OBJ FROM THE BP OBJ
        #THIS IS NEEDED TO SET THE ANGLE OF THE NEXT WALL WHEN ROTATING
        constraint_obj['WALL_CONSTRAINT_OBJ_ID'] = self.current_wall.obj_bp.name

    def set_child_properties(self,obj):
        obj["PROMPT_ID"] = "room.wall_prompts"   
        if obj.type == 'EMPTY':
            obj.hide_viewport = True    
        if obj.type == 'MESH':
            obj.display_type = 'WIRE'            
        if obj.name != self.drawing_plane.name:
            self.exclude_objects.append(obj)    
        for child in obj.children:
            self.set_child_properties(child)

    def set_placed_properties(self,obj):
        if obj.type == 'MESH':
            obj.display_type = 'TEXTURED'   
            self.obj_wall_meshes.append(obj)
        for child in obj.children:
            self.set_placed_properties(child) 

    def create_drawing_plane(self,context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0,0,0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100,100,1)

    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y

        selected_point, selected_obj = bp_utils.get_selection_point(context,event,exclude_objects=self.exclude_objects)

        self.position_object(selected_point,selected_obj)
        self.set_end_angles()            

        if self.event_is_place_first_point(event):
            self.starting_point = (selected_point[0],selected_point[1],selected_point[2])
            return {'RUNNING_MODAL'}
            
        if self.event_is_place_next_point(event):
            self.set_placed_properties(self.current_wall.obj_bp)
            self.create_wall()
            self.connect_walls()
            self.starting_point = (selected_point[0],selected_point[1],selected_point[2])
            return {'RUNNING_MODAL'}

        if self.event_is_cancel_command(event):
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'} 

        return {'RUNNING_MODAL'}

    def event_is_place_next_point(self,event):
        if self.starting_point == ():
            return False
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_place_first_point(self,event):
        if self.starting_point != ():
            return False
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_cancel_command(self,event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return True
        else:
            return False
    
    def event_is_pass_through(self,event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return True
        else:
            return False

    def set_end_angles(self):
        if self.previous_wall and self.current_wall:
            left_angle = self.current_wall.get_prompt("Left Angle")
            prev_right_angle = self.previous_wall.get_prompt("Right Angle") 

            prev_rot = self.previous_wall.obj_bp.rotation_euler.z  
            rot = self.current_wall.obj_bp.rotation_euler.z

            current_rot = round(math.degrees(rot),0)
            previous_rot = round(math.degrees(prev_rot),0)
            diff = int(math.fabs(current_rot-previous_rot))

            if diff == 0 or diff == 180:
                left_angle.set_value(0)
                prev_right_angle.set_value(0)
            else:
                left_angle.set_value((rot-prev_rot)/2)
                prev_right_angle.set_value((prev_rot-rot)/2)

            self.current_wall.obj_prompts.location = self.current_wall.obj_prompts.location
            self.previous_wall.obj_prompts.location = self.previous_wall.obj_prompts.location            
        
    def position_object(self,selected_point,selected_obj):
        if self.starting_point == ():
            self.current_wall.obj_bp.location = selected_point
        else:
            x = selected_point[0] - self.starting_point[0]
            y = selected_point[1] - self.starting_point[1]
            parent_rot = self.current_wall.obj_bp.parent.rotation_euler.z if self.current_wall.obj_bp.parent else 0
            if math.fabs(x) > math.fabs(y):
                if x > 0:
                    self.current_wall.obj_bp.rotation_euler.z = math.radians(0) + parent_rot
                else:
                    self.current_wall.obj_bp.rotation_euler.z = math.radians(180) + parent_rot
                self.current_wall.obj_x.location.x = math.fabs(x)
                
            if math.fabs(y) > math.fabs(x):
                if y > 0:
                    self.current_wall.obj_bp.rotation_euler.z = math.radians(90) + parent_rot
                else:
                    self.current_wall.obj_bp.rotation_euler.z = math.radians(-90) + parent_rot
                self.current_wall.obj_x.location.x = math.fabs(y)

    def cancel_drop(self,context):
        if self.previous_wall:
            prev_right_angle = self.previous_wall.get_prompt("Right Angle") 
            prev_right_angle.set_value(0)

        for obj in self.obj_wall_meshes:
            room_utils.unwrap_obj(context,obj)

        obj_list = []
        obj_list.append(self.drawing_plane)
        obj_list.append(self.current_wall.obj_bp)
        for child in self.current_wall.obj_bp.children:
            obj_list.append(child)
        bp_utils.delete_obj_list(obj_list)
        return {'CANCELLED'}


class ROOM_OT_place_square_room(bpy.types.Operator):
    bl_idname = "room.place_square_room"
    bl_label = "Place Square Room"
    
    filepath: bpy.props.StringProperty(name="Filepath",default="Error")

    obj_bp_name: bpy.props.StringProperty(name="Obj Base Point Name")
    
    drawing_plane = None
    assembly = None
    obj = None
    exclude_objects = []

    starting_point = ()

    def execute(self, context):
        self.starting_point = ()
        self.create_drawing_plane(context)
        self.obj = self.get_object(context)
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def set_child_properties(self,obj):
        obj["PROMPT_ID"] = "room.room_prompts"   
        if obj.type == 'EMPTY':
            obj.hide_viewport = True    
        if obj.name != self.drawing_plane.name:
            self.exclude_objects.append(obj)    
        for child in obj.children:
            self.set_child_properties(child)

    def get_object(self,context):
        self.exclude_objects = []
        obj = bpy.data.objects[self.obj_bp_name]
        room_bp = room_utils.get_room_bp(obj)
        self.assembly = bp_types.Assembly(room_bp)
        self.assembly.obj_x.location.x = 1
        self.assembly.obj_y.location.y = 1
        self.set_child_properties(self.assembly.obj_bp)
        return self.assembly.obj_bp

    def create_drawing_plane(self,context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0,0,0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100,100,1)

    def position_object(self,selected_point,selected_obj):
        if self.starting_point == ():
            self.assembly.obj_bp.location = selected_point
        else:
            x = selected_point[0] - self.starting_point[0]
            y = selected_point[1] - self.starting_point[1]

            self.assembly.obj_x.location.x = math.fabs(x)
            self.assembly.obj_y.location.y = math.fabs(y)

    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y

        selected_point, selected_obj = bp_utils.get_selection_point(context,event,exclude_objects=self.exclude_objects)

        self.position_object(selected_point,selected_obj)

        if self.event_is_place_object(event):
            if self.starting_point == ():
                self.starting_point = (selected_point[0],selected_point[1],selected_point[2])
            else:
                return self.finish(context)

        if self.event_is_cancel_command(event):
            return self.cancel_drop(context)
        
        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'}        
        
        return {'RUNNING_MODAL'}

    def event_is_place_object(self,event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_cancel_command(self,event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return True
        else:
            return False
    
    def event_is_pass_through(self,event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return True
        else:
            return False

    def cancel_drop(self,context):
        obj_list = []
        obj_list.append(self.drawing_plane)
        obj_list.append(self.obj)
        bp_utils.delete_obj_list(obj_list)
        return {'CANCELLED'}
    
    def set_prompt_id(self):
        for child in self.assembly.obj_bp.children:
            child["PROMPT_ID"] = "room.room_prompts"

    def finish(self,context):
        context.window.cursor_set('DEFAULT')
        if self.drawing_plane:
            bp_utils.delete_obj_list([self.drawing_plane])
        bpy.ops.object.select_all(action='DESELECT')
        self.obj.select_set(True)  
        context.view_layer.objects.active = self.obj 
        context.area.tag_redraw()
        return {'FINISHED'}


class ROOM_OT_place_door(bpy.types.Operator):
    bl_idname = "room.place_door"
    bl_label = "Place Door"
    
    filepath: bpy.props.StringProperty(name="Filepath",default="Error")

    obj_bp_name: bpy.props.StringProperty(name="Obj Base Point Name")
    
    drawing_plane = None

    door = None
    obj = None
    exclude_objects = []

    class_name = ""

    def execute(self, context):
        self.get_class_name()
        self.create_drawing_plane(context)
        self.create_door()
        context.window_manager.modal_handler_add(self)
        context.area.tag_redraw()
        return {'RUNNING_MODAL'}

    def get_class_name(self):
        name, ext = os.path.splitext(os.path.basename(self.filepath))
        self.class_name = name

    def create_door(self):
        props = room_utils.get_room_scene_props(bpy.context)
        self.door = eval("data_doors." + self.class_name + "()")
        self.door.draw_door()
        self.set_child_properties(self.door.obj_bp)

    def set_child_properties(self,obj):
        obj["PROMPT_ID"] = "room.wall_prompts"   
        if obj.type == 'EMPTY':
            obj.hide_viewport = True    
        if obj.type == 'MESH':
            obj.display_type = 'WIRE'            
        if obj.name != self.drawing_plane.name:
            self.exclude_objects.append(obj)    
        for child in obj.children:
            self.set_child_properties(child)

    def set_placed_properties(self,obj):
        if obj.type == 'MESH':
            if 'IS_BOOLEAN' in obj:
                obj.display_type = 'WIRE' 
                obj.hide_viewport = True
            else:
                obj.display_type = 'TEXTURED'  

        for child in obj.children:
            self.set_placed_properties(child) 

    def create_drawing_plane(self,context):
        bpy.ops.mesh.primitive_plane_add()
        plane = context.active_object
        plane.location = (0,0,0)
        self.drawing_plane = context.active_object
        self.drawing_plane.display_type = 'WIRE'
        self.drawing_plane.dimensions = (100,100,1)

    def get_boolean_obj(self,obj):
        #TODO FIGURE OUT HOW TO DO RECURSIVE SEARCHING 
        #ONLY SERACHES THREE LEVELS DEEP :(
        if 'IS_BOOLEAN' in obj:
            return obj
        for child in obj.children:
            if 'IS_BOOLEAN' in child:
                return child
            for nchild in child.children:
                if 'IS_BOOLEAN' in nchild:
                    return nchild

    def add_boolean_modifier(self,wall_mesh):
        obj_bool = self.get_boolean_obj(self.door.obj_bp)
        if wall_mesh and obj_bool:
            mod = wall_mesh.modifiers.new(obj_bool.name,'BOOLEAN')
            mod.object = obj_bool
            mod.operation = 'DIFFERENCE'

    def parent_door_to_wall(self,obj_wall_bp):
        x_loc = bp_utils.calc_distance((self.door.obj_bp.location.x,self.door.obj_bp.location.y,0),
                                       (obj_wall_bp.matrix_local[0][3],obj_wall_bp.matrix_local[1][3],0))
        self.door.obj_bp.location = (0,0,0)
        self.door.obj_bp.rotation_euler = (0,0,0)
        self.door.obj_bp.parent = obj_wall_bp
        self.door.obj_bp.location.x = x_loc        

    def modal(self, context, event):
        context.area.tag_redraw()
        self.mouse_x = event.mouse_x
        self.mouse_y = event.mouse_y

        selected_point, selected_obj = bp_utils.get_selection_point(context,event,exclude_objects=self.exclude_objects)

        self.position_object(selected_point,selected_obj)

        if self.event_is_place_first_point(event):
            self.add_boolean_modifier(selected_obj)
            self.set_placed_properties(self.door.obj_bp)
            if selected_obj.parent:
                self.parent_door_to_wall(selected_obj.parent)
            self.create_door()
            return {'RUNNING_MODAL'}

        if self.event_is_cancel_command(event):
            return self.cancel_drop(context)

        if self.event_is_pass_through(event):
            return {'PASS_THROUGH'} 

        return {'RUNNING_MODAL'}

    def event_is_place_next_point(self,event):
        if self.starting_point == ():
            return False
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_place_first_point(self,event):
        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            return True
        elif event.type == 'NUMPAD_ENTER' and event.value == 'PRESS':
            return True
        elif event.type == 'RET' and event.value == 'PRESS':
            return True
        else:
            return False

    def event_is_cancel_command(self,event):
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            return True
        else:
            return False
    
    def event_is_pass_through(self,event):
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return True
        else:
            return False      
            
    def position_object(self,selected_point,selected_obj):
        if selected_obj:
            wall_bp = selected_obj.parent
            if self.door.obj_bp and wall_bp:
                self.door.obj_bp.rotation_euler.z = wall_bp.rotation_euler.z
                self.door.obj_bp.location.x = selected_point[0]
                self.door.obj_bp.location.y = selected_point[1]
                self.door.obj_bp.location.z = 0

    def cancel_drop(self,context):
        bp_utils.delete_object_and_children(self.door.obj_bp)
        bp_utils.delete_object_and_children(self.drawing_plane)
        return {'CANCELLED'}

    def finish(self,context):
        context.window.cursor_set('DEFAULT')
        if self.drawing_plane:
            bp_utils.delete_obj_list([self.drawing_plane])
        bpy.ops.object.select_all(action='DESELECT')
        context.area.tag_redraw()
        return {'FINISHED'}


class ROOM_OT_draw_floor_plane(bpy.types.Operator):
    bl_idname = "room.draw_floor_plane"
    bl_label = "Draw Floor Plane"
    bl_options = {'UNDO'}
    
    def create_floor_mesh(self,name,size):
        
        verts = [(0.0, 0.0, 0.0),
                (0.0, size[1], 0.0),
                (size[0], size[1], 0.0),
                (size[0], 0.0, 0.0),
                ]

        faces = [(0, 1, 2, 3),
                ]

        return bp_utils.create_object_from_verts_and_faces(verts,faces,name)

    def execute(self, context):
        largest_x = 0
        largest_y = 0
        smallest_x = 0
        smallest_y = 0
        overhang = bp_unit.inch(6)
        wall_assemblies = []
        wall_bps = []
        for obj in context.visible_objects:
            if obj.parent and 'IS_WALL_BP' in obj.parent and obj.parent not in wall_bps:
                wall_bps.append(obj.parent)
                wall_assemblies.append(bp_types.Assembly(obj.parent))
            
        for assembly in wall_assemblies:
            start_point = (assembly.obj_bp.matrix_world[0][3],assembly.obj_bp.matrix_world[1][3],0)
            end_point = (assembly.obj_x.matrix_world[0][3],assembly.obj_x.matrix_world[1][3],0)

            if start_point[0] > largest_x:
                largest_x = start_point[0]
            if start_point[1] > largest_y:
                largest_y = start_point[1]
            if start_point[0] < smallest_x:
                smallest_x = start_point[0]
            if start_point[1] < smallest_y:
                smallest_y = start_point[1]
            if end_point[0] > largest_x:
                largest_x = end_point[0]
            if end_point[1] > largest_y:
                largest_y = end_point[1]
            if end_point[0] < smallest_x:
                smallest_x = end_point[0]
            if end_point[1] < smallest_y:
                smallest_y = end_point[1]

        loc = (smallest_x - overhang, smallest_y - overhang,0)
        width = math.fabs(smallest_y) + math.fabs(largest_y) + (overhang*2)
        length = math.fabs(largest_x) + math.fabs(smallest_x) + (overhang*2)
        if width == 0:
            width = bp_unit.inch(-48)
        if length == 0:
            length = bp_unit.inch(-48)
        obj_plane = self.create_floor_mesh('Floor',(length,width,0.0))
        context.view_layer.active_layer_collection.collection.objects.link(obj_plane)
        obj_plane.location = loc
        room_utils.unwrap_obj(context,obj_plane)
        room_utils.assign_floor_pointers(obj_plane)
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.flip_normals()
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.select_all(action='DESELECT')

        #SET CONTEXT
        context.view_layer.objects.active = obj_plane
        
        return {'FINISHED'}


class ROOM_OT_add_room_light(bpy.types.Operator):
    bl_idname = "room.add_room_light"
    bl_label = "Add Room Light"
    bl_options = {'UNDO'}
    
    def execute(self, context):
        largest_x = 0
        largest_y = 0
        smallest_x = 0
        smallest_y = 0
        wall_groups = []
        height = 0
        # for obj in context.visible_objects:
        #     if obj.mv.type == 'BPWALL':
        #         wall_groups.append(fd_types.Wall(obj))
            
        wall_assemblies = []
        wall_bps = []
        for obj in context.visible_objects:
            if obj.parent and 'IS_WALL_BP' in obj.parent and obj.parent not in wall_bps:
                wall_bps.append(obj.parent)
                wall_assemblies.append(bp_types.Assembly(obj.parent))

        for assembly in wall_assemblies:
            start_point = (assembly.obj_bp.matrix_world[0][3],assembly.obj_bp.matrix_world[1][3],0)
            end_point = (assembly.obj_x.matrix_world[0][3],assembly.obj_x.matrix_world[1][3],0)
            height = assembly.obj_z.location.z
            
            if start_point[0] > largest_x:
                largest_x = start_point[0]
            if start_point[1] > largest_y:
                largest_y = start_point[1]
            if start_point[0] < smallest_x:
                smallest_x = start_point[0]
            if start_point[1] < smallest_y:
                smallest_y = start_point[1]
            if end_point[0] > largest_x:
                largest_x = end_point[0]
            if end_point[1] > largest_y:
                largest_y = end_point[1]
            if end_point[0] < smallest_x:
                smallest_x = end_point[0]
            if end_point[1] < smallest_y:
                smallest_y = end_point[1]

        x = (math.fabs(largest_x) - math.fabs(smallest_x))/2
        y = (math.fabs(largest_y) - math.fabs(smallest_y))/2
        z = height - bp_unit.inch(.01)
        
        width = math.fabs(smallest_y) + math.fabs(largest_y)
        length = math.fabs(largest_x) + math.fabs(smallest_x)
        if width == 0:
            width = bp_unit.inch(-48)
        if length == 0:
            length = bp_unit.inch(-48)

        bpy.ops.object.light_add(type = 'AREA')
        obj_lamp = context.active_object
        obj_lamp.location.x = x
        obj_lamp.location.y = y
        obj_lamp.location.z = z
        obj_lamp.data.shape = 'RECTANGLE'
        obj_lamp.data.size = length + bp_unit.inch(20)
        obj_lamp.data.size_y = math.fabs(width) + bp_unit.inch(20)
        obj_lamp.data.energy = max(bp_unit.meter_to_active_unit(largest_x),bp_unit.meter_to_active_unit(largest_y))/4
        return {'FINISHED'}


class ROOM_OT_update_scene_materials(bpy.types.Operator):
    bl_idname = "room.update_scene_materials"
    bl_label = "Update Scene Materials"
    bl_options = {'UNDO'}

    def execute(self, context):

        return {'FINISHED'}


class ROOM_OT_update_material_pointer(bpy.types.Operator):
    bl_idname = "room.update_material_pointer"
    bl_label = "Update Material Pointer"
    bl_options = {'UNDO'}

    pointer_name: bpy.props.StringProperty(name="Pointer Name",default="")

    def execute(self, context):

        return {'FINISHED'}

classes = (
    ROOM_OT_draw_molding,
    ROOM_OT_draw_multiple_walls,
    ROOM_OT_place_square_room,
    ROOM_OT_place_door,
    ROOM_OT_draw_floor_plane,
    ROOM_OT_add_room_light,
    ROOM_OT_update_scene_materials,
    ROOM_OT_update_material_pointer
)

register, unregister = bpy.utils.register_classes_factory(classes)      
