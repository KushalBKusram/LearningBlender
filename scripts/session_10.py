"""Session 10 -- Sculpting Basics: a round creature head, ready to sculpt.

Run: Blender --background --python scripts/session_10.py
Head has Multires subdivided twice; eyes/ears/nose are separate parented objects so the
head can be sculpted freely (and later rigged as capstone "Character B").
"""
import os
import sys
import math
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs

OUT = "session-10/session-10-start.blend"


def sphere(name, loc, scale, mat, segments=32, rings=16, radius=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=radius, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    bpy.ops.object.shade_smooth()
    o.data.materials.append(mat)
    return o


def _g(d, s):
    return math.exp(-(d / s) ** 2)


def starter_face_sculpt(head):
    """Push brow ridges, cheek puffs, a muzzle and a smiling mouth groove into the
    base mesh (before Multires), so the head reads as a character, not a ball.
    Displacement is along each vertex normal; co is head-local (centre at origin)."""
    me = head.data
    new = []
    for v in me.vertices:
        x, y, z = v.co
        front = max(0.0, -y / 0.62)          # only affect the face side (-Y)
        d = 0.0
        for sx in (1, -1):
            # brow ridge over each eye, slanting slightly inward-down
            bz = 0.31 - 0.02 * (1 - abs(x) / 0.35)
            d += 0.075 * _g(x - sx * 0.24, 0.14) * _g(z - bz, 0.05)
            # cheek puff
            d += 0.05 * _g(x - sx * 0.34, 0.12) * _g(z + 0.10, 0.11)
        # muzzle swell under the nose
        d += 0.045 * _g(x, 0.18) * _g(z + 0.13, 0.14)
        # smiling mouth groove (inward), corners lifted
        mz = -0.235 + 0.9 * x * x
        d -= 0.06 * _g(z - mz, 0.03) * max(0.0, 1 - (abs(x) / 0.30) ** 2)
        # philtrum notch from nose to mouth
        d -= 0.025 * _g(x, 0.02) * (1.0 if -0.22 < z < -0.10 else 0.0)
        new.append(v.co + v.normal * (d * front))
    for v, co in zip(me.vertices, new):
        v.co = co
    me.update()
    bpy.ops.object.shade_smooth()


def build():
    bs.clear_scene()
    scn = bpy.context.scene
    coll = bs.new_collection("Character_B")

    # Same orange family the capstone tints Character B ("Mote") with, so what you
    # sculpt here drops straight into Session 18 without a colour jump.
    clay = bs.make_material("Clay_Head", (0.95, 0.42, 0.10), roughness=0.6)
    ear_mat = bs.make_material("Clay_Ear", (1.00, 0.58, 0.30), roughness=0.6)
    eye_mat = bs.make_material("Eye_White", (0.95, 0.95, 0.92), roughness=0.15)
    pupil_mat = bs.make_material("Eye_Pupil", (0.02, 0.02, 0.03), roughness=0.1)
    nose_mat = bs.make_material("Nose_Dark", (0.12, 0.06, 0.06), roughness=0.3)
    ground_mat = bs.make_material("Ground_Warm", (0.75, 0.68, 0.58), roughness=0.8)

    # Denser base mesh (64x32) so a starter face can be pushed into it before Multires.
    head = sphere("Creature_Head", (0, 0, 0.75), (1.0, 0.95, 0.88), clay,
                  segments=64, rings=32, radius=0.65)
    starter_face_sculpt(head)
    parts = [head]

    for side, sx in (("L", 1), ("R", -1)):
        ear = sphere(f"Creature_Ear{side}", (sx * 0.52, 0.02, 1.25), (0.28, 0.12, 0.28), ear_mat, radius=1.0)
        ear.rotation_euler = (0, math.radians(-25 * sx), 0)
        eye = sphere(f"Creature_Eye{side}", (sx * 0.24, -0.52, 0.88), (1, 1, 1), eye_mat, radius=0.15)
        pupil = sphere(f"Creature_Pupil{side}", (sx * 0.24, -0.655, 0.88), (1, 1, 1), pupil_mat, radius=0.075)
        parts += [ear, eye, pupil]
    nose = sphere("Creature_Nose", (0, -0.655, 0.68), (1.3, 1.0, 0.9), nose_mat, radius=0.09)
    parts.append(nose)

    for p in parts[1:]:
        p.parent = head
        p.matrix_parent_inverse = head.matrix_world.inverted()
    for p in parts:
        bs.move_to_collection(p, coll)

    bpy.context.view_layer.objects.active = head
    head.select_set(True)
    head.modifiers.new("Multires", 'MULTIRES')
    for _ in range(2):
        bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')
    mr = head.modifiers["Multires"]
    mr.levels = mr.sculpt_levels = mr.render_levels = 2

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(ground_mat)

    bs._studio_lighting(scn)
    # AgX washes saturated colours out toward pale pastel; Standard keeps the set colour.
    scn.view_settings.view_transform = 'Standard'
    scn.view_settings.exposure = -1.6
    cam, _ = bs._aimed_camera("Camera", (0.0, -3.4, 1.05), (0, 0, 0.75), 50)
    scn.camera = cam

    txt = bpy.data.texts.new("session-10-notes")
    txt.write(
        "Session 10 -- Sculpting Basics\n"
        "-------------------------------\n"
        "Creature_Head has a Multires modifier already subdivided to level 2.\n"
        "Eyes, ears and nose are separate objects parented to the head (they follow it).\n\n"
        "To sculpt: select Creature_Head, switch to the Sculpting workspace tab.\n"
        "Brushes to try (shortcut keys in sculpt mode):\n"
        "  Draw (D)       - push/pull volume: brow ridge, cheeks, snout\n"
        "  Clay Strips    - build up forms quickly\n"
        "  Grab (G)       - move big shapes: pull the jaw, stretch an ear\n"
        "  Smooth (Shift) - hold Shift with any brush to relax lumps\n"
        "  Crease         - wrinkles, mouth line, eye sockets\n"
        "  Mask / Inflate - fine control, puffy cheeks\n"
        "Tips: turn on X-Mirror (symmetry buttons, top right) so both sides match.\n"
        "Ctrl+Wheel or the Multires 'Sculpt' level steps between detail levels.\n"
        "Already pushed in as a starter: brow ridges, cheek puffs, a muzzle and a smiling\n"
        "mouth line. Colours match Character B ('Mote') in Session 18 -- keep the object\n"
        "names (Creature_*) so the capstone can pick your sculpt up.\n"
        "Deliverable: take it further -- deepen the mouth, add eyelids, a chin, wrinkles.\n"
        "Save when done; it may become the capstone's Character B.\n"
    )
    bs.show_text(txt)
    bs.save(OUT)


if __name__ == "__main__":
    build()
