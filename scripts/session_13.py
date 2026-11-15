"""Session 13 -- Animating Rigged Objects. Session 12's character + a 24-frame in-place walk cycle.

Run: Blender --background --python scripts/session_13.py
Action 'Walk_Cycle' (fake user) is on Character_Rig; frame range 1-24, F-curves have Cycles modifiers.
"""
import os
import sys
import math
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs  # noqa: E402
import session_12 as s12  # noqa: E402

STRIDE = 0.25     # foot travel from centre, front/back (metres)
LIFT = 0.15       # foot lift at passing pose
KEYS = (1, 7, 13, 19, 25)  # frame 25 == frame 1, closes the loop


def key_loc(pb, frame, vec):
    s12.world_offset(pb, vec)
    pb.keyframe_insert("location", frame=frame)


def key_rot(pb, frame, euler):
    pb.rotation_euler = euler
    pb.keyframe_insert("rotation_euler", frame=frame)


def animate(rig):
    scene = bpy.context.scene
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 1, 24
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='POSE')
    pb = rig.pose.bones
    rad = math.radians

    # Feet (world offsets from rest; forward is -Y). Left foot: front contact at 1,
    # back at 13, lifted through the swing; right foot is half a cycle behind.
    left = {1: (-STRIDE, 0), 7: (0, 0), 13: (STRIDE, 0), 19: (0, LIFT), 25: (-STRIDE, 0)}
    right = {1: (STRIDE, 0), 7: (0, LIFT), 13: (-STRIDE, 0), 19: (0, 0), 25: (STRIDE, 0)}
    for f in KEYS:
        key_loc(pb["Foot_IK.L"], f, (0, left[f][0], left[f][1]))
        key_loc(pb["Foot_IK.R"], f, (0, right[f][0], right[f][1]))

    # Hips: bob (low at contact, high at passing), sway over the planted foot, twist.
    hip_z = {1: -0.06, 7: 0.0, 13: -0.06, 19: 0.0, 25: -0.06}
    hip_x = {1: 0.0, 7: 0.03, 13: 0.0, 19: -0.03, 25: 0.0}
    hip_twist = {1: rad(8), 7: 0, 13: rad(-8), 19: 0, 25: rad(8)}
    spine_twist = {k: -v * 1.2 for k, v in hip_twist.items()}
    for f in KEYS:
        key_loc(pb["Hips"], f, (hip_x[f], 0, hip_z[f]))
        key_rot(pb["Hips"], f, (0, hip_twist[f], 0))
        key_rot(pb["Spine"], f, (rad(3), spine_twist[f], 0))
        key_rot(pb["Head"], f, (0, -spine_twist[f] * 0.5, 0))

    # Arms swing opposite to the same-side leg. Forward is -Y, so -X rotation swings an arm
    # forward and +X swings it back. Left foot is forward at frame 1 -> left arm is back (+X).
    arm_l = {1: rad(28), 7: 0, 13: rad(-28), 19: 0, 25: rad(28)}
    arm_r = {k: -v for k, v in arm_l.items()}
    elbow = lambda a: -(rad(15) + max(0, -a) * 0.9)   # -X flexes the forearm forward; more on the forward swing
    for f in KEYS:
        key_rot(pb["UpperArm.L"], f, (arm_l[f], 0, 0))
        key_rot(pb["UpperArm.R"], f, (arm_r[f], 0, 0))
        key_rot(pb["LowerArm.L"], f, (elbow(arm_l[f]), 0, 0))
        key_rot(pb["LowerArm.R"], f, (elbow(arm_r[f]), 0, 0))

    bpy.ops.object.mode_set(mode='OBJECT')
    act = rig.animation_data.action
    act.name = "Walk_Cycle"
    act.use_fake_user = True

    # Blender 5.x layered actions: curves live in a channelbag, not action.fcurves.
    slot = rig.animation_data.action_slot
    cb = act.layers[0].strips[0].channelbag(slot)
    for fc in cb.fcurves:
        is_foot_y = "Foot_IK" in fc.data_path and fc.data_path.endswith("location") and fc.array_index == 1
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR' if is_foot_y else 'BEZIER'
            if not is_foot_y:
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'
        fc.modifiers.new('CYCLES')
        fc.update()
    scene.frame_set(1)


NOTES = """Session 13 -- Animating Rigged Objects
======================================
Character_Rig already carries a 24-frame in-place walk cycle (action 'Walk_Cycle').
Press Space to play. The F-curves have a Cycles modifier, so it loops forever.

What's keyed (frames 1, 7, 13, 19, 25 -- frame 25 repeats frame 1 to close the loop)
- Foot_IK.L / .R  : forward/back + lift. Feet are half a cycle apart.
- Hips            : down at contact, up at passing, sways over the planted foot, twists.
- Spine / Head    : counter-twist. UpperArm / LowerArm: opposite-leg swing.

Try this
1. Open an Animation workspace tab (your duplicated tab works) and a Graph Editor.
2. Select Foot_IK.L in Pose Mode and look at its curves; the Y curve is linear on purpose
   (planted foot slides back at constant speed), Z is smooth.
3. Make it a jog: scale the Y stride up and set frame_end lower; or add a head bob.
4. Add 'breakdown' keys at frames 4, 10, 16, 22 for softer contacts.
5. Walk-in-place is root-motion free. To travel, key the Root bone's Y over time.
"""


def build(save_file=True):
    body, rig = s12.build_character(False)
    animate(rig)
    for t in list(bpy.data.texts):
        bpy.data.texts.remove(t)
    txt = bpy.data.texts.new("session-13-notes")
    txt.write(NOTES)
    bs.show_text(txt)
    if save_file:
        bs.save("session-13/session-13-start.blend")
    return body, rig


def filmstrip(out="session-13/renders/walk_filmstrip.png", frames=(1, 5, 9, 13, 17, 21)):
    """Render frames from the saved .blend through Cam_Side and stitch them into one strip."""
    import numpy as np
    scene = bpy.context.scene
    scene.render.resolution_x, scene.render.resolution_y = 300, 420
    scene.render.resolution_percentage = 100
    scene.camera = bpy.data.objects["Cam_Side"]
    paths = []
    for f in frames:
        scene.frame_set(f)
        scene.render.filepath = f"/tmp/s13_fs_{f:02d}.png"
        bpy.ops.render.render(write_still=True)
        paths.append(scene.render.filepath)
    imgs = [bpy.data.images.load(p) for p in paths]
    w, h = imgs[0].size
    canvas = np.zeros((h, w * len(imgs), 4), dtype=np.float32)
    for i, im in enumerate(imgs):
        px = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(px)
        canvas[:, i * w:(i + 1) * w, :] = px.reshape(h, w, 4)
    sheet = bpy.data.images.new("strip", w * len(imgs), h)
    sheet.pixels.foreach_set(canvas.reshape(-1))
    sheet.filepath_raw = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), out)
    sheet.file_format = 'PNG'
    sheet.save()


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args and args[0] == "filmstrip":
        filmstrip()
    else:
        build(True)
