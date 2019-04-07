import bpy, itertools
import numpy as np

#----
def run(sheet_name, sheet_size_x, sheet_size_y):

    print("SPRITE_BAKE\n")
    sprite_bake.node_setup()
    image = create_sheet(sheet_size_x, sheet_size_y, sheet_name)

    image.filepath_raw = bpy.context.scene.render.filepath+sheet_name+".png"
    image.file_format = 'PNG'
    image.save()

    print("Done!\n")
    
#----
def node_setup():
    bpy.context.scene.use_nodes = True
    tree = bpy.context.scene.node_tree
    
    if "Viewer" not in tree.nodes:
        viewer = tree.nodes.new('CompositorNodeViewer')   
        viewer.location = 750,210
        viewer.use_alpha = True
        
    if "Render Layers" not in tree.nodes:
        rlayers = tree.nodes.new('CompositorNodeRLayers') 
        rlayers.location = 185,285
        
    if "Composite" not in tree.nodes:
        composite = tree.nodes.new("CompositorNodeComposite")
        composite.location = 750,360
        
    viewer = tree.nodes["Viewer"]
    rlayers = tree.nodes["Render Layers"]
    composite = tree.nodes["Composite"]
    
    tree.links.new(rlayers.outputs[0], viewer.inputs[0])
    tree.links.new(rlayers.outputs[0], composite.inputs[0])
    
#----
def create_sheet(tiles_x, tiles_y, sheet_name="baked_sprite_sheet"):

    frame_start, frame_end = bpy.context.scene.frame_start, bpy.context.scene.frame_end
    anim_length = abs(frame_start-frame_end)+1
    
    bpy.context.scene.frame_set(frame_start)
    bpy.ops.render.render()
    
    #----
    source = bpy.data.images["Viewer Node"]
    source_x, source_y = int(bpy.context.scene.render.resolution_x), int(bpy.context.scene.render.resolution_y)

    size = source_x*tiles_x, source_y*tiles_y
    
    #----
    if sheet_name in bpy.data.images:
        bpy.data.images.remove(bpy.data.images[sheet_name])
        
    sheet = bpy.data.images.new(sheet_name, alpha=True, width=size[0], height=size[1])
    sheet_x, sheet_y = size

    sheet_mat = np.ndarray((sheet_y,sheet_x,4), buffer=np.array(sheet.pixels))
    source_mat = np.ndarray((source_y,source_x,4), buffer=np.array(source.pixels))
    
    #----
    frame_dict = {}
    i = 0
    
    print("Rendering... ")
    
    for current_y_tile in range(1, tiles_y+1):

        for current_x_tile in range(0, tiles_x):
            
            pos_x = (source_x*current_x_tile)
            pos_y = sheet_y-(source_y*current_y_tile)
            
            frame_dict[i] = [current_x_tile, current_y_tile-1]
            i += 1
            
            print("Tile %d of %d"%(i,tiles_x*tiles_y))
            
            sheet_mat[pos_y:pos_y+source_y, pos_x:pos_x+source_x] = source_mat
            
            if bpy.context.scene.frame_current == frame_end: break
            
            #----
            bpy.context.scene.frame_set(bpy.context.scene.frame_current+1)
            bpy.ops.render.render()
            
            source_mat = np.ndarray((source_y,source_x,4), buffer=np.array(source.pixels))
            
    #----
    print("Drawing sheet")
    final_mat = list(itertools.chain.from_iterable(sheet_mat.tolist()))
    final_mat = list(itertools.chain.from_iterable(final_mat))

    sheet.pixels = final_mat
    bpy.context.scene.frame_set(frame_start)
    
    create_sprite(sheet_name, tiles_x, tiles_y, frame_dict)
    return bpy.data.images[sheet_name]

#---
def create_sprite(sheet_name, tiles_x, tiles_y, frame_dict):
    
    purge_ID(sheet_name)
    texture = bpy.data.textures.new(sheet_name, "IMAGE")
    texture.image = bpy.data.images[sheet_name]
    
    anim_id = str(tiles_x)+"x"+str(tiles_y)+"_sprite_sheet"
    
    #---
    if anim_id not in bpy.data.meshes:
        
        print("Creating a new mesh")
        for key, value in frame_dict.items():
            x, y = value
            bpy.ops.mesh.primitive_plane_add(enter_editmode=True)
            bpy.data.screens['UV Editing'].areas[1].spaces[0].image = texture.image
            bpy.ops.uv.unwrap()
            
        #----    
        bpy.data.screens['UV Editing'].areas[1].spaces[0].image = texture.image    
        bpy.ops.object.mode_set(mode="OBJECT")
        
        bpy.context.selected_objects[0].name = bpy.context.selected_objects[0].data.name = anim_id
        bpy.context.selected_objects[0].data.use_fake_user = True
        
        new_size = bpy.context.selected_objects[0]
        
        #---
        uv_layer = new_size.data.uv_layers.active.data
        i = 0
        
        for poly in new_size.data.polygons:
            
            group = new_size.vertex_groups.new(name="frame_"+str(i))
            x,y = frame_dict[i]
            verts = []
            
            #---
            for loop_index in range(poly.loop_start, poly.loop_start + poly.loop_total):
                
                vertex_index = new_size.data.loops[loop_index].vertex_index
                verts.append(vertex_index)
                
                if tiles_x > 1 and tiles_y > 1:
                    
                    divid = min(tiles_x, tiles_y)
                    
                    uv_layer[loop_index].uv[0] = uv_layer[loop_index].uv[0]/divid
                    uv_layer[loop_index].uv[1] = uv_layer[loop_index].uv[1]/divid
                
                uv_layer[loop_index].uv[0] += x/tiles_x
                uv_layer[loop_index].uv[1] += (tiles_y-(1+y))/tiles_y
            
            group.add(verts, 1.0, 'ADD')
            i += 1
        
        #---
        animate_sprite(bpy.context.selected_objects[0], tiles_x, tiles_y, anim_id)
        
        new_size.layers[19] = True
        new_size.layers[0:19] = [False for i in range(0,19)]
        
    #---
    print("Setting up sprite ")
    template = bpy.context.scene.objects.get(anim_id)
    new_sprite = template.copy()
    new_sprite.data = template.data.copy()
    bpy.context.scene.objects.link(new_sprite)
    
    for obj in bpy.context.selected_objects: obj.select = False
    new_sprite.select = True
    new_sprite.data.name = new_sprite.name = sheet_name
    
    clean_dupli_anim(new_sprite, anim_id, tiles_x*tiles_y)
    if new_sprite.data.shape_keys.animation_data == None:
        anim_data = new_sprite.data.shape_keys.animation_data_create()
        anim_data.action = bpy.data.actions[str(tiles_x*tiles_y)+"_frame_sprite"]
    
    new_sprite.layers[1] = True
    new_sprite.layers[0] = False
    
    #---- 
    material = bpy.data.materials.new(name=sheet_name)
    new_sprite.data.materials.append(material)
    
    slot = material.texture_slots.add()
    slot.texture = texture
    slot.use_map_alpha = True
    
    material.use_transparency = True
    material.use_shadeless = True
    material.alpha = 0.0
        
#---
def clean_dupli_anim(obj_list, anim_id, frames):
    
    sprite_anim = str(frames)+"_frame_sprite"
    
    actions = [act for act in bpy.data.actions if sprite_anim in act.name and "." in act.name]
    
    for act in actions:
        act.user_remap(bpy.data.actions[sprite_anim])
        bpy.data.actions.remove(act)
        
    sk = [key for key in bpy.data.shape_keys if anim_id in key.name and "." in key.name]
    
    for key in sk:
        key.user_remap(bpy.data.shape_keys[anim_id])
        
#---
def animate_sprite(obj, tiles_x, tiles_y, anim_id):
    
    frames = tiles_x*tiles_y
    sk_basis = obj.shape_key_add('Basis')
    obj.data.shape_keys.use_relative = True
    
    mesh_verts = obj.data.vertices
    
    #---
    for n in range(0, frames):

        sk = obj.shape_key_add('frame_'+str(n))        
        shape_verts = [v.index for v in mesh_verts if n not in [vg.group for vg in v.groups]]

        for index in shape_verts:
            sk.data[index].co = [0,0,0]
            
    this_key = list(bpy.data.shape_keys.keys())[-1]
    bpy.data.shape_keys[this_key].name = anim_id
    
    #---
    if str(frames)+"_frame_sprite" not in bpy.data.actions:
    
        for n in range(0, frames):
            curr_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(n))]
            
            if n == 0:
                next_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(n+1))]
                prev_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(frames-1))]
            
            elif n == frames-1:
                next_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(0))]
                prev_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(n-1))]
                
            else:
                next_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(n+1))]
                prev_block = obj.data.shape_keys.key_blocks['frame_%s'%(str(n-1))]
                
            #---
            curr_block.value = 1
            next_block.value = prev_block.value = 0
            
            curr_block.keyframe_insert("value",frame=n)
            next_block.keyframe_insert("value",frame=n)
            prev_block.keyframe_insert("value",frame=n)
            
        #---
        fcurves = bpy.data.actions[anim_id+"Action"].fcurves
        for fcurve in fcurves:
            for kf in fcurve.keyframe_points:
                kf.interpolation = 'CONSTANT'
                
        bpy.data.actions[anim_id+"Action"].name = str(frames)+"_frame_sprite"

#---
def purge_ID(name):
    if name in bpy.data.objects:
        object = bpy.data.objects[name]
        bpy.data.objects.remove(object)
        
    if name in bpy.data.materials:
        material = bpy.data.materials[name]
        bpy.data.materials.remove(material)
        
    if name in bpy.data.meshes:
        mesh = bpy.data.meshes[name]
        bpy.data.meshes.remove(mesh)
        
    if name in bpy.data.textures:
        texture = bpy.data.textures[name]
        bpy.data.textures.remove(texture)
        
#---
