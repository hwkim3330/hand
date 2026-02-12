"""Export hand as SKINNED mesh from original blend file.
   Keep full armature. Minimal changes: remove duplicate mesh, add materials.
   Let JS handle the positioning offset.
"""
import bpy, os

arm_obj = bpy.data.objects.get('Armature')
mesh1 = bpy.data.objects.get('Cube.000')
mesh2 = bpy.data.objects.get('Cube.005')

# Print key info for JS code
bpy.context.view_layer.update()
hand_bone = arm_obj.data.bones.get('hand.L')
hand_world = arm_obj.matrix_world @ hand_bone.head_local
mcp_bone = arm_obj.data.bones.get('finger_middle.01.L')
mcp_world = arm_obj.matrix_world @ mcp_bone.head_local
mesh_mw = mesh1.matrix_world
print(f'hand.L world: {hand_world[:]}')
print(f'MCP world: {mcp_world[:]}')
print(f'Mesh matrix_world: {[list(row) for row in mesh_mw]}')

# Wrist-to-MCP in model space
hand_size = (hand_world - mcp_world).length
print(f'Wrist-to-MCP distance: {hand_size:.4f}')

# Delete duplicate mesh & lights
if mesh2:
    bpy.data.objects.remove(mesh2, do_unlink=True)
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

# Setup material with textures
tex_dir = '/home/kim/hand-tracking/blend_src/textures/'
mat = bpy.data.materials.new(name='HandSkin')
mat.use_nodes = True
tree = mat.node_tree
bsdf = tree.nodes.get('Principled BSDF')

color_path = os.path.join(tex_dir, 'HAND_C.jpg')
if os.path.exists(color_path):
    tex_c = tree.nodes.new('ShaderNodeTexImage')
    tex_c.image = bpy.data.images.load(color_path)
    tree.links.new(tex_c.outputs['Color'], bsdf.inputs['Base Color'])

normal_path = os.path.join(tex_dir, 'HAND_N .jpg')
if os.path.exists(normal_path):
    nmap = tree.nodes.new('ShaderNodeNormalMap')
    tex_n = tree.nodes.new('ShaderNodeTexImage')
    tex_n.image = bpy.data.images.load(normal_path)
    tex_n.image.colorspace_settings.name = 'Non-Color'
    tree.links.new(tex_n.outputs['Color'], nmap.inputs['Color'])
    tree.links.new(nmap.outputs['Normal'], bsdf.inputs['Normal'])

mesh1.data.materials.clear()
mesh1.data.materials.append(mat)

# Export with skinning
out = '/home/kim/hand-tracking/models/hand.glb'
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format='GLB',
    export_skins=True,
    export_animations=False,
    export_apply=False,
    use_selection=False,
)
size = os.path.getsize(out)
print(f'EXPORT: {out} ({size} bytes)')
