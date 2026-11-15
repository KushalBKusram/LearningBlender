"""Session 11 -- Intro to Animation: bouncing ball with squash/stretch and timing.

Run: Blender --background --python scripts/session_11.py
Keyframes: location X/Z and scale on 'Bounce_Ball' (key frames 1-72, plays 1-71 @ 24 fps).
A looping hop: rest -> anticipation squash -> big hop -> two smaller hops -> settle -> rest.
Z/scale F-curves get Cycles modifiers (REPEAT) and X gets REPEAT_OFFSET, so the ball
keeps hopping forward forever; frame 72 equals frame 1 in pose, so playback ends at 71.
Peaks use auto-clamped ease handles; contact/stretch keys use vector handles so impacts
stay snappy rather than floaty.
"""
import os
import sys
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs

OUT = "session-11/session-11-start.blend"
R = 0.4

# frame, x, z(center), scale(x,y,z), kind  (kind: 'ease' for peaks/rest, 'snap' for impact keys)
KEYS = [
    (1,  -2.4, 0.40, (1.0, 1.0, 1.0),    'ease'),   # rest on the ground
    (6,  -2.4, 0.28, (1.18, 1.18, 0.7),  'snap'),   # anticipation: crouch down
    (10, -2.4, 0.52, (0.85, 0.85, 1.3),  'snap'),   # launch: stretched, leaving ground
    (22, -1.2, 1.60, (1.0, 1.0, 1.0),    'ease'),   # peak of the big hop
    (32, -0.3, 0.50, (0.88, 0.88, 1.25), 'snap'),   # stretched just before contact
    (34,  0.0, 0.24, (1.3, 1.3, 0.6),    'snap'),   # contact: full squash
    (36,  0.3, 0.50, (0.88, 0.88, 1.25), 'snap'),   # stretched leaving the ground
    (44,  1.1, 0.95, (1.0, 1.0, 1.0),    'ease'),   # peak of the second hop
    (50,  1.75, 0.55, (0.92, 0.92, 1.18), 'snap'),  # stretch before 2nd contact
    (52,  1.9, 0.29, (1.15, 1.15, 0.72), 'snap'),   # 2nd contact (smaller squash)
    (54,  2.0, 0.50, (0.94, 0.94, 1.1),  'snap'),   # stretch leaving
    (58,  2.1, 0.62, (1.0, 1.0, 1.0),    'ease'),   # tiny third hop peak
    (62,  2.2, 0.37, (1.05, 1.05, 0.92), 'snap'),   # tiny contact
    (66,  2.4, 0.40, (1.0, 1.0, 1.0),    'ease'),   # settle
    (72,  2.4, 0.40, (1.0, 1.0, 1.0),    'ease'),   # rest (same pose as frame 1 -> loop point)
]


def set_interpolation(ball):
    slot = ball.animation_data.action_slot
    cb = ball.animation_data.action.layers[0].strips[0].channelbag(slot)
    kind_by_frame = {k[0]: k[4] for k in KEYS}
    for fc in cb.fcurves:
        for kp in fc.keyframe_points:
            kind = kind_by_frame.get(round(kp.co.x), 'ease')
            if fc.data_path == "location" and fc.array_index == 0:
                kp.interpolation = 'LINEAR'          # constant forward travel
                continue
            kp.interpolation = 'BEZIER'
            h = 'VECTOR' if kind == 'snap' else 'AUTO_CLAMPED'
            kp.handle_left_type = kp.handle_right_type = h
        mod = fc.modifiers.new('CYCLES')
        # X keeps travelling forward each cycle; Z and scale just repeat.
        mod.mode_before = mod.mode_after = 'REPEAT_OFFSET' if (fc.data_path == "location" and fc.array_index == 0) else 'REPEAT'
        fc.update()


def add_contact_shadow(ball):
    """Soft blob shadow on the ground that follows the ball and shrinks/fades as it rises."""
    bpy.ops.mesh.primitive_plane_add(size=2.4, location=(ball.location.x, 0, 0.004))
    sh = bpy.context.active_object
    sh.name = "Contact_Shadow"
    sh.hide_select = True
    con = sh.constraints.new('COPY_LOCATION')
    con.target = ball
    con.use_z = False

    mat = bpy.data.materials.new("Contact_Shadow_Mat")
    mat.use_nodes = True
    try:
        mat.surface_render_method = 'BLENDED'
    except (AttributeError, TypeError):
        pass
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (2, 2, 0)   # flat plane: ignore Generated Z
    mp.inputs["Location"].default_value = (-1, -1, 0)
    grad = nt.nodes.new("ShaderNodeTexGradient")
    grad.gradient_type = 'QUADRATIC_SPHERE'
    mul = nt.nodes.new("ShaderNodeMath")
    mul.operation = 'MULTIPLY'
    mul.inputs[1].default_value = 1.6
    dark = nt.nodes.new("ShaderNodeBsdfDiffuse")
    dark.inputs["Color"].default_value = (0, 0, 0, 1)
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(tc.outputs["Generated"], mp.inputs["Vector"])
    nt.links.new(mp.outputs["Vector"], grad.inputs["Vector"])
    nt.links.new(grad.outputs["Fac"], mul.inputs[0])
    nt.links.new(mul.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[1])
    nt.links.new(dark.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    sh.data.materials.append(mat)
    sh.visible_shadow = False

    # drivers: height above rest (ball z - 0.4 * scale_z -> use location z) shrinks/fades the blob
    def drive(fcurve, expr):
        d = fcurve.driver
        d.type = 'SCRIPTED'
        var = d.variables.new()
        var.name = "z"
        var.type = 'TRANSFORMS'
        var.targets[0].id = ball
        var.targets[0].transform_type = 'LOC_Z'
        d.expression = expr
    for i in (0, 1):
        drive(sh.driver_add("scale", i), "1.0/(1.0+max(0.0,z-0.4)*0.9)")
    drive(mat.node_tree.driver_add('nodes["Math"].inputs[1].default_value'),
          "1.6/(1.0+max(0.0,z-0.4)*1.0)")
    return sh


def build():
    bs.clear_scene()
    scn = bpy.context.scene
    scn.frame_start, scn.frame_end = 1, 71
    scn.render.fps = 24

    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=R, location=(-2.4, 0, 2.4))
    ball = bpy.context.active_object
    ball.name = "Bounce_Ball"
    bpy.ops.object.shade_smooth()
    ball.data.materials.append(bs.make_material("Ball_Red", (0.8, 0.08, 0.06), roughness=0.25))

    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    gmat = bs.make_material("Ground_Warm", (0.75, 0.68, 0.58), roughness=0.8)
    nt = gmat.node_tree
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Scale"].default_value = 6.0
    chk.inputs["Color1"].default_value = (0.82, 0.76, 0.66, 1)
    chk.inputs["Color2"].default_value = (0.52, 0.46, 0.38, 1)
    nt.links.new(chk.outputs["Color"], nt.nodes.get("Principled BSDF").inputs["Base Color"])
    ground.data.materials.append(gmat)

    for frame, x, z, scale, _ in KEYS:
        scn.frame_set(frame)
        ball.location = (x, 0, z)
        ball.scale = scale
        ball.keyframe_insert(data_path="location", frame=frame)
        ball.keyframe_insert(data_path="scale", frame=frame)
    set_interpolation(ball)
    add_contact_shadow(ball)
    scn.frame_set(1)

    bs._studio_lighting(scn)
    cam, _ = bs._aimed_camera("Camera", (0, -7.0, 3.6), (0, 0, 0.6), 35)
    scn.camera = cam

    txt = bpy.data.texts.new("session-11-notes")
    txt.write(
        "Session 11 -- Intro to Animation\n"
        "---------------------------------\n"
        "Bounce_Ball is keyframed (24 fps): location + scale. It starts at rest, does an\n"
        "anticipation squash (frames 1-10), launches, then makes three shrinking hops and\n"
        "settles by frame 66. Cycles modifiers loop it, with X moving on every repeat.\n"
        "Press Space in the 3D viewport to play. Things to study:\n"
        "1. Timeline: diamonds are keyframes. Frame 6 is the anticipation crouch; frames\n"
        "   32/34/36 are stretch -> squash -> stretch around the first impact; 50/52/54\n"
        "   repeat it smaller. 'Contact_Shadow' shrinks and fades as the ball rises.\n"
        "2. Switch to the Animation workspace and open the Graph Editor: select the ball,\n"
        "   look at Z Location. Peaks have smooth ease handles; impact keys use sharp\n"
        "   (vector) handles. Select a key and press T to change interpolation/easing.\n"
        "3. Try it: move the frame-12 key to frame 13 (slower fall), or change the squash\n"
        "   scale values, and notice how the 'weight' of the ball changes.\n"
        "4. Volume rule: when Z scale goes down, X/Y scale goes up so volume feels constant.\n"
        "Deliverable: your own bouncing-ball variation (heavier, lighter, rubbery).\n"
    )
    bs.show_text(txt)
    bs.save(OUT)


if __name__ == "__main__":
    build()
