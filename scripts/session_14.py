"""Session 14 -- Particles & Physics Basics.

Run: Blender --background --python scripts/session_14.py
Builds session-14/session-14-start.blend: rigid-body tower + wrecking ball on the
left (baked), confetti particle emitter on the right.
"""
import os
import sys
import math
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs

SESSION_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session-14")


def active_rigid(obj, kind, **kw):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.rigidbody.object_add(type=kind)
    rb = obj.rigid_body
    for k, v in kw.items():
        setattr(rb, k, v)


def build():
    bs.clear_scene()
    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 60

    # Ground: passive rigid body + collision for particles.
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(bs.make_material("Ground_Mat", (0.7, 0.66, 0.6), roughness=0.8))
    active_rigid(ground, 'PASSIVE', friction=0.8)
    ground.modifiers.new("Collision", 'COLLISION')

    # --- (a) Rigid bodies: a 3-layer cube tower and a wrecking ball.
    colors = [(0.8, 0.2, 0.2), (0.2, 0.5, 0.8), (0.9, 0.7, 0.2)]
    colors = colors + [(0.3, 0.7, 0.4), (0.7, 0.3, 0.8)]
    mats = [bs.make_material(f"Block_{i}", c, roughness=0.5) for i, c in enumerate(colors)]
    size = 0.5
    for layer in range(5):
        for i in range(2):
            for j in range(2):
                bpy.ops.mesh.primitive_cube_add(
                    size=size,
                    location=(-2.5 + i * size * 1.02, j * size * 1.02 - 0.25, size / 2 + layer * size * 1.01))
                cube = bpy.context.active_object
                cube.name = f"Block_L{layer}_{i}{j}"
                cube.data.materials.append(mats[layer])
                active_rigid(cube, 'ACTIVE', mass=0.5, friction=0.5)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.35, location=(-6.0, 0, 1.0))
    ball = bpy.context.active_object
    ball.name = "Wrecking_Ball"
    ball.data.materials.append(bs.make_material("Ball_Mat", (0.15, 0.15, 0.18), metallic=0.9, roughness=0.3))
    bpy.ops.object.shade_smooth()
    active_rigid(ball, 'ACTIVE', mass=8.0, friction=0.5)
    ball.rigid_body.linear_damping = 0.0
    # Initial shove toward the tower is applied by keyframing the Animated flag:
    # animated until frame 6 (moves along a path), then released to physics.
    ball.rigid_body.kinematic = True
    ball.keyframe_insert(data_path="rigid_body.kinematic", frame=1)
    for f, x, z in ((1, -6.0, 0.9), (6, -3.5, 0.5)):
        ball.location = (x, 0, z)
        ball.keyframe_insert(data_path="location", frame=f)
    ball.rigid_body.kinematic = False
    ball.keyframe_insert(data_path="rigid_body.kinematic", frame=7)

    rbw = scn.rigidbody_world
    rbw.substeps_per_frame = 30
    rbw.solver_iterations = 30
    rbw.point_cache.frame_start = 1
    rbw.point_cache.frame_end = 60

    # --- (b) Confetti particles: emitter plane overhead, small cube instances.
    bpy.ops.mesh.primitive_plane_add(size=3.5, location=(2.8, 0, 3.2))
    emitter = bpy.context.active_object
    emitter.name = "Confetti_Emitter"

    bpy.ops.mesh.primitive_cube_add(size=0.22, location=(0, 0, -30))
    chip = bpy.context.active_object
    chip.name = "Confetti_Chip"
    chip.scale = (1, 1, 0.12)
    chip.data.materials.append(bs.make_material("Chip_Mat", (0.95, 0.35, 0.55), roughness=0.4))

    bpy.context.view_layer.objects.active = emitter
    bpy.ops.object.particle_system_add()
    ps = emitter.particle_systems[-1]
    ps.name = "Confetti"
    st = ps.settings
    st.count = 250
    st.frame_start = 1
    st.frame_end = 30
    st.lifetime = 200
    st.emit_from = 'FACE'
    st.normal_factor = 0.0
    st.object_align_factor = (0, 0, 0)
    st.render_type = 'OBJECT'
    st.instance_object = chip
    st.particle_size = 1.0
    st.size_random = 0.4
    st.use_rotations = True
    st.rotation_mode = 'NONE'
    st.angular_velocity_mode = 'RAND'
    st.angular_velocity_factor = 6.0
    st.phase_factor_random = 2.0
    st.physics_type = 'NEWTON'
    st.mass = 0.05
    st.drag_factor = 0.25
    st.use_dynamic_rotation = False
    st.effector_weights.gravity = 1.0
    st.factor_random = 0.5
    emitter.particle_systems[-1].point_cache.frame_end = 60

    # Pick up chip texture color variety by instancing the same object only; the
    # colored chips come from Chip_Mat. Hide the source chip from render.
    emitter.show_instancer_for_render = False

    # --- Camera, lights, world.
    bs._studio_lighting(scn)
    bs._set_world(scn, (0.55, 0.58, 0.65), 0.7)
    cam, _ = bs._aimed_camera("Camera", (0.0, -9.5, 3.0), (0.0, 0, 1.3), 28)
    scn.camera = cam
    bpy.context.view_layer.objects.active = None

    txt = bpy.data.texts.new("session-14-notes")
    txt.write(
        "Session 14 -- Particles & Physics\n"
        "---------------------------------\n"
        "Left: a 12-block tower (Rigid Body: Active) and a heavy wrecking ball. The ball is\n"
        "'Animated' for frames 1-6 (kinematic keyframes) then released to physics. The\n"
        "Ground is a Passive rigid body. The simulation is already baked (Physics tab >\n"
        "Rigid Body World > Cache). Press Space or scrub the timeline to watch it.\n\n"
        "Right: Confetti_Emitter drops 250 chip instances (Particles tab > Confetti).\n"
        "Try: change Count, Lifetime, Gravity weight, Mass, or swap the instance object.\n"
        "To re-simulate after edits: Physics > Rigid Body World > Cache > Delete Bake, Bake.\n"
        "Both caches live inside this .blend (memory cache, no external folder). After\n"
        "reopening you may see 'cache is outdated' in the cache panel: that is just a\n"
        "load-time flag; the bake still plays back. Re-bake whenever you change settings.\n"
    )
    bs.show_text(txt)


def bake_rigid_body():
    scn = bpy.context.scene
    # Step through the frames in order so the rigid-body cache fills, then bake.
    for f in range(scn.frame_start, scn.frame_end + 1):
        scn.frame_set(f)
    try:
        override = {"scene": scn, "point_cache": scn.rigidbody_world.point_cache}
        with bpy.context.temp_override(**override):
            bpy.ops.ptcache.bake(bake=True)
        print("BAKED rigid body:", scn.rigidbody_world.point_cache.is_baked)
    except Exception as e:
        print("bake op failed, relying on stepped cache:", e)
    scn.frame_set(1)


if __name__ == "__main__":
    build()
    bake_rigid_body()
    bs.save("session-14/session-14-start.blend")
