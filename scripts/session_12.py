"""Session 12 -- Rigging Basics. Builds 'Character_A' (one connected mesh) + 'Character_Rig'.

Run: Blender --background --python scripts/session_12.py
"""
import os
import sys
import math
import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ----------------------------------------------------------------- mesh
def _cyl(radius, depth, loc, rot=(0, 0, 0), scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=radius, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.scale = scale
    return o


def _sphere(radius, loc, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20, ring_count=12, radius=radius, location=loc)
    o = bpy.context.active_object
    o.scale = scale
    return o


def build_body_mesh():
    parts = []
    parts.append(_cyl(0.2, 0.6, (0, 0, 1.15), scale=(1, 0.65, 1)))       # torso
    parts.append(_cyl(0.07, 0.25, (0, 0, 1.5)))                          # neck
    parts.append(_sphere(0.2, (0, 0, 1.72), scale=(0.9, 0.95, 1.15)))    # head
    parts.append(_cyl(0.06, 0.4, (0.18, 0, 1.38), rot=(0, math.radians(90), 0)))   # shoulders (both sides
    parts[-1].location.x = 0.0
    parts[-1].scale = (1, 1, 1.95)                                       # ... one long bar across)
    for s in (1, -1):
        parts.append(_cyl(0.06, 0.34, (s * 0.38, 0, 1.23)))              # upper arm
        parts.append(_cyl(0.052, 0.34, (s * 0.38, 0, 0.93)))             # lower arm
        parts.append(_sphere(0.07, (s * 0.38, 0, 0.7)))                  # hand
        parts.append(_cyl(0.085, 0.52, (s * 0.12, 0, 0.69)))             # thigh
        parts.append(_cyl(0.07, 0.42, (s * 0.12, 0, 0.26)))              # shin
        parts.append(_sphere(0.07, (s * 0.12, -0.05, 0.05), scale=(1, 2.2, 0.8)))  # foot

    bpy.ops.object.select_all(action='DESELECT')
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.object.join()
    body = bpy.context.active_object
    body.name = "Character_A"

    # Voxel remesh fuses the primitives into one watertight, connected skin so
    # automatic weights have a clean surface to bind to.
    rm = body.modifiers.new("Remesh", 'REMESH')
    rm.mode = 'VOXEL'
    rm.voxel_size = 0.03
    rm.use_smooth_shade = True
    bpy.ops.object.modifier_apply(modifier=rm.name)
    bpy.ops.object.shade_smooth()
    body.data.materials.append(bs.make_material("Character_Skin", (0.25, 0.5, 0.85), roughness=0.55))
    return body


# ----------------------------------------------------------------- rig
BONES = []  # (name, head, tail, parent, connect, deform)


def _bone_defs():
    d = []
    add = lambda *a, **k: d.append((a[0], Vector(a[1]), Vector(a[2]), a[3] if len(a) > 3 else None,
                                    k.get("connect", False), k.get("deform", True)))
    add("Root", (0, 0, 0), (0, 0, 0.15), deform=False)
    add("Hips", (0, 0, 0.9), (0, 0, 1.0), "Root")
    add("Spine", (0, 0, 1.0), (0, 0, 1.4), "Hips", connect=True)
    add("Head", (0, 0, 1.4), (0, 0, 1.95), "Spine", connect=True)
    for suf, s in ((".L", 1), (".R", -1)):
        add("Clavicle" + suf, (s * 0.05, 0, 1.38), (s * 0.38, 0, 1.38), "Spine")
        add("UpperArm" + suf, (s * 0.38, 0, 1.38), (s * 0.38, 0, 1.08), "Clavicle" + suf, connect=True)
        add("LowerArm" + suf, (s * 0.38, 0, 1.08), (s * 0.38, 0, 0.78), "UpperArm" + suf, connect=True)
        add("Hand" + suf, (s * 0.38, 0, 0.78), (s * 0.38, 0, 0.64), "LowerArm" + suf, connect=True)
        add("Thigh" + suf, (s * 0.12, 0, 0.95), (s * 0.12, -0.03, 0.5), "Hips")
        add("Shin" + suf, (s * 0.12, -0.03, 0.5), (s * 0.12, 0, 0.08), "Thigh" + suf, connect=True)
        add("Foot" + suf, (s * 0.12, 0, 0.08), (s * 0.12, -0.2, 0.04), "Shin" + suf, connect=True)
        add("Foot_IK" + suf, (s * 0.12, 0, 0.08), (s * 0.12, -0.2, 0.08), "Root", deform=False)
        add("Knee_Pole" + suf, (s * 0.12, -0.9, 0.5), (s * 0.12, -0.9, 0.6), "Root", deform=False)
    return d


def build_rig():
    arm_data = bpy.data.armatures.new("Character_Rig")
    rig = bpy.data.objects.new("Character_Rig", arm_data)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    for name, head, tail, parent, connect, deform in _bone_defs():
        b = eb.new(name)
        b.head, b.tail = head, tail
        b.use_deform = deform
        b.roll = 0.0
    for name, head, tail, parent, connect, deform in _bone_defs():
        if parent:
            eb[name].parent = eb[parent]
            eb[name].use_connect = connect
    bpy.ops.object.mode_set(mode='OBJECT')
    arm_data.display_type = 'OCTAHEDRAL'
    rig.show_in_front = True
    return rig


def add_leg_ik(rig):
    """IK on the shins (chain of 2), pole targets steer the knees forward (-Y);
    feet copy rotation from the IK target bones."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    for suf in (".L", ".R"):
        shin = rig.pose.bones["Shin" + suf]
        ik = shin.constraints.new('IK')
        ik.target = rig
        ik.subtarget = "Foot_IK" + suf
        ik.pole_target = rig
        ik.pole_subtarget = "Knee_Pole" + suf
        ik.chain_count = 2
        foot = rig.pose.bones["Foot" + suf]
        cr = foot.constraints.new('COPY_ROTATION')
        cr.target = rig
        cr.subtarget = "Foot_IK" + suf
        cr.target_space = 'WORLD'
        cr.owner_space = 'WORLD'
    for pb in rig.pose.bones:
        pb.rotation_mode = 'XYZ'
    bpy.ops.object.mode_set(mode='OBJECT')

    # Pick the pole angle that actually puts the knee in front (-Y).
    best = None
    for deg in (0, 90, -90, 180):
        for suf in (".L", ".R"):
            rig.pose.bones["Shin" + suf].constraints["IK"].pole_angle = math.radians(deg)
        pb_hip = rig.pose.bones["Hips"]
        pb_hip.location = rig.pose.bones["Hips"].bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, -0.12))
        bpy.context.view_layer.update()
        knee_y = (rig.matrix_world @ rig.pose.bones["Shin.L"].head).y
        if best is None or knee_y < best[0]:
            best = (knee_y, deg)
        pb_hip.location = (0, 0, 0)
    for suf in (".L", ".R"):
        rig.pose.bones["Shin" + suf].constraints["IK"].pole_angle = math.radians(best[1])
    bpy.context.view_layer.update()
    print("POLE_ANGLE", best)


def bind(body, rig):
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')


def world_offset(pb, v):
    """Set a pose bone's location from a world-space delta (parent must be un-posed)."""
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(v)


def setup_stage(scene):
    bs._studio_lighting(scene)
    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    g = bpy.context.active_object
    g.name = "Ground"
    g.data.materials.append(bs.make_material("Ground_Warm", (0.75, 0.68, 0.58), roughness=0.8))
    bs._aimed_camera("Cam_Front", (2.6, -4.2, 1.5), (0, 0, 0.95), 38)
    bs._aimed_camera("Cam_Side", (5.2, 0.0, 1.0), (0, 0, 0.95), 40)
    scene.camera = bpy.data.objects["Cam_Front"]


NOTES = """Session 12 -- Rigging Basics
============================
Character_A (one connected mesh) is already bound to Character_Rig with
automatic weights. Your job is to poke at it and make the deformation better.

Rig layout
- Root (no deform) > Hips > Spine > Head; Spine > Clavicle.L/R > UpperArm > LowerArm > Hand
- Hips > Thigh.L/R > Shin > Foot  (legs are driven by IK)
- Foot_IK.L/R: move these to move the feet. Knee_Pole.L/R: steer where the knees point.
  Both are non-deforming control bones parented to Root.

Try this
1. Select Character_Rig, switch to Pose Mode (Ctrl+Tab). Rotate LowerArm.L (R, X) to bend an elbow.
2. Grab Foot_IK.L (G, Z) and lift it -- the knee should bend forward.
3. Move Hips down (G Z) for a crouch. Then rotate Head and Spine.
4. Look for pinching/collapsing at elbows, knees and shoulders. Select Character_A, enter
   Weight Paint mode, pick a bone, and fix the weights (Smooth / Average brushes).
5. Reset a pose: Alt+G / Alt+R / Alt+S on selected bones, or Select All then clear transforms.
"""


def build_character(save_file=True):
    bs.clear_scene()
    scene = bpy.context.scene
    body = build_body_mesh()
    rig = build_rig()
    bind(body, rig)
    add_leg_ik(rig)
    setup_stage(scene)
    txt = bpy.data.texts.new("session-12-notes")
    txt.write(NOTES)
    bs.show_text(txt)
    if save_file:
        bs.save("session-12/session-12-start.blend")
    return body, rig


if __name__ == "__main__":
    build_character(True)
