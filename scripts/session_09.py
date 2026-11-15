"""Session 9 -- UV Unwrapping & Texturing. Run:
Blender --background --python scripts/session_09.py
"""
import sys
import os
import math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import bmesh
from mathutils import Vector, noise
import build_session as bs

ROOT = bs.ROOT
OUT = f"{ROOT}/session-09/renders"
os.makedirs(OUT, exist_ok=True)

bs.build_04(False)
for name in ("Sun", "Camera"):
    bpy.data.objects.remove(bpy.data.objects[name], do_unlink=True)
scn = bpy.context.scene
bs._studio_lighting(scn)

bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
ground = bpy.context.active_object
ground.name = "Ground"
ground.data.materials.append(bs.make_material("Ground_Warm", (0.75, 0.68, 0.58), roughness=0.8))


def unwrap_with_seams(obj):
    """Seams: the cap/side boundary rings (so caps become their own islands)
    plus one vertical meridian (so the side 'unrolls' into a flat strip)."""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(obj.data)
    marked = 0
    for e in bm.edges:
        e.seam = False
        caps = [abs(f.normal.z) > 0.99 for f in e.link_faces]
        ring = len(caps) == 2 and caps[0] != caps[1]
        meridian = all(abs(v.co.y) < 1e-4 and v.co.x > 0 for v in e.verts) and not any(caps)
        if ring or meridian:
            e.seam = True
            marked += 1
    for f in bm.faces:
        f.select = True
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.02)
    bpy.ops.object.mode_set(mode='OBJECT')
    print("SEAMS", obj.name, marked)


for n in ("Lamp_Shade", "Lamp_Base", "Lamp_Pole"):
    unwrap_with_seams(bpy.data.objects[n])

def textured_material(name, image, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = image
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


# Checker/grid image: any stretching or pinching in the UVs shows up as distorted squares.
grid = bpy.data.images.new("UV_Color_Grid", width=1024, height=1024)
grid.generated_type = 'COLOR_GRID'
grid.generated_width = 1024
grid.generated_height = 1024

# "Hand-painted" look: clean teal base with cream pinstripe bands and a mustard
# gradient cap, all roughened by fine brush-grain streaks along the bands.
W = H = 256
pix = []
teal = Vector((0.07, 0.34, 0.40))
cream = Vector((0.93, 0.88, 0.74))
mustard = Vector((0.90, 0.66, 0.16))
for y in range(H):
    v = y / H
    # 5 broad bands: teal, with a cream pinstripe pair and a mustard gradient at the top
    phase = (v * 5.0) % 1.0
    stripe = 1.0 if (0.44 < phase < 0.50 or 0.58 < phase < 0.62) else 0.0
    grad = max(0.0, (v - 0.78) / 0.22)
    for x in range(W):
        u = x / W
        grain = noise.noise(Vector((u * 3.0, v * 90.0, 1.0))) * 0.06
        wob = noise.noise(Vector((u * 6.0, v * 8.0, 2.0))) * 0.03
        c = teal.lerp(mustard, min(1.0, grad + wob))
        c = c.lerp(cream, stripe * 0.9)
        pix.extend((min(1, max(0, c.x + grain)), min(1, max(0, c.y + grain)),
                    min(1, max(0, c.z + grain)), 1.0))
painted = bpy.data.images.new("Hand_Painted_Pole", width=W, height=H)
painted.pixels.foreach_set(pix)
painted.update()
painted.pack()

shade = bpy.data.objects["Lamp_Shade"]
base = bpy.data.objects["Lamp_Base"]
pole = bpy.data.objects["Lamp_Pole"]
ridge = bpy.data.objects["Lamp_Base_Ridge"]
shade.data.materials.append(textured_material("Shade_UVGrid", grid, roughness=0.4))
base.data.materials.append(textured_material("Base_UVGrid", grid, roughness=0.4))
pole.data.materials.append(textured_material("Pole_HandPainted", painted, roughness=0.55))
ridge.data.materials.append(bs.make_material("Ridge_Accent", (0.8, 0.1, 0.1), metallic=0.8, roughness=0.25))

# Cameras for check renders / for the user.
overview, _ = bs._aimed_camera("Cam_Overview", (3.3, -4.0, 1.5), (0, 0, 0.9), 32)
cam_shade, _ = bs._aimed_camera("Cam_Shade", (1.7, -2.0, 1.9), (0, 0, 1.6), 85)
cam_base, _ = bs._aimed_camera("Cam_Base", (1.3, -1.8, 0.8), (0, 0, 0.2), 50)
for c in (overview, cam_shade, cam_base):
    c.data.show_composition_thirds = False
scn.camera = overview

scn.render.resolution_x = 700
scn.render.resolution_y = 560
try:
    scn.render.engine = 'BLENDER_EEVEE_NEXT'
except TypeError:
    scn.render.engine = 'BLENDER_EEVEE'
scn.eevee.taa_render_samples = 32
for cam, fn in ((overview, "overview"), (cam_shade, "shade_closeup"), (cam_base, "base_closeup")):
    scn.camera = cam
    scn.render.filepath = f"{OUT}/{fn}.png"
    bpy.ops.render.render(write_still=True)
scn.camera = overview

txt = bpy.data.texts.new("session-09-notes")
txt.write(
    "Session 9 -- UV Unwrapping & Texturing\n"
    "---------------------------------------\n"
    "Already done for you:\n"
    "  - Shade, base and pole are UV-unwrapped with hand-placed seams: a ring\n"
    "    around each cap plus one vertical line down the side (the 'cut along\n"
    "    the seam, unroll the tube' trick). Seams show as red edges in Edit Mode.\n"
    "  - Shade + base use a Color Grid image so any stretching is obvious;\n"
    "    the pole uses a clean 'hand-painted' image: teal with cream pinstripes\n"
    "    and a mustard fade near the top (packed in the file).\n\n"
    "Your turn:\n"
    "1. Open the UV Editing workspace tab, select Lamp_Shade, press Tab for\n"
    "   Edit Mode, A to select all. Compare the UV islands to the grid on the\n"
    "   3D side. Squares that look squashed = stretched UVs.\n"
    "2. Clear a seam (Alt+click an edge > Mark Seam menu > Clear Seam), re-unwrap\n"
    "   with U > Unwrap, and see how the grid changes. Then re-mark it.\n"
    "3. Try U > Smart UV Project and U > Cube Projection on the base for comparison.\n"
    "4. Texture Paint workspace: paint on the pole's image, or swap the pole's\n"
    "   image for your own.\n"
    "Reference renders: session-09/renders/ (overview, shade_closeup, base_closeup).\n"
)
bs.show_text(txt)
bs.save("session-09/session-09-start.blend")
