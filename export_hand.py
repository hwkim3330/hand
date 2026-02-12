"""Blender script: Export hand-only skinned GLB.
   - Apply mesh X-mirror transform to vertex data
   - Remove arm bones, keep hand.L + descendants (25 bones)
   - Transfer forearm weights to hand.L
   - Translate BOTH bones AND vertices so hand.L = origin
   - Materials + textures
   - Export GLB
"""
import bpy, os
from mathutils import Matrix

arm_obj = bpy.data.objects.get('Armature')
mesh1 = bpy.data.objects.get('Cube.000')
mesh2 = bpy.data.objects.get('Cube.005')

if not arm_obj:
    print('ERROR: No Armature'); raise SystemExit(1)

# ── 0. Remove duplicate mesh first ──
if mesh2:
    bpy.data.objects.remove(mesh2, do_unlink=True)
    print('Removed duplicate mesh')

# ── 1. Apply mesh object transform (bakes X-mirror into vertices) ──
bpy.ops.object.select_all(action='DESELECT')
mesh1.select_set(True)
bpy.context.view_layer.objects.active = mesh1
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.context.view_layer.update()
print(f'Mesh transform applied. matrix_world now: {[list(row) for row in mesh1.matrix_world]}')

# ── 2. Get hand.L position (now mesh local = armature local) ──
hand_bone = arm_obj.data.bones.get('hand.L')
offset = hand_bone.head_local.copy()  # in armature local space
print(f'hand.L head_local (= mesh local): {offset[:]}')

# Sample vertex near hand to verify
v_sample = mesh1.data.vertices[0]
print(f'Vertex[0] after apply: {v_sample.co[:]}')

# ── 3. Transfer forearm.L weights → hand.L ──
forearm_vg = mesh1.vertex_groups.get('forearm.L')
hand_vg = mesh1.vertex_groups.get('hand.L')
if forearm_vg and hand_vg:
    for v in mesh1.data.vertices:
        fw = 0
        for g in v.groups:
            if g.group == forearm_vg.index:
                fw = g.weight; break
        if fw > 0:
            try: hw = hand_vg.weight(v.index)
            except RuntimeError: hw = 0
            hand_vg.add([v.index], min(hw + fw, 1.0), 'REPLACE')
    mesh1.vertex_groups.remove(forearm_vg)
    print('Transferred forearm.L → hand.L')

# Remove unused vertex groups
removable = [vg for vg in mesh1.vertex_groups
             if '.R' in vg.name or vg.name in [
                 'ribs.001', 'shoulder.L', 'upper_arm.L',
                 'forearm.L', 'forearm.L.003',
                 'shoulder.R', 'upper_arm.R', 'forearm.R', 'forearm.R.003']]
for vg in removable:
    mesh1.vertex_groups.remove(vg)
print(f'Vertex groups: {[vg.name for vg in mesh1.vertex_groups]}')

# ── 4. Edit armature: keep only hand.L subtree ──
bpy.ops.object.select_all(action='DESELECT')
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

hand_l = arm_obj.data.edit_bones.get('hand.L')
if not hand_l:
    print('ERROR: No hand.L bone!'); raise SystemExit(1)

keep = set()
def collect(bone):
    keep.add(bone.name)
    for c in bone.children: collect(c)
collect(hand_l)
print(f'Keeping {len(keep)} bones')

# Delete non-hand bones
to_delete = [b.name for b in arm_obj.data.edit_bones if b.name not in keep]
for bname in to_delete:
    b = arm_obj.data.edit_bones.get(bname)
    if b: arm_obj.data.edit_bones.remove(b)

# Make hand.L root
hand_l = arm_obj.data.edit_bones.get('hand.L')
hand_l.parent = None

# Mirror bone X positions to match applied mesh X-mirror, then translate to origin
for bone in arm_obj.data.edit_bones:
    bone.head.x = -bone.head.x
    bone.tail.x = -bone.tail.x

# Recompute offset after X-mirror
offset = hand_l.head.copy()
print(f'hand.L after X-mirror: {offset[:]}')

for bone in arm_obj.data.edit_bones:
    bone.head -= offset
    bone.tail -= offset
print(f'hand.L head after translate: {hand_l.head[:]}')

bpy.ops.object.mode_set(mode='OBJECT')

# Reset armature transform
arm_obj.location = (0, 0, 0)
arm_obj.rotation_euler = (0, 0, 0)
arm_obj.scale = (1, 1, 1)

# ── 5. Translate mesh vertices by same offset ──
mesh1.data.transform(Matrix.Translation(-offset))
mesh1.data.update()
bpy.context.view_layer.update()

xs = [v.co.x for v in mesh1.data.vertices]
ys = [v.co.y for v in mesh1.data.vertices]
zs = [v.co.z for v in mesh1.data.vertices]
print(f'Mesh bounds: X[{min(xs):.4f}, {max(xs):.4f}] Y[{min(ys):.4f}, {max(ys):.4f}] Z[{min(zs):.4f}, {max(zs):.4f}]')

# ── 6. Remove lights ──
for obj in list(bpy.data.objects):
    if obj.type == 'LIGHT':
        bpy.data.objects.remove(obj, do_unlink=True)

# ── 7. Materials ──
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

# ── 8. Export ──
out = '/home/kim/hand-tracking/models/hand.glb'
bpy.ops.export_scene.gltf(
    filepath=out,
    export_format='GLB',
    export_skins=True,
    export_animations=False,
    export_apply=False,
    use_selection=False,
)
print(f'EXPORT: {out} ({os.path.getsize(out)} bytes)')
