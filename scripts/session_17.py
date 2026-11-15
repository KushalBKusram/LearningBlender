"""
Session 17 helper: renders 6 blockout storyboard panels and composes a contact sheet.
  blender --background --python scripts/session_17.py -- panel N   # N = 1..6
  blender --background --python scripts/session_17.py -- sheet
"""
import os
import sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import build_session as bs

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session-17")
PW, PH = 640, 360

CAPTIONS = [
    ("S01  WIDE ESTABLISHING", "f001-048  (2.0s)", "Empty room, lamp unlit. A enters frame left."),
    ("S02  MEDIUM TRACKING", "f049-096  (2.0s)", "A patrols past, stops, head turns."),
    ("S03  CLOSE-UP", "f097-132  (1.5s)", "B's eyes peek from behind the lamp base."),
    ("S04  TWO-SHOT", "f133-186  (2.25s)", "B startles, bounces away. A reaches out."),
    ("S05  LOW ANGLE", "f187-240  (2.25s)", "A pulls the lamp chain. Shade glows."),
    ("S06  WIDE / RESOLVE", "f241-300  (2.5s)", "B returns, curls into the light. A sits. Fade."),
]


def mat(name, color, **kw):
    return bs.make_material(name, color, **kw)


def add_box(name, size, loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    o.data.materials.append(material)
    return o


def character_a(x, y, rot_z=0.0, arm_up=False, seated=False):
    m = mat("A_Blue", (0.15, 0.35, 0.75), metallic=0.3, roughness=0.4)
    dark = mat("A_Dark", (0.08, 0.1, 0.15), roughness=0.5)
    s = 0.6 if seated else 1.0
    root = bpy.data.objects.new("A_Root", None)
    bpy.context.scene.collection.objects.link(root)
    root.location = (x, y, 0)
    root.rotation_euler = (0, 0, rot_z)
    parts = [
        add_box("A_Torso", (0.42, 0.28, 0.5 * s), (0, 0, 0.75 * s), m),
        add_box("A_Pelvis", (0.36, 0.26, 0.16), (0, 0, 0.42 * s), dark),
        add_box("A_Head", (0.3, 0.26, 0.26), (0, 0, 1.15 * s + (0.0 if not seated else 0.1)), m),
        add_box("A_LegL", (0.14, 0.14, 0.42 * s), (-0.12, 0, 0.21 * s), dark),
        add_box("A_LegR", (0.14, 0.14, 0.42 * s), (0.12, 0, 0.21 * s), dark),
        add_box("A_ArmL", (0.1, 0.1, 0.45), (-0.3, 0, 0.8 * s), dark),
        add_box("A_ArmR", (0.1, 0.1, 0.45), (0.3, 0, 0.8 * s if not arm_up else 1.15), dark),
    ]
    if arm_up:
        parts[-1].rotation_euler = (0, math.radians(12), 0)
    for p in parts:
        p.parent = root
    return root


def character_b(x, y, z=0.35, squash=(1, 1, 1)):
    body = mat("B_Orange", (0.95, 0.45, 0.1), roughness=0.5)
    eye_w = mat("B_EyeWhite", (1, 1, 1), roughness=0.2)
    eye_k = mat("B_Pupil", (0.02, 0.02, 0.02), roughness=0.2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(x, y, z))
    b = bpy.context.active_object
    b.name = "B_Body"
    b.scale = squash
    b.data.materials.append(body)
    bpy.ops.object.shade_smooth()
    for sx in (-0.12, 0.12):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.09, location=(x + sx, y - 0.3, z + 0.1))
        e = bpy.context.active_object
        e.data.materials.append(eye_w)
        e.parent = b
        e.matrix_parent_inverse = b.matrix_world.inverted()
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045, location=(x + sx, y - 0.37, z + 0.1))
        p = bpy.context.active_object
        p.data.materials.append(eye_k)
        p.parent = b
        p.matrix_parent_inverse = b.matrix_world.inverted()
    return b


def lamp_glow(on):
    shade = bpy.data.objects["Lamp_Shade"]
    m = shade.data.materials[0]
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if on:
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.8, 0.5, 1)
        bsdf.inputs["Emission Strength"].default_value = 6.0
        bs._add_light(bpy.context.scene, "Lamp_Glow", 'POINT', 300, (0, 0, 1.4), color=(1.0, 0.75, 0.45))


def build_panel(n):
    bs.build_05(False)
    for nm in ("Sun", "Camera"):
        bpy.data.objects.remove(bpy.data.objects[nm], do_unlink=True)
    scn = bpy.context.scene
    bs._studio_lighting(scn)
    scn.render.resolution_x, scn.render.resolution_y = PW, PH
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'

    if n == 1:
        character_a(-3.2, -0.5, rot_z=math.radians(-90))
        cam, _ = bs._aimed_camera("Cam", (6.0, -7.0, 2.4), (-0.5, 0, 0.9), 28)
    elif n == 2:
        character_a(-1.2, -0.8, rot_z=math.radians(-30))
        cam, _ = bs._aimed_camera("Cam", (-0.5, -5.2, 1.2), (-1.0, 0, 0.9), 40)
    elif n == 3:
        character_b(0.45, 0.45, 0.38)
        cam, _ = bs._aimed_camera("Cam", (1.5, -1.7, 0.6), (0.4, 0.3, 0.4), 85)
    elif n == 4:
        character_a(-1.6, -0.3, rot_z=math.radians(-60), arm_up=True)
        character_b(1.7, 0.3, z=1.2, squash=(0.9, 0.9, 1.2))
        cam, _ = bs._aimed_camera("Cam", (0.0, -6.0, 1.4), (0, 0, 0.9), 35)
    elif n == 5:
        character_a(-0.9, -0.5, rot_z=math.radians(-40), arm_up=True)
        lamp_glow(True)
        cam, _ = bs._aimed_camera("Cam", (-1.0, -2.6, 0.15), (0, 0, 1.2), 24)
    else:
        character_a(-1.5, -0.2, rot_z=math.radians(-70), seated=True)
        character_b(0.75, 0.2, z=0.35, squash=(1.1, 1.1, 0.8))
        lamp_glow(True)
        cam, _ = bs._aimed_camera("Cam", (4.5, -5.0, 1.7), (0, 0, 0.75), 32)
    scn.camera = cam
    cam.data.show_composition_thirds = False
    scn.render.filepath = f"{ROOT}/panels/panel_{n}.png"
    bpy.ops.render.render(write_still=True)
    print("PANEL", n)


def build_sheet():
    bs.clear_scene()
    scn = bpy.context.scene
    W, H = 1800, 1040
    scn.render.resolution_x, scn.render.resolution_y = W, H
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'
    scn.view_settings.view_transform = 'Standard'
    world = bpy.data.worlds.new("W")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.09, 0.09, 0.1, 1)
    scn.world = world

    unit = 100.0 / (W / 1800.0)
    cols, rows = 3, 2
    pw, ph = 5.6, 3.15
    gap = 0.4
    cap_h = 1.0
    total_w = cols * pw + (cols + 1) * gap
    total_h = 1.1 + rows * (ph + cap_h) + (rows + 1) * gap
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.type = 'ORTHO'
    cam_data.ortho_scale = total_w
    cam = bpy.data.objects.new("Cam", cam_data)
    scn.collection.objects.link(cam)
    cam.location = (total_w / 2, total_h / 2, 10)
    scn.camera = cam
    scn.render.resolution_y = int(W * total_h / total_w)

    def add_text(body, x, y, size, color=(1, 1, 1), align='LEFT'):
        cu = bpy.data.curves.new("t", 'FONT')
        cu.body = body
        cu.size = size
        cu.align_x = align
        o = bpy.data.objects.new("t", cu)
        scn.collection.objects.link(o)
        o.location = (x, y, 0.1)
        m = bpy.data.materials.new("tm")
        m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = 1.0
        o.data.materials.append(m)

    add_text("STORYBOARD  -  'THE LAMP KEEPER'  -  300 frames @ 24fps (12.5s)",
             gap, total_h - 0.75, 0.42)
    for i in range(6):
        r, c = divmod(i, cols)
        x = gap + c * (pw + gap)
        y_top = total_h - 1.1 - gap - r * (ph + cap_h + gap)
        img = bpy.data.images.load(f"{ROOT}/panels/panel_{i+1}.png")
        img.colorspace_settings.name = 'sRGB'
        m = bpy.data.materials.new(f"p{i}")
        m.use_nodes = True
        nt = m.node_tree
        for nd in list(nt.nodes):
            nt.nodes.remove(nd)
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = img
        em = nt.nodes.new("ShaderNodeEmission")
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(tex.outputs["Color"], em.inputs["Color"])
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        bpy.ops.mesh.primitive_plane_add(size=1, location=(x + pw / 2, y_top - ph / 2, 0))
        p = bpy.context.active_object
        p.scale = (pw, ph, 1)
        p.data.materials.append(m)
        title, frames, note = CAPTIONS[i]
        add_text(title, x, y_top - ph - 0.35, 0.27)
        add_text(frames, x, y_top - ph - 0.7, 0.2, color=(0.7, 0.8, 1.0))
        add_text(note, x, y_top - ph - 0.98, 0.17, color=(0.85, 0.85, 0.85))
    scn.render.filepath = f"{ROOT}/storyboard_panels.png"
    bpy.ops.render.render(write_still=True)
    print("SHEET_DONE")


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "panel":
        build_panel(int(a[1]))
    else:
        build_sheet()
