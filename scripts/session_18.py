"""Session 18 -- Capstone skeleton: "The Lamp Keeper" (see session-17/storyboard.md).

Assembles Character A (Session 12/13 rig + walk), Character B (Session 10 creature, recoloured
"Mote" orange), the Session 4/5 lamp, studio lighting (Session 6) and the six storyboard cameras
(Session 7 vocabulary) in ONE scene, with rough blocking animation, camera-binding markers and a
placeholder VSE timeline.

  Blender --background --python scripts/session_18.py              # build the .blend
  Blender --background session-18/session-18-start.blend --python scripts/session_18.py -- check
  Blender --background session-18/session-18-start.blend --python scripts/session_18.py -- preview
"""
import os
import re
import sys
import math
import tempfile

import bpy
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT + "/scripts")
import build_session as bs  # noqa: E402
import session_10  # noqa: E402
import session_12 as s12  # noqa: E402
import session_13  # noqa: E402

OUT = "session-18/session-18-start.blend"
FPS, END = 24, 300
SHOTS = [("S01", 1, 48), ("S02", 49, 96), ("S03", 97, 132),
         ("S04", 133, 186), ("S05", 187, 240), ("S06", 241, 300)]

A_SCALE = 0.8            # Character A rig scale (1.95 -> ~1.56 tall)
B_SCALE = 0.55           # Character B ("Mote") base scale (head radius ~0.36)
STOP = 79                # frame A finishes its last step (walk phase == frame 7: feet together)
YAW_WALK = math.radians(90)    # rig yaw while walking: faces +X
YAW_FACE = math.radians(135)   # rig yaw when facing the lamp from the south-west
# Chair + sit-down staging (world metres / radians; rig/chair forward vector = (sin yaw, -cos yaw)).
WALK_YAW = math.radians(216)     # heading from the lamp stop toward the chair
SIT_YAW = math.radians(77.6)     # chair/seated-A facing (toward the light pool where B settles)
WALK_LEN = 1.2                   # 36 walk-phase units * (2*STRIDE/12*A_SCALE)
FEET_FWD = 0.34                  # seated feet sit this far in front of the seat centre
SEAT_TOP = 0.44
GROUND_FIX = 0.033               # rig sits this much lower so the soles touch the floor (mesh bottom was 3.3 cm up)
REACH_UPPER, REACH_LOWER = math.radians(-85), math.radians(-25)  # -X swings the arm forward (-Y)


def sstep(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def piecewise(f, pts):
    """Smoothstep-interpolate between (frame, value) control points; clamp outside."""
    if f <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * sstep((f - f0) / (f1 - f0))
    return pts[-1][1]


# ------------------------------------------------------------------ assets
def stage_parts():
    """Build lamp + creature in throwaway .blend files, then Character A as the live scene."""
    tmp = tempfile.mkdtemp(prefix="s18_")
    lamp_path, cre_path = os.path.join(tmp, "lamp.blend"), os.path.join(tmp, "creature.blend")
    bs.build_05(False)
    bpy.ops.wm.save_as_mainfile(filepath=lamp_path, copy=True)
    real_save, bs.save = bs.save, (lambda *a, **k: None)
    try:
        session_10.build()
    finally:
        bs.save = real_save
    bpy.ops.wm.save_as_mainfile(filepath=cre_path, copy=True)
    body, rig = session_13.build(False)
    return body, rig, lamp_path, cre_path


def append_objects(path, pick):
    with bpy.data.libraries.load(path, link=False) as (src, dst):
        dst.objects = [n for n in src.objects if pick(n)]
    return list(dst.objects)


def key(obj_or_struct, prop, frame, **kw):
    obj_or_struct.keyframe_insert(prop, frame=frame, **kw)


# ------------------------------------------------------------------ Character A
def solve_stop_position(rig, chain_xy):
    """Where must A stand (facing YAW_FACE, arm in full reach pose) so the hand meets the chain?"""
    rig.animation_data.action = None
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_euler = (0, 0, 0)
    rig.scale = (A_SCALE,) * 3
    rig.location = (0, 0, 0)
    rig.rotation_euler = (0, 0, YAW_FACE)
    rig.pose.bones["UpperArm.L"].rotation_euler = (REACH_UPPER, 0, 0)
    rig.pose.bones["LowerArm.L"].rotation_euler = (REACH_LOWER, 0, 0)
    bpy.context.view_layer.update()
    hand = rig.matrix_world @ rig.pose.bones["Hand.L"].tail
    for pb in rig.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    stop = Vector((chain_xy[0] - hand.x, chain_xy[1] - hand.y, 0))
    return stop, hand.z


def animate_keeper(rig, stop_xy):
    scene = bpy.context.scene
    walk = bpy.data.actions["Walk_Cycle"]
    slot = rig.animation_data.action_slot if rig.animation_data else None
    cb = walk.layers[0].strips[0].channelbag(slot) if slot else None

    # session_13.build() left the action assigned; solve_stop_position() cleared it, so find
    # the channelbag through the action's own slot list instead.
    if cb is None:
        cb = walk.layers[0].strips[0].channelbag(walk.slots[0])
    chan = {}
    for fc in cb.fcurves:
        m = re.match(r'pose\.bones\["(.+)"\]\.(location|rotation_euler)', fc.data_path)
        chan.setdefault((m.group(1), m.group(2)), {})[fc.array_index] = fc

    def cycle(bone, prop, f):
        d = chan[(bone, prop)]
        return Vector([d[i].evaluate(f) if i in d else 0.0 for i in range(3)])

    # Root travel along +X. The walk PHASE decelerates smoothly (ease-out) into the stop pose
    # (phase 79 == cycle frame 7: left foot planted, right foot passing) and the root speed is
    # tied to the phase rate, so the planted foot stays planted instead of skating.
    v0 = session_13.STRIDE * 2 / 12 * A_SCALE
    F0, F1, D = 67, 91, STOP - 67          # decel from f67 to f91 covers 12 phase units
    def phase(f):
        if f <= F0:
            return float(f)
        if f >= F1:
            return float(STOP)
        t = (f - F0) / (F1 - F0)
        return F0 + D * (2 * t - t * t)
    disp, x = {}, 0.0
    for f in range(1, END + 1):
        disp[f] = x
        x += v0 * (phase(f + 1) - phase(f))
    x_start = stop_xy.x - disp[END]

    arm_reach = [(150, 0), (165, 0.35), (175, 0.35), (184, 0.15), (188, 0.2), (202, 1.0),
                 (206, 1.0), (210, 0.85), (214, 0.85), (228, 0.0)]

    rig.rotation_mode = 'XYZ'
    for f in range(1, END + 1):
        scene.frame_set(f)
        cf = phase(f)
        w = sstep((f - F1) / 10.0)
        if f >= 224:   # walk the 36-phase-unit path to the chair, cycle weight back to 0 only while walking
            w = 1.0 - sstep((f - 224) / 5.0) * (1.0 - sstep((f - 259) / 5.0))
            t_walk = sstep((f - 228) / 32.0)
            cf = 79 + 36 * t_walk
        reach = piecewise(f, arm_reach)
        head_turn = math.radians(55) * sstep((f - 92) / 10.0) * (1.0 - sstep((f - 150) / 20.0))
        # Flinch when B pops out (f134): lean back, step the hips back, arms snap up, then settle.
        bump = piecewise(f, [(133, 0), (136, 1), (141, 0.8), (150, 0.25), (158, 0)])
        sit = sstep((f - 264) / 16.0)
        crouch = -(0.31 - GROUND_FIX / A_SCALE) * sit
        for (bone, prop) in chan:
            pb = rig.pose.bones[bone]
            v = cycle(bone, prop, cf) * (1.0 - w)
            if bone == "Head" and prop == "rotation_euler":
                v.y += head_turn
                v.x += math.radians(10) * bump
            if bone in ("UpperArm.L", "UpperArm.R") and prop == "rotation_euler":
                v.x += math.radians(-38) * bump
            if bone in ("LowerArm.L", "LowerArm.R") and prop == "rotation_euler":
                v.x += math.radians(-25) * bump
            if bone == "UpperArm.L" and prop == "rotation_euler":
                v.x += REACH_UPPER * reach
            if bone == "LowerArm.L" and prop == "rotation_euler":
                v.x += REACH_LOWER * reach
            if bone == "Hips" and prop == "location":
                v += pb.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0.34 / A_SCALE * sit, crouch))
            if bone == "Hips" and prop == "location":
                v += pb.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0.07 * bump, 0))
            if bone == "Spine" and prop == "rotation_euler":
                v.x += math.radians(6) * sit + math.radians(-14) * bump
            setattr(pb, prop, v)
            pb.keyframe_insert(prop, frame=f)
        yaw = YAW_WALK + (YAW_FACE - YAW_WALK) * sstep((f - 150) / 25.0)
        loc = Vector((x_start + disp[f], stop_xy.y))
        if f >= 220:
            yaw = YAW_FACE + (WALK_YAW - YAW_FACE) * sstep((f - 220) / 8.0) + (SIT_YAW - WALK_YAW) * sstep((f - 258) / 8.0)
            u = Vector((math.sin(WALK_YAW), -math.cos(WALK_YAW)))
            loc = Vector((x_start + disp[END], stop_xy.y)) + u * WALK_LEN * sstep((f - 228) / 32.0)
        rig.location = (loc.x, loc.y, -GROUND_FIX)
        rig.rotation_euler = (0, 0, yaw)
        rig.keyframe_insert("location", frame=f)
        rig.keyframe_insert("rotation_euler", frame=f)
    rig.animation_data.action.name = "Keeper_Blocking"
    scene.frame_set(1)
    return x_start, disp


# ------------------------------------------------------------------ Chair
def make_chair(center_xy, yaw):
    """Simple wooden chair, seat top at SEAT_TOP, front toward local -Y, then yawed like the rig."""
    coll = bs.new_collection("Chair")
    parts = []

    def box(name, size, loc):
        bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
        o = bpy.context.active_object
        o.name = name
        o.scale = size
        bpy.ops.object.transform_apply(scale=True)
        parts.append(o)

    box("Seat", (0.46, 0.44, 0.04), (0, 0, SEAT_TOP - 0.02))
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
        box(f"Leg{i}", (0.045, 0.045, SEAT_TOP - 0.04), (sx * 0.19, sy * 0.185, (SEAT_TOP - 0.04) / 2))
    for sx in (-1, 1):
        box(f"BackPost{sx}", (0.045, 0.045, 0.52), (sx * 0.19, 0.185, SEAT_TOP + 0.26))
    for z in (0.68, 0.80, 0.91):
        box(f"Rail{z}", (0.34, 0.03, 0.07), (0, 0.185, z))
    for z in (SEAT_TOP - 0.10,):
        box("Stretcher", (0.34, 0.03, 0.03), (0, -0.185, z))

    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    chair = bpy.context.active_object
    chair.name = "Wooden_Chair"
    bev = chair.modifiers.new("Bevel", 'BEVEL')
    bev.width, bev.segments = 0.006, 2

    mat = bpy.data.materials.new("Chair_Wood")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    coord = nt.nodes.new("ShaderNodeTexCoord")
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 7.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.28, 0.15, 0.07, 1)
    ramp.color_ramp.elements[1].color = (0.52, 0.30, 0.14, 1)
    nt.links.new(coord.outputs["Object"], wave.inputs["Vector"])
    nt.links.new(wave.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5
    chair.data.materials.append(mat)

    chair.location = (center_xy[0], center_xy[1], 0)
    chair.rotation_euler = (0, 0, yaw)
    bs.move_to_collection(chair, coll)
    return chair


# ------------------------------------------------------------------ Character B
def setup_mote():
    scene = bpy.context.scene
    coll = bs.new_collection("Character_B")
    objs = append_objects(CRE_PATH, lambda n: n.startswith("Creature_"))
    for o in objs:
        coll.objects.link(o)
    head = bpy.data.objects["Creature_Head"]
    head.location.z -= 0.178            # head bottom now rests on z = 0
    root = bpy.data.objects.new("Character_B_Root", None)
    root.empty_display_type = 'PLAIN_AXES'
    coll.objects.link(root)
    head.parent = root

    def tint(mat_name, rgb):
        mat = bpy.data.materials[mat_name]
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*rgb, 1)
    tint("Clay_Head", (0.95, 0.42, 0.10))
    tint("Clay_Ear", (1.00, 0.58, 0.30))
    return root


def animate_mote(root):
    def pose(f, loc, scl=(1, 1, 1)):
        root.location = loc
        root.scale = tuple(B_SCALE * s for s in scl)
        root.keyframe_insert("location", frame=f)
        root.keyframe_insert("scale", frame=f)

    SQUASH, STRETCH, LAND = (1.25, 1.25, 0.7), (0.85, 0.85, 1.25), (0.9, 0.9, 1.15)

    def arc(c0, c1, p0, p1, h):
        """Parabolic hop from contact c0 to contact c1: take-off c0+3, landing c1-2, keyed every
        2 frames; stretch follows vertical speed, so apex is round and take-off/landing are long."""
        t_off, t_land = c0 + 3, c1 - 2
        pose(c0, (*p0, 0.0), SQUASH)                       # anticipation squash on the floor
        for f in range(t_off, t_land + 1, 2):
            u = (f - t_off) / (t_land - t_off)
            xy = (p0[0] + (p1[0] - p0[0]) * u, p0[1] + (p1[1] - p0[1]) * u)
            z = h * 4 * u * (1 - u)
            vz = abs(1 - 2 * u)                            # 1 at take-off/landing, 0 at apex
            sz = 1 + 0.28 * vz
            sxy = 1 / math.sqrt(sz)
            pose(f, (*xy, z), (sxy, sxy, sz))
        pose(t_land, (*p1, 0.0), LAND)
    hide = (0.35, 0.75)

    # S01-S02: hidden below the floor. S03: rises just far enough to peek, bobs, blinks.
    pose(1, (*hide, -1.0))
    pose(96, (*hide, -1.0))
    pose(106, (*hide, -0.22), (0.92, 0.92, 1.1))
    pose(110, (*hide, -0.22))
    pose(120, (*hide, -0.18))
    pose(132, (*hide, -0.22))

    # S04: startle (stretch + squash) then three hops to the right.
    P = [(0.45, 0.80), (1.20, 0.75), (1.95, 0.50), (2.65, 0.70)]
    C = [136, 152, 168, 184]
    pose(134, (*hide, -0.05), (0.8, 0.8, 1.3))
    pose(C[0], (*P[0], 0.0), SQUASH)
    for i, h in enumerate((0.75, 0.6, 0.5)):
        arc(C[i], C[i + 1], P[i], P[i + 1], h)
    pose(C[3], (*P[3], 0.0), SQUASH)
    pose(190, (*P[3], 0.0))
    # S05: watches the lamp, breathing.
    pose(205, (*P[3], 0.0), (1.02, 1.02, 1.05))
    pose(220, (*P[3], 0.0))
    pose(236, (*P[3], 0.0), (1.02, 1.02, 1.05))
    pose(244, (*P[3], 0.0))
    # S06: slow small hops back to the light pool, then curls up.
    Q = [P[3], (2.05, 0.45), (1.50, 0.15), (1.00, -0.25)]
    D = [246, 260, 274, 288]
    pose(D[0], (*Q[0], 0.0), SQUASH)
    for i in range(3):
        arc(D[i], D[i + 1], Q[i], Q[i + 1], 0.28)
    pose(D[3], (*Q[3], 0.0), SQUASH)
    pose(296, (*Q[3], 0.0), (1.3, 1.3, 0.55))
    pose(300, (*Q[3], 0.0), (1.3, 1.3, 0.55))

    # Blinks: eyes squash flat (scale Z). Peek blink in S03, sleepy close in S06.
    eyes = [bpy.data.objects[n] for n in ("Creature_EyeL", "Creature_EyeR", "Creature_PupilL", "Creature_PupilR")]

    def eye_z(f, z):
        for e in eyes:
            e.scale = (1, 1, z)
            e.keyframe_insert("scale", frame=f)
    for f, z in ((1, 1), (113, 1), (116, 0.12), (119, 1), (126, 1), (128, 0.12), (130, 1),
                 (286, 1), (292, 0.15), (296, 0.1), (300, 0.1)):
        eye_z(f, z)


# ------------------------------------------------------------------ lamp, lights, cameras
def animate_lighting(scene, chain, chain_z):
    shade_mat = bpy.data.materials["Lamp_Shade_Plastic"]
    bsdf = shade_mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.55, 0.15, 1)
    for f, v in ((1, 0.0), (209, 0.0), (210, 2.2), (212, 0.6), (214, 3.0), (216, 1.8), (230, 4.0), (300, 4.0)):
        bsdf.inputs["Emission Strength"].default_value = v
        bsdf.inputs["Emission Strength"].keyframe_insert("default_value", frame=f)

    glow = bs._add_light(scene, "Lamp_Glow", 'POINT', 0, (0, 0, 1.25), color=(1.0, 0.70, 0.40))
    glow.data.shadow_soft_size = 0.15
    for f, v in ((1, 0), (209, 0), (210, 1100), (212, 300), (214, 1500), (216, 900), (230, 2000), (288, 2000), (300, 0)):
        glow.data.energy = v
        glow.data.keyframe_insert("energy", frame=f)

    for name in ("Key", "Fill", "Rim"):
        light = bpy.data.objects[name]
        base = light.data.energy
        for f, m in ((1, 0.7), (209, 0.7), (230, 0.25), (288, 0.25), (300, 0.0)):
            light.data.energy = base * m
            light.data.keyframe_insert("energy", frame=f)
        light.data.energy = base * 0.7

    bg = scene.world.node_tree.nodes["Background"]
    for f, v in ((1, 0.4), (209, 0.4), (230, 0.12), (288, 0.12), (300, 0.0)):
        bg.inputs["Strength"].default_value = v
        bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
    for f, v in ((1, -0.35), (288, -0.35), (300, -8.0)):
        scene.view_settings.exposure = v
        scene.view_settings.keyframe_insert("exposure", frame=f)
    scene.view_settings.exposure = -0.35

    # Chain pull (S05): drops a few cm as A's hand pulls it.
    for f, dz in ((1, 0.0), (203, 0.0), (206, -0.01), (209, -0.075), (213, -0.075), (216, 0.012), (219, -0.004), (222, 0.0), (300, 0.0)):
        chain.location.z = chain_z + dz
        chain.keyframe_insert("location", frame=f)


def make_chain(chain_xy, hand_z):
    top = 1.40
    length = max(0.12, top - hand_z)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.006, depth=length, vertices=8,
                                        location=(chain_xy[0], chain_xy[1], top - length / 2))
    chain = bpy.context.active_object
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.028, segments=12, ring_count=8,
                                         location=(chain_xy[0], chain_xy[1], top - length))
    bead = bpy.context.active_object
    bpy.ops.object.select_all(action='DESELECT')
    chain.select_set(True)
    bead.select_set(True)
    bpy.context.view_layer.objects.active = chain
    bpy.ops.object.join()
    chain.name = "Lamp_Chain"
    chain.data.materials.append(bpy.data.materials["Lamp_Metal"])
    bs.move_to_collection(chain, bpy.data.collections["Lamp"])
    return chain


def setup_cameras(scene, a_x, head):
    cams = {}
    cams["S01"], _ = bs._aimed_camera("Cam_S01", (6, -7, 2.4), (-0.5, 0, 0.9), 28)

    c2, t2 = bs._aimed_camera("Cam_S02", (-1.2, -5.2, 1.2), (-1.4, -0.5, 0.9), 40)
    for f, cx, tx in ((49, a_x(49) + 0.2, a_x(49)), (96, a_x(96) + 0.3, a_x(96))):
        c2.location.x, t2.location.x = cx, tx
        c2.keyframe_insert("location", frame=f)
        t2.keyframe_insert("location", frame=f)
    cams["S02"] = c2

    c3, t3 = bs._aimed_camera("Cam_S03", (1.2, -2.4, 0.42), (0.35, 0.75, 0.22), 50)
    c3.data.dof.use_dof = True
    c3.data.dof.focus_object = head
    c3.data.dof.aperture_fstop = 1.4
    cams["S03"] = c3

    cams["S04"], _ = bs._aimed_camera("Cam_S04", (0, -6, 1.4), (1.1, 0.4, 0.7), 35)
    cams["S05"], _ = bs._aimed_camera("Cam_S05", (1.2, -2.4, 0.15), (-0.2, -0.1, 0.95), 23)

    c6, _ = bs._aimed_camera("Cam_S06", (4.5, -5, 1.7), (0.6, 0, 0.6), 32)
    start = c6.location.copy()
    end = start + (Vector((0.6, 0, 0.6)) - start) * 0.10
    c6.location = start
    c6.keyframe_insert("location", frame=241)
    c6.location = end
    c6.keyframe_insert("location", frame=300)
    cams["S06"] = c6

    for name, start_f, _ in SHOTS:
        m = scene.timeline_markers.new(name, frame=start_f)
        m.camera = cams[name]
    scene.camera = cams["S01"]
    return cams


NOTES = """Session 18 -- Capstone: "The Lamp Keeper"
==========================================
This is a ROUGH BLOCKING skeleton of the whole short (24 fps, frames 1-300, 1280x720). Everything
needed is already in the scene; your job is to make it good. Story + shot list: session-17/storyboard.md.

What is already here
- Character A  : Character_A + Character_Rig (Session 12 rig, Session 13 walk). Action 'Keeper_Blocking'
                 (baked per-frame keys, so you can edit any key in the Dope Sheet / Graph Editor).
- Character B  : Character_B collection (Session 10 creature, orange). Animate 'Character_B_Root'
                 for position/squash; the eyes blink via their own scale keys.
- The lamp     : Lamp collection + a small pull-chain (Lamp_Chain). Shade emission and the warm
                 'Lamp_Glow' light ramp on at frames ~209-222 (the glow moment).
- Six cameras  : Cam_S01..S06, bound to the timeline by markers (S01 f1, S02 f49, S03 f97, S04 f133,
                 S05 f187, S06 f241). Render the animation and it cuts between them automatically.
- Fade to black: exposure + world + lights ramp to zero over the last 12 frames.
- VSE timeline : six placeholder colour strips S01..S06 at the shot ranges (alternating channels 1/2).

Roughness you should fix (suggested order, see the cut list in the storyboard)
1. A's walk slides a little at the stop; refine foot contacts and the stop (frames 70-95).
2. A's reach for the chain: tweak UpperArm.L / LowerArm.L and add a hand close-up pose (f 195-215).
3. A's "sit" at the end is a crouch; add real sit poses / spine curve (f 250-275).
4. B is a rigid blob that squashes at the root; sculpt it (Session 10), add ear/eye life.
5. Add audio (storyboard audio plan), then render each shot.

Assembling the final cut
- The scene's Sequencer output is turned OFF (Render > Post Processing > Sequencer) so rendering
  gives you the 3D shots. Render each shot to image sequences/movies, replace the colour strips
  with them (Add > Movie / Image), add audio, TURN SEQUENCER ON, then render to MPEG4 / H.264.
- Quick preview render: Eevee, resolution_percentage 50. Final: 100%.
"""


# ------------------------------------------------------------------ realism: room, materials, Cycles
def _mat(name):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]


def _box(name, size, loc, mat, coll):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(mat)
    bs.move_to_collection(o, coll)
    return o


def make_room(scene):
    """Wood-plank floor, plaster walls (back + left), baseboards, a daylight window on the left wall."""
    if "Ground" in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects["Ground"], do_unlink=True)
    coll = bs.new_collection("Room")

    # Floor: plank pattern via Brick texture (1.2 m x 0.14 m boards) + grain noise + bump.
    floor, nt, bsdf = _mat("Floor_Planks")
    coord = nt.nodes.new("ShaderNodeTexCoord")
    brick = nt.nodes.new("ShaderNodeTexBrick")
    brick.offset = 0.5
    brick.inputs["Color1"].default_value = (0.42, 0.26, 0.13, 1)
    brick.inputs["Color2"].default_value = (0.30, 0.17, 0.08, 1)
    brick.inputs["Mortar"].default_value = (0.03, 0.02, 0.01, 1)
    brick.inputs["Mortar Size"].default_value = 0.004
    brick.inputs["Brick Width"].default_value = 1.2
    brick.inputs["Row Height"].default_value = 0.14
    brick.inputs["Scale"].default_value = 1.0
    grain = nt.nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 18.0
    grain.inputs["Detail"].default_value = 8.0
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (1.0, 14.0, 1.0)   # stretch the grain along the boards
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.blend_type = 'MULTIPLY'
    mix.inputs[0].default_value = 0.6
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(coord.outputs["Object"], brick.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], grain.inputs["Vector"])
    nt.links.new(brick.outputs["Color"], mix.inputs[6])
    nt.links.new(grain.outputs["Color"], mix.inputs[7])
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nt.links.new(grain.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.38
    bpy.ops.mesh.primitive_plane_add(size=1, location=(2.0, -1.0, 0))
    fl = bpy.context.active_object
    fl.name = "Floor"
    fl.scale = (26, 16, 1)
    bpy.ops.object.transform_apply(scale=True)
    fl.data.materials.append(floor)
    bs.move_to_collection(fl, coll)

    # Plaster walls.
    wall, wnt, wb = _mat("Wall_Plaster")
    wb.inputs["Base Color"].default_value = (0.60, 0.53, 0.44, 1)
    wb.inputs["Roughness"].default_value = 0.85
    wn = wnt.nodes.new("ShaderNodeTexNoise")
    wn.inputs["Scale"].default_value = 60.0
    wbump = wnt.nodes.new("ShaderNodeBump")
    wbump.inputs["Strength"].default_value = 0.08
    wnt.links.new(wn.outputs["Fac"], wbump.inputs["Height"])
    wnt.links.new(wbump.outputs["Normal"], wb.inputs["Normal"])
    trim, _, tb = _mat("Trim_White")
    tb.inputs["Base Color"].default_value = (0.9, 0.89, 0.86, 1)
    tb.inputs["Roughness"].default_value = 0.5
    _box("Wall_Back", (26, 0.12, 3.2), (2.0, 3.2, 1.6), wall, coll)
    _box("Wall_Left", (0.12, 16, 3.2), (-4.5, -1.0, 1.6), wall, coll)
    _box("Ceiling", (26, 16, 0.12), (2.0, -1.0, 3.26), wall, coll)
    _box("Baseboard_Back", (26, 0.03, 0.14), (2.0, 3.12, 0.07), trim, coll)
    _box("Baseboard_Left", (0.03, 16, 0.14), (-4.42, -1.0, 0.07), trim, coll)

    # Daylight window on the left wall: glowing pane + white frame + cross bars.
    glass, gnt, gb = _mat("Window_Glow")
    gnt.nodes.remove(gb)
    em = gnt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.70, 0.84, 1.0, 1)
    em.inputs["Strength"].default_value = 3.5
    gnt.links.new(em.outputs["Emission"], gnt.nodes["Material Output"].inputs["Surface"])
    _box("Window_Pane", (0.02, 1.5, 1.7), (-4.43, 0.6, 1.55), glass, coll)
    for name, size, loc in (("Win_Top", (0.05, 1.66, 0.08), (-4.41, 0.6, 2.43)),
                            ("Win_Bottom", (0.05, 1.66, 0.08), (-4.41, 0.6, 0.67)),
                            ("Win_L", (0.05, 0.08, 1.7), (-4.41, -0.2, 1.55)),
                            ("Win_R", (0.05, 0.08, 1.7), (-4.41, 1.4, 1.55)),
                            ("Win_Mid_V", (0.05, 0.05, 1.7), (-4.41, 0.6, 1.55)),
                            ("Win_Mid_H", (0.05, 1.5, 0.05), (-4.41, 0.6, 1.55))):
        _box(name, size, loc, trim, coll)

    # Re-purpose the old studio lights: soft window key, warm bounce fill, dim back rim.
    key, fill, rim = (bpy.data.objects[n] for n in ("Key", "Fill", "Rim"))
    key.location, key.rotation_euler = (-4.0, 0.6, 1.55), (0, math.radians(-90), 0)
    key.data.shape, key.data.size, key.data.size_y = 'RECTANGLE', 1.5, 1.7
    key.data.energy, key.data.color = 380, (0.78, 0.88, 1.0)
    fill.location, fill.rotation_euler = (3.5, -4.5, 1.6), (math.radians(80), 0, math.radians(38))
    fill.data.size, fill.data.energy, fill.data.color = 3.0, 60, (1.0, 0.86, 0.7)
    rim.location, rim.rotation_euler = (1.5, 2.6, 2.4), (math.radians(115), 0, math.radians(-15))
    rim.data.energy = 70

    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.055, 0.07, 1)


def realistic_materials():
    def b(name):
        return bpy.data.materials[name].node_tree.nodes["Principled BSDF"]
    skin = b("Character_Skin")
    skin.inputs["Roughness"].default_value = 0.42
    skin.inputs["Subsurface Weight"].default_value = 0.12
    skin.inputs["Coat Weight"].default_value = 0.0
    skin.inputs["Base Color"].default_value = (0.05, 0.17, 0.55, 1)
    for n in ("Clay_Head", "Clay_Ear"):
        m = b(n)
        m.inputs["Roughness"].default_value = 0.55
        m.inputs["Subsurface Weight"].default_value = 0.2
        m.inputs["Subsurface Radius"].default_value = (1.0, 0.35, 0.15)
        m.inputs["Sheen Weight"].default_value = 0.4
    shade = b("Lamp_Shade_Plastic")
    shade.inputs["Roughness"].default_value = 0.8
    shade.inputs["Subsurface Weight"].default_value = 0.5
    metal = b("Lamp_Metal")
    metal.inputs["Roughness"].default_value = 0.22
    for name, mat in bpy.data.materials.items():
        pass


def setup_cycles(scene, samples=64):
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.cycles.denoiser = 'OPENIMAGEDENOISE'
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.max_bounces = 8
    scene.cycles.film_exposure = 1.0
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'
    except Exception as e:
        print("GPU setup failed, using CPU:", e)


def build():
    global CRE_PATH
    body, rig, lamp_path, CRE_PATH = stage_parts()
    scene = bpy.context.scene

    # Strip the Session 12/13 stage cameras and leftovers; keep ground + studio lights + world.
    for n in ("Cam_Front", "Cam_Side", "Cam_Front_Target", "Cam_Side_Target"):
        if n in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[n], do_unlink=True)
    for t in list(bpy.data.texts):
        bpy.data.texts.remove(t)

    scene.render.fps = FPS
    scene.frame_start, scene.frame_end = 1, END
    scene.render.resolution_x, scene.render.resolution_y = 1280, 720
    scene.render.resolution_percentage = 100
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'

    lamp_coll = bs.new_collection("Lamp")
    for o in append_objects(lamp_path, lambda n: n.startswith("Lamp_") or n == "Ridge_Offset"):
        lamp_coll.objects.link(o)

    a_coll = bs.new_collection("Character_A")
    bs.move_to_collection(rig, a_coll)
    bs.move_to_collection(body, a_coll)

    root = setup_mote()

    # Chain sits under the shade on the side A approaches from (south-west).
    toward_a = Vector((-0.707, -0.707, 0))
    chain_xy = (toward_a.x * 0.30, toward_a.y * 0.30)
    stop_xy, hand_z = solve_stop_position(rig, chain_xy)
    print("STOP_XY", tuple(stop_xy), "HAND_Z", hand_z)
    chain = make_chain(chain_xy, hand_z - GROUND_FIX)

    # Chair: A walks WALK_LEN from the lamp stop, then sits with feet FEET_FWD in front of the seat centre.
    u = Vector((math.sin(WALK_YAW), -math.cos(WALK_YAW)))
    fwd = Vector((math.sin(SIT_YAW), -math.cos(SIT_YAW)))
    feet = Vector((stop_xy.x, stop_xy.y)) + u * WALK_LEN
    make_chair(feet - fwd * FEET_FWD, SIT_YAW)

    x_start, disp = animate_keeper(rig, stop_xy)
    animate_mote(root)
    make_room(scene)
    realistic_materials()
    animate_lighting(scene, chain, chain.location.z)
    cams = setup_cameras(scene, lambda f: x_start + disp[f], bpy.data.objects["Creature_Head"])
    for name in ("S01", "S04", "S06"):
        d = cams[name].data.dof
        d.use_dof, d.focus_object, d.aperture_fstop = True, bpy.data.objects["Lamp_Shade"], 5.6
    setup_cycles(scene)

    # Placeholder VSE timeline (output disabled so 3D renders aren't replaced by colour blocks).
    scene.sequence_editor_create()
    cols = [(0.10, 0.12, 0.2), (0.12, 0.25, 0.2), (0.3, 0.2, 0.1), (0.25, 0.12, 0.25), (0.35, 0.25, 0.08), (0.15, 0.15, 0.15)]
    for i, (name, a, b) in enumerate(SHOTS):
        s = scene.sequence_editor.strips.new_effect(name, type='COLOR', channel=1 + (i % 2),
                                                    frame_start=a, length=b - a + 1)
        s.color = cols[i]
    scene.render.use_sequencer = False
    wav = ROOT + "/session-18/audio/lamp_keeper_audio.wav"
    if os.path.exists(wav):
        scene.sequence_editor.strips.new_sound("Audio - Lamp Keeper", wav, channel=5, frame_start=1)

    txt = bpy.data.texts.new("session-18-notes")
    txt.write(NOTES)
    bs.show_text(txt)
    scene.frame_set(1)
    bs.save(OUT)


# ------------------------------------------------------------------ checks (run on the saved .blend)
def _set_cam(scene, f):
    marks = sorted([m for m in scene.timeline_markers if m.frame <= f], key=lambda m: m.frame)
    scene.camera = marks[-1].camera


def _stitch(paths, cols, out_path):
    import numpy as np
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size
    rows = (len(imgs) + cols - 1) // cols
    canvas = np.zeros((rows * h, cols * w, 4), dtype=np.float32)
    for i, im in enumerate(imgs):
        px = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        r, c = divmod(i, cols)
        y0 = (rows - 1 - r) * h
        canvas[y0:y0 + h, c * w:(c + 1) * w, :] = px.reshape(h, w, 4)
    sheet = bpy.data.images.new("sheet", cols * w, rows * h)
    sheet.pixels.foreach_set(canvas.reshape(-1))
    sheet.filepath_raw = out_path
    sheet.file_format = 'PNG'
    sheet.save()


DENSE = (8, 24, 44, 56, 76, 94, 104, 116, 130, 136, 152, 180, 196, 206, 232, 250, 272, 284)


def dense(pct=33):
    """18 frames (3 per shot), 6 columns x 3 rows."""
    scene = bpy.context.scene
    scene.render.resolution_percentage = pct
    out_dir = ROOT + "/session-18/renders"
    paths = []
    for f in DENSE:
        scene.frame_set(f)
        _set_cam(scene, f)
        scene.render.filepath = f"/tmp/s18_dense_{f:03d}.png"
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
    _stitch(paths, 6, f"{out_dir}/contact_sheet_dense.png")
    print("DENSE_DONE")


def glow_still(frame=224):
    scene = bpy.context.scene
    scene.render.resolution_percentage = 100
    scene.frame_set(frame)
    _set_cam(scene, frame)
    scene.render.filepath = ROOT + "/session-18/renders/glow_moment_1280x720.png"
    bpy.ops.render.render(write_still=True)
    print("GLOW_DONE")


def check(frames=(24, 72, 114, 160, 214, 270), pct=50):
    scene = bpy.context.scene
    scene.render.resolution_percentage = pct
    out_dir = ROOT + "/session-18/renders"
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for f in frames:
        scene.frame_set(f)
        _set_cam(scene, f)
        scene.render.filepath = f"{out_dir}/check_f{f:03d}.png"
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
    _stitch(paths, 3, f"{out_dir}/shot_contact_sheet.png")
    print("CONTACT_SHEET_DONE")


def preview():
    scene = bpy.context.scene
    scene.render.resolution_percentage = 50
    scene.cycles.samples = 24
    r = scene.render
    # Audio is only mixed when the sequencer is on. With every colour placeholder muted and only the
    # sound strip left, Blender still renders the 3D scene as the picture.
    for st in scene.sequence_editor.strips_all:
        if st.type == 'COLOR':
            st.mute = True
    r.use_sequencer = True
    r.image_settings.media_type = 'VIDEO'
    r.image_settings.file_format = 'FFMPEG'
    r.ffmpeg.format = 'MPEG4'
    r.ffmpeg.codec = 'H264'
    r.ffmpeg.audio_codec = 'AAC'
    r.ffmpeg.audio_bitrate = 128
    r.ffmpeg.audio_mixrate = 44100
    r.ffmpeg.audio_channels = 'STEREO'
    r.filepath = ROOT + "/session-18/renders/preview.mp4"
    bpy.ops.render.render(animation=True)
    print("PREVIEW_DONE")


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    mode = args[0] if args else "build"
    if mode == "build":
        build()
    elif mode == "check":
        check(tuple(int(a) for a in args[1:]) or (24, 72, 114, 160, 214, 270))
    elif mode == "preview":
        preview()
    elif mode == "dense":
        dense()
    elif mode == "glow":
        glow_still(int(args[1]) if len(args) > 1 else 224)
