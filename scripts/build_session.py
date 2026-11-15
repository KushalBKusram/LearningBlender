"""
Builds a starter .blend file for one session of the Learning Blender program.

Usage (headless):
  /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/build_session.py -- <N>

Where <N> is 1-18. Each build_NN() function sets up the scaffolding (collections,
base meshes, modifier stacks, cameras, lights, armatures, timelines, etc.) called
for by that session's brief. Hands-on technique (sculpting strokes, final posing,
material tweaks, the final edit) is left for you to do in Blender -- these files
are a running start, not the finished homework.
"""
import os
import bpy
import bmesh
import sys
import math
from mathutils import Vector

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_collection(name, parent=None):
    coll = bpy.data.collections.new(name)
    (parent or bpy.context.scene.collection).children.link(coll)
    return coll


def move_to_collection(obj, coll):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    coll.objects.link(obj)


def add_camera(location, rotation, name="Camera"):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.scene.collection.objects.link(cam)
    cam.location = location
    cam.rotation_euler = rotation
    return cam


def add_sun(name="Sun", energy=2.0, rotation=(0.6, 0.2, 0.3)):
    light_data = bpy.data.lights.new(name, type='SUN')
    light_data.energy = energy
    light = bpy.data.objects.new(name, light_data)
    bpy.context.scene.collection.objects.link(light)
    light.rotation_euler = rotation
    return light


def show_text(txt):
    """Point every Text Editor area (the Scripting tab's, by default) at this
    text block and switch the active workspace to Scripting, so the notes are
    visible immediately on opening the file -- no hunting for them."""
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'TEXT_EDITOR':
                for space in area.spaces:
                    if space.type == 'TEXT_EDITOR':
                        space.text = txt
                        space.top = 0
    scripting_ws = bpy.data.workspaces.get("Scripting")
    if scripting_ws:
        for window in bpy.context.window_manager.windows:
            window.workspace = scripting_ws


def save(filename):
    path = f"{ROOT}/{filename}"
    bpy.ops.wm.save_as_mainfile(filepath=path)
    # Store external media (movie/sound/image strips) relative to the .blend so the repo is portable.
    bpy.ops.file.make_paths_relative()
    bpy.ops.wm.save_as_mainfile(filepath=path)
    print(f"SAVED: {path}")


def make_material(name, base_color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base_color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


# ---------------------------------------------------------------- Session 1
def build_01():
    clear_scene()
    scn = bpy.context.scene
    ref = new_collection("Reference")
    props = new_collection("Props")
    wip = new_collection("WIP")
    cam = add_camera((4, -4, 2.5), (math.radians(70), 0, math.radians(45)))
    move_to_collection(cam, props)
    sun = add_sun()
    move_to_collection(sun, props)

    txt = bpy.data.texts.new("session-01-notes")
    txt.write(
        "Session 1 -- Onboarding & Interface\n"
        "------------------------------------\n"
        "This file is a tidy, empty sandbox: three collections (Reference, Props, WIP),\n"
        "a camera and a sun light already placed.\n\n"
        "Your job this session is NOT to add objects -- it's to get comfortable:\n"
        "1. Practice orbit/pan/zoom (middle-mouse drag, shift+middle-mouse, scroll).\n"
        "2. Switch between the Layout, Modeling, and Animation workspace tabs at the top.\n"
        "3. Duplicate one workspace tab and rearrange its editors into a layout you like.\n"
        "4. Save this file -- that save IS the deliverable for Session 1.\n"
    )
    show_text(txt)
    save("session-01/session-01-start.blend")


# ---------------------------------------------------------------- Session 2
def build_02():
    clear_scene()
    coll = new_collection("StillLife")
    specs = [
        ("mesh.primitive_cube_add", dict(size=1, location=(-2, 0, 0.5))),
        ("mesh.primitive_uv_sphere_add", dict(radius=0.6, location=(-1, 1, 0.6))),
        ("mesh.primitive_cylinder_add", dict(radius=0.5, depth=1.2, location=(0.5, -0.5, 0.6))),
        ("mesh.primitive_cone_add", dict(radius1=0.6, depth=1.2, location=(2, 0.5, 0.6))),
        ("mesh.primitive_torus_add", dict(major_radius=0.6, minor_radius=0.2, location=(0, 2, 0.3))),
    ]
    for op_name, kwargs in specs:
        getattr(bpy.ops, op_name.split(".")[0])
        op = bpy.ops
        for part in op_name.split("."):
            op = getattr(op, part)
        op(**kwargs)
        move_to_collection(bpy.context.active_object, coll)

    bpy.ops.mesh.primitive_plane_add(size=10, location=(0, 0, 0))
    move_to_collection(bpy.context.active_object, coll)
    bpy.context.active_object.name = "Ground"

    add_camera((6, -7, 4), (math.radians(60), 0, math.radians(40)))
    add_sun()
    save("session-02/session-02-start.blend")


# ---------------------------------------------------------------- Session 3
def build_03():
    clear_scene()
    coll = new_collection("Props")

    # Outer body: short, wide cylinder (mug proportions, not a test tube).
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.5, depth=0.6, location=(0, 0, 0.3))
    body = bpy.context.active_object
    body.name = "Mug_Body"

    # Hollow it with a Boolean difference -- far more reliable than hand-rolled
    # bmesh inset/extrude, and leaves a visible open top + a solid base.
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.38, depth=0.6, location=(0, 0, 0.35))
    cutter = bpy.context.active_object
    cutter.name = "Mug_Cutter"

    mod = body.modifiers.new("Hollow", 'BOOLEAN')
    mod.operation = 'DIFFERENCE'
    mod.object = cutter
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(cutter, do_unlink=True)

    # Handle: a torus rotated about X so its ring actually reaches out in X/Z
    # (a vertical loop facing the camera edge-on, like a real handle) instead
    # of lying flat as a thin disc against the wall. Its near edge sits a few
    # cm inside the solid wall (never into the hollow cavity), then it's
    # fused to the body with a Boolean UNION for one continuous watertight
    # mesh -- actually connected on every side, not just visually overlapping.
    body_outer_radius = 0.5
    major_radius = 0.18
    minor_radius = 0.045
    embed_depth = 0.08  # how far the near edge sits inside the outer wall surface
    near_edge_x = body_outer_radius - embed_depth
    center_x = near_edge_x + major_radius + minor_radius
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius, major_segments=20, minor_segments=10,
        location=(center_x, 0, 0.3))
    handle = bpy.context.active_object
    handle.name = "Mug_Handle"
    handle.rotation_euler = (math.radians(90), 0, 0)

    union_mod = body.modifiers.new("Attach_Handle", 'BOOLEAN')
    union_mod.operation = 'UNION'
    union_mod.object = handle
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=union_mod.name)
    bpy.data.objects.remove(handle, do_unlink=True)

    body.name = "Mug"
    move_to_collection(body, coll)

    add_camera((1.8, -2.2, 1.1), (math.radians(72), 0, math.radians(40)))
    add_sun()
    save("session-03/session-03-start.blend")


# ---------------------------------------------------------------- Session 4
def build_04(save_file=True):
    clear_scene()
    coll = new_collection("Lamp")

    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 0.1))
    base = bpy.context.active_object
    base.name = "Lamp_Base"
    bevel = base.modifiers.new("Bevel", 'BEVEL')
    bevel.width = 0.02
    bevel.segments = 3
    move_to_collection(base, coll)

    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=1.2, location=(0, 0, 0.8))
    pole = bpy.context.active_object
    pole.name = "Lamp_Pole"
    move_to_collection(pole, coll)

    # Classic lampshade: a cylinder given several rings along its height, then
    # each ring's radius is set from a profile (tapered drum with a flared rim).
    # The extra rings anchor the silhouette so Subsurf smooths it instead of
    # ballooning it into a ball (a plain cone only has two rings).
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.4, depth=0.5, location=(0, 0, 1.6))
    shade = bpy.context.active_object
    shade.name = "Lamp_Shade"
    bm = bmesh.new()
    bm.from_mesh(shade.data)
    vert_edges = [e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 1e-4]
    bmesh.ops.subdivide_edges(bm, edges=vert_edges, cuts=5, use_grid_fill=True)
    for v in bm.verts:
        t = (v.co.z + 0.25) / 0.5            # 0 at the rim, 1 at the top
        r = 0.44 - 0.17 * t                   # straight taper
        r += 0.035 * max(0.0, 1.0 - t / 0.12) ** 2   # flared lower lip
        ang = math.atan2(v.co.y, v.co.x)
        v.co.x, v.co.y = r * math.cos(ang), r * math.sin(ang)
    bm.to_mesh(shade.data)
    bm.free()
    for poly in shade.data.polygons:
        poly.use_smooth = True
    sub = shade.modifiers.new("Subsurf", 'SUBSURF')
    sub.levels = 1
    shade.modifiers.new("Bevel", 'BEVEL').width = 0.008
    move_to_collection(shade, coll)

    # Object-offset Array rotates copies around the EMPTY's origin only if the
    # arrayed object's own origin also sits at that same pivot (with its mesh
    # geometry offset off-center) -- otherwise each copy's relative transform
    # includes a translation that compounds every iteration and spirals the
    # copies away from the base instead of ringing them around it.
    offset_empty = bpy.data.objects.new("Ridge_Offset", None)
    bpy.context.scene.collection.objects.link(offset_empty)
    offset_empty.rotation_euler = (0, 0, math.radians(30))
    offset_empty.location = (0, 0, 0.1)
    move_to_collection(offset_empty, coll)

    bpy.ops.mesh.primitive_cube_add(size=0.07, location=(0.52, 0, 0.1))
    ridge = bpy.context.active_object
    ridge.name = "Lamp_Base_Ridge"
    bpy.context.scene.cursor.location = (0, 0, 0.1)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    arr = ridge.modifiers.new("Array", 'ARRAY')
    arr.count = 12
    arr.use_relative_offset = False
    arr.use_object_offset = True
    arr.offset_object = offset_empty
    move_to_collection(ridge, coll)

    # Mirror modifier demo: model only the +X half of a bracket bar under the
    # shade (origin sits on the pole axis), and let Mirror build the -X half.
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.07, 0, 1.33))
    collar = bpy.context.active_object
    collar.name = "Lamp_Collar_Mirror"
    collar.scale = (0.14, 0.06, 0.05)
    bpy.ops.object.transform_apply(scale=True)
    bpy.context.scene.cursor.location = (0, 0, 1.33)
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    mir = collar.modifiers.new("Mirror", 'MIRROR')
    mir.use_axis = (True, False, False)
    mir.use_clip = True
    collar.modifiers.new("Bevel", 'BEVEL').width = 0.008
    move_to_collection(collar, coll)

    root = bpy.data.objects.new("Lamp_Root", None)
    bpy.context.scene.collection.objects.link(root)
    move_to_collection(root, coll)
    for obj in (base, pole, shade, ridge, collar):
        obj.parent = root

    add_camera((3.5, -4.2, 1.75), (math.radians(76), 0, math.radians(40)))
    add_sun()
    if save_file:
        save("session-04/session-04-start.blend")


# ---------------------------------------------------------------- Session 5
def _studio_world(scene, backdrop=(0.42, 0.43, 0.47), name=None):
    """Studio world with a contrasty reflection environment for metals (dark
    floor, bright horizon band, mid-gray sky) but a calm flat backdrop for
    anything seen directly by the camera."""
    w = bpy.data.worlds.new(name or f"Studio_World_{scene.name}")
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs["Strength"].default_value = 1.0
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    cr = ramp.color_ramp
    cr.elements[0].position, cr.elements[0].color = 0.0, (0.06, 0.055, 0.05, 1)   # floor bounce
    cr.elements[1].position, cr.elements[1].color = 1.0, (0.5, 0.55, 0.65, 1)     # sky
    e = cr.elements.new(0.3); e.color = (0.1, 0.095, 0.09, 1)
    e = cr.elements.new(0.45); e.color = (0.22, 0.22, 0.22, 1)
    e = cr.elements.new(0.5); e.color = (1.5, 1.5, 1.45, 1)                       # bright softbox band
    e = cr.elements.new(0.57); e.color = (0.18, 0.19, 0.21, 1)
    e = cr.elements.new(0.8); e.color = (0.35, 0.38, 0.45, 1)
    cam_ray = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = 'RGBA'
    mix.inputs[7].default_value = (*backdrop, 1)    # B: what the camera sees
    nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"])
    # World "Generated" coords are the unit view direction (z in -1..1), so
    # remap to 0..1 before feeding the ramp: 0.5 = horizon.
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = -1.0
    remap.inputs["From Max"].default_value = 1.0
    nt.links.new(sep.outputs["Z"], remap.inputs["Value"])
    nt.links.new(remap.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(cam_ray.outputs["Is Camera Ray"], mix.inputs[0])
    nt.links.new(ramp.outputs["Color"], mix.inputs[6])   # A: reflections/lighting
    nt.links.new(mix.outputs[2], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])
    scene.world = w
    return w


def build_05(save_file=True):
    build_04(False)
    base = bpy.data.objects["Lamp_Base"]
    pole = bpy.data.objects["Lamp_Pole"]
    shade = bpy.data.objects["Lamp_Shade"]
    ridge = bpy.data.objects["Lamp_Base_Ridge"]

    metal = make_material("Lamp_Metal", (0.92, 0.88, 0.8), metallic=1.0, roughness=0.18)
    plastic = make_material("Lamp_Shade_Plastic", (0.9, 0.85, 0.7), metallic=0.0, roughness=0.4)
    accent = make_material("Lamp_Ridge_Accent", (0.8, 0.1, 0.1), metallic=0.8, roughness=0.25)

    collar = bpy.data.objects["Lamp_Collar_Mirror"]
    for obj, mat in ((base, metal), (pole, metal), (collar, metal), (shade, plastic), (ridge, accent)):
        obj.data.materials.append(mat)

    # Metal only reads as metal when it has something to reflect -- give the
    # scene a contrasty studio environment (see _studio_world).
    _studio_world(bpy.context.scene, name="Studio_World")
    bpy.context.scene.camera = bpy.data.objects["Camera"]

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    ground.data.materials.append(make_material("Ground_Warm", (0.55, 0.5, 0.44), roughness=0.8))

    if save_file:
        save("session-05/session-05-start.blend")


# ---------------------------------------------------------------- Session 6
def _lamp_stand_in():
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.2, location=(0, 0, 0.1))
    base = bpy.context.active_object
    base.name = "Lamp_Base"
    bpy.ops.mesh.primitive_cone_add(radius1=0.4, radius2=0.25, depth=0.5, location=(0, 0, 1.0))
    shade = bpy.context.active_object
    shade.name = "Lamp_Shade"
    return [base, shade]


def _set_world(scene, color, strength):
    w = bpy.data.worlds.new(f"World_{scene.name}")
    w.use_nodes = True
    bg = w.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (*color, 1)
    bg.inputs["Strength"].default_value = strength
    scene.world = w


def _add_light(scene, name, kind, energy, loc, rot=(0, 0, 0), color=(1, 1, 1), size=None, spot=None):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if size is not None:
        data.size = size
    if spot is not None:
        data.spot_size = math.radians(spot)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def build_06():
    build_05(False)
    bpy.data.objects.remove(bpy.data.objects["Sun"], do_unlink=True)
    scn = bpy.context.scene
    scn.name = "Scene_Studio"
    cam_loc = bpy.data.objects["Camera"].location.copy()

    # Duplicate the scene twice (linked objects, so the lamp stays in sync).
    # bpy.data.scenes is name-sorted, so find the new scene by set difference.
    def dup_scene(new_name):
        before = set(bpy.data.scenes)
        bpy.ops.scene.new(type='LINK_COPY')
        new = (set(bpy.data.scenes) - before).pop()
        new.name = new_name
        return new

    studio = scn
    dramatic = dup_scene("Scene_Dramatic")
    outdoor = dup_scene("Scene_Outdoor")

    # 1. Studio: classic three-point, soft neutral backdrop.
    _studio_world(studio)
    _add_light(studio, "Key", 'AREA', 500, (3, -3, 3), (math.radians(55), 0, math.radians(45)), size=2)
    _add_light(studio, "Fill", 'AREA', 150, (-3, -2, 1.5), (math.radians(75), 0, math.radians(-55)), size=3)
    _add_light(studio, "Rim", 'AREA', 400, (0, 3, 2.5), (math.radians(120), 0, 0), size=1.5)

    # 2. Dramatic: one hard warm spot, almost no ambient light.
    _set_world(dramatic, (0.02, 0.02, 0.03), 0.2)
    _add_light(dramatic, "Spot", 'SPOT', 1500, (2.2, -2.2, 3.2), (math.radians(50), 0, math.radians(45)),
               color=(1.0, 0.75, 0.5), spot=28)

    # 3. Outdoor: sun + procedural sky.
    sky_world = bpy.data.worlds.new("World_Outdoor")
    sky_world.use_nodes = True
    nt = sky_world.node_tree
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sun_disc = False
    # Sky lights the scene gently (so the sun dominates and casts clear
    # shadows) but looks full-bright when seen directly by the camera.
    bg_light = nt.nodes.get("Background")
    bg_light.inputs["Strength"].default_value = 0.08
    bg_view = nt.nodes.new("ShaderNodeBackground")
    bg_view.inputs["Strength"].default_value = 0.9
    lp = nt.nodes.new("ShaderNodeLightPath")
    mixsh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(sky.outputs["Color"], bg_light.inputs["Color"])
    nt.links.new(sky.outputs["Color"], bg_view.inputs["Color"])
    nt.links.new(lp.outputs["Is Camera Ray"], mixsh.inputs["Fac"])
    nt.links.new(bg_light.outputs["Background"], mixsh.inputs[1])
    nt.links.new(bg_view.outputs["Background"], mixsh.inputs[2])
    nt.links.new(mixsh.outputs["Shader"], nt.nodes.get("World Output").inputs["Surface"])
    outdoor.world = sky_world
    _add_light(outdoor, "Sun", 'SUN', 3.2, (0, 0, 5), (math.radians(50), 0, math.radians(40)),
               color=(1.0, 0.93, 0.82))
    outdoor.view_settings.exposure = -0.4

    for sc in (studio, dramatic, outdoor):
        sc.camera = bpy.data.objects["Camera"]
    save("session-06/session-06-start.blend")



# ---------------------------------------------------------------- Session 7
def _studio_lighting(scene):
    _studio_world(scene)
    _add_light(scene, "Key", 'AREA', 500, (3, -3, 3), (math.radians(55), 0, math.radians(45)), size=2)
    _add_light(scene, "Fill", 'AREA', 150, (-3, -2, 1.5), (math.radians(75), 0, math.radians(-55)), size=3)
    _add_light(scene, "Rim", 'AREA', 400, (0, 3, 2.5), (math.radians(120), 0, 0), size=1.5)


def _aimed_camera(name, loc, target_loc, lens):
    cam = add_camera(loc, (0, 0, 0), name)
    cam.data.lens = lens
    cam.data.show_composition_thirds = True
    target = bpy.data.objects.new(f"{name}_Target", None)
    bpy.context.scene.collection.objects.link(target)
    target.location = target_loc
    con = cam.constraints.new('TRACK_TO')
    con.target = target
    con.track_axis = 'TRACK_NEGATIVE_Z'
    con.up_axis = 'UP_Y'
    return cam, target


def build_07():
    build_05(False)
    bpy.data.objects.remove(bpy.data.objects["Sun"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
    scn = bpy.context.scene
    _studio_lighting(scn)

    # Wide: aim past the lamp so it lands on the left third with room to breathe.
    wide, _ = _aimed_camera("Cam_Wide", (2.9, -3.5, 1.35), (0.8, 0.65, 0.85), 32)

    # Close-up (macro): 85mm wide open (f/1.2), focused on one stud of the
    # base ring. Neighbouring studs, the pole and the shade fall off into
    # blur, which is exactly what depth of field is. Focus distance is the
    # camera-to-stud distance.
    close, _tgt = _aimed_camera("Cam_CloseUp", (1.0, -1.4, 0.38), (0.26, -0.45, 0.1), 85)
    close.data.dof.use_dof = True
    close.data.dof.focus_distance = 1.24
    close.data.dof.aperture_fstop = 1.2

    # Low angle: close enough to feel monumental, far enough to keep the base.
    _aimed_camera("Cam_LowAngle", (1.35, -1.85, 0.14), (0, 0, 1.0), 20)

    scn.camera = wide
    save("session-07/session-07-start.blend")



# ---------------------------------------------------------------- Session 8
def build_08():
    clear_scene()
    _lamp_stand_in()
    mat = make_material("Lamp_Preview_Material", (0.8, 0.5, 0.2), metallic=0.3, roughness=0.4)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.data.materials.append(mat)
    add_sun()
    cam = add_camera((3, -3, 1.8), (math.radians(68), 0, math.radians(45)))
    scn = bpy.context.scene
    scn.camera = cam
    scn.render.resolution_x = 480
    scn.render.resolution_y = 270

    import os
    render_dir = f"{ROOT}/session-08/renders"
    os.makedirs(render_dir, exist_ok=True)

    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'
    scn.render.filepath = f"{render_dir}/eevee_test.png"
    bpy.ops.render.render(write_still=True)

    scn.render.engine = 'CYCLES'
    scn.cycles.samples = 32
    scn.render.filepath = f"{render_dir}/cycles_test.png"
    bpy.ops.render.render(write_still=True)

    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'
    save("session-08/session-08-start.blend")


# ---------------------------------------------------------------- Session 9
def build_09():
    clear_scene()
    shade = _lamp_stand_in()[1]
    bpy.data.objects.remove(bpy.data.objects["Lamp_Base"], do_unlink=True)

    bpy.context.view_layer.objects.active = shade
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66))
    bpy.ops.object.mode_set(mode='OBJECT')

    img = bpy.data.images.new("UV_Grid_Check", width=1024, height=1024)
    img.generated_type = 'UV_GRID'

    mat = bpy.data.materials.new("Lamp_Shade_UVCheck")
    mat.use_nodes = True
    nt = mat.node_tree
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    bsdf = nt.nodes.get("Principled BSDF")
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    shade.data.materials.append(mat)

    add_sun()
    add_camera((2, -2, 1.5), (math.radians(65), 0, math.radians(45)))
    save("session-09/session-09-start.blend")


# ---------------------------------------------------------------- Session 10
def build_10():
    clear_scene()
    coll = new_collection("Sculpt")
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=0.6, location=(0, 0, 0.6))
    rock = bpy.context.active_object
    rock.name = "Rock_Base"

    import mathutils.noise as noise
    me = rock.data
    for v in me.vertices:
        co = v.co.copy()
        n = noise.noise(co * 3.0)
        v.co += v.normal * (n * 0.18)
    me.update()

    multires = rock.modifiers.new("Multires", 'MULTIRES')
    bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')
    bpy.ops.object.multires_subdivide(modifier="Multires", mode='CATMULL_CLARK')

    move_to_collection(rock, coll)
    add_sun()
    add_camera((2, -2, 1.3), (math.radians(65), 0, math.radians(45)))

    txt = bpy.data.texts.new("session-10-notes")
    txt.write(
        "Rock_Base is a noise-displaced icosphere with a Multires modifier already\n"
        "subdivided twice. Enter Sculpt Mode and use Multires levels + brushes\n"
        "(Clay Strips, Crease, Smooth) to push this from 'procedural blob' to an\n"
        "actual hand-sculpted rock, fruit, or creature head -- your call.\n"
    )
    show_text(txt)
    save("session-10/session-10-start.blend")


# ---------------------------------------------------------------- Session 11
def build_11():
    clear_scene()
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(-3, 0, 0.4))
    ball = bpy.context.active_object
    ball.name = "Bounce_Ball"
    mat = make_material("Ball_Red", (0.8, 0.1, 0.1), roughness=0.3)
    ball.data.materials.append(mat)

    bpy.ops.mesh.primitive_plane_add(size=10)
    bpy.context.active_object.name = "Ground"

    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 48

    keys = [
        (1, (-3, 0, 1.5), (1, 1, 1)),
        (12, (-1, 0, 0.4), (1.3, 1.3, 0.6)),
        (14, (-1, 0, 0.5), (0.9, 0.9, 1.15)),
        (24, (1, 0, 1.3), (1, 1, 1)),
        (36, (3, 0, 0.4), (1.3, 1.3, 0.6)),
        (38, (3, 0, 0.5), (0.9, 0.9, 1.15)),
        (48, (3, 0, 0.9), (1, 1, 1)),
    ]
    for frame, loc, scale in keys:
        scn.frame_set(frame)
        ball.location = loc
        ball.scale = scale
        ball.keyframe_insert(data_path="location")
        ball.keyframe_insert(data_path="scale")
    scn.frame_set(1)

    add_sun()
    add_camera((0, -6, 1.5), (math.radians(80), 0, 0))
    save("session-11/session-11-start.blend")


# ---------------------------------------------------------------- Session 12
def build_12():
    clear_scene()
    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.6, location=(0, 0, 0.8))
    body = bpy.context.active_object
    body.name = "Character_Stub"

    bpy.ops.object.armature_add(location=(0, 0, 0))
    arm_obj = bpy.context.active_object
    arm_obj.name = "Character_Rig"
    arm = arm_obj.data

    bpy.ops.object.mode_set(mode='EDIT')
    ebones = arm.edit_bones
    root = ebones[0]
    root.name = "Root"
    root.head = (0, 0, 0)
    root.tail = (0, 0, 0.6)

    spine = ebones.new("Spine")
    spine.head = (0, 0, 0.6)
    spine.tail = (0, 0, 1.2)
    spine.parent = root

    head = ebones.new("Head")
    head.head = (0, 0, 1.2)
    head.tail = (0, 0, 1.6)
    head.parent = spine
    bpy.ops.object.mode_set(mode='OBJECT')

    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')

    add_sun()
    add_camera((3, -3, 1.6), (math.radians(68), 0, math.radians(45)))
    save("session-12/session-12-start.blend")


# ---------------------------------------------------------------- Session 13
def build_13():
    build_12()
    arm_obj = bpy.data.objects["Character_Rig"]
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')
    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 24

    spine = arm_obj.pose.bones["Spine"]
    head = arm_obj.pose.bones["Head"]
    poses = [
        (1, 0, 0),
        (6, math.radians(10), math.radians(-5)),
        (12, 0, 0),
        (18, math.radians(-10), math.radians(5)),
        (24, 0, 0),
    ]
    for frame, spine_x, head_x in poses:
        scn.frame_set(frame)
        spine.rotation_mode = 'XYZ'
        head.rotation_mode = 'XYZ'
        spine.rotation_euler = (spine_x, 0, 0)
        head.rotation_euler = (head_x, 0, 0)
        spine.keyframe_insert(data_path="rotation_euler")
        head.keyframe_insert(data_path="rotation_euler")
    scn.frame_set(1)
    bpy.ops.object.mode_set(mode='OBJECT')
    save("session-13/session-13-start.blend")


# ---------------------------------------------------------------- Session 14
def build_14():
    clear_scene()
    bpy.ops.mesh.primitive_plane_add(size=6, location=(0, 0, 0))
    ground = bpy.context.active_object
    ground.name = "Ground"
    bpy.context.view_layer.objects.active = ground
    ground.select_set(True)
    bpy.ops.rigidbody.object_add(type='PASSIVE')

    for i in range(5):
        bpy.ops.mesh.primitive_cube_add(size=0.4, location=(i * 0.1 - 0.2, 0, 1.5 + i * 0.6))
        cube = bpy.context.active_object
        cube.name = f"Falling_Cube_{i+1}"
        bpy.context.view_layer.objects.active = cube
        bpy.ops.object.select_all(action='DESELECT')
        cube.select_set(True)
        bpy.ops.rigidbody.object_add(type='ACTIVE')

    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 60
    scn.rigidbody_world.point_cache.frame_end = 60

    add_sun()
    add_camera((4, -5, 3), (math.radians(65), 0, math.radians(40)))

    txt = bpy.data.texts.new("session-14-notes")
    txt.write(
        "Five active rigid-body cubes over a passive rigid-body ground are already set up.\n"
        "Press Space to play and watch them fall and settle -- that's the rigid-body side\n"
        "of this session. For the particle half, add a Particle System to Ground (hair or\n"
        "emitter) and experiment with count/size/physics.\n"
    )
    show_text(txt)
    save("session-14/session-14-start.blend")


# ---------------------------------------------------------------- Session 15
def build_15():
    clear_scene()
    _lamp_stand_in()
    mat = make_material("Lamp_Comp_Preview", (0.8, 0.5, 0.2), metallic=0.3, roughness=0.4)
    for obj in bpy.context.scene.objects:
        if obj.type == 'MESH':
            obj.data.materials.append(mat)
    add_sun()
    cam = add_camera((3, -3, 1.6), (math.radians(68), 0, math.radians(45)))
    bpy.context.scene.camera = cam

    nt = bpy.data.node_groups.new("Compositor", 'CompositorNodeTree')
    nt.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')
    rl = nt.nodes.new("CompositorNodeRLayers")
    glare = nt.nodes.new("CompositorNodeGlare")
    glare.inputs["Type"].default_value = 'Fog Glow'
    glare.inputs["Threshold"].default_value = 0.8
    cc = nt.nodes.new("CompositorNodeColorBalance")
    group_out = nt.nodes.new("NodeGroupOutput")
    nt.links.new(rl.outputs["Image"], glare.inputs["Image"])
    nt.links.new(glare.outputs["Image"], cc.inputs["Image"])
    nt.links.new(cc.outputs["Image"], group_out.inputs["Image"])
    bpy.context.scene.compositing_node_group = nt

    save("session-15/session-15-start.blend")


# ---------------------------------------------------------------- Session 16
def build_16():
    clear_scene()
    scn = bpy.context.scene
    scn.sequence_editor_create()
    se = scn.sequence_editor

    s1 = se.strips.new_effect("Shot_01_Intro", type='COLOR', channel=1, frame_start=1, length=50)
    s1.color = (0.1, 0.1, 0.15)
    s2 = se.strips.new_effect("Shot_02_Action", type='COLOR', channel=1, frame_start=51, length=70)
    s2.color = (0.15, 0.3, 0.2)
    s3 = se.strips.new_effect("Shot_03_Reveal", type='COLOR', channel=1, frame_start=121, length=50)
    s3.color = (0.3, 0.2, 0.1)

    se.strips.new_effect(
        "CrossFade_1_2", type='CROSS', channel=2,
        frame_start=45, length=10, input1=s1, input2=s2)
    se.strips.new_effect(
        "CrossFade_2_3", type='CROSS', channel=2,
        frame_start=116, length=10, input1=s2, input2=s3)

    scn.frame_start = 1
    scn.frame_end = 170

    txt = bpy.data.texts.new("session-16-notes")
    txt.write(
        "Three placeholder color strips (Intro / Action / Reveal) are laid out on the\n"
        "VSE timeline with cross-fades already bridging them. Replace each color strip\n"
        "with your real rendered image/video strips (Add > Movie/Image), keeping the\n"
        "transitions, and add an audio strip for sync.\n"
    )
    show_text(txt)
    save("session-16/session-16-start.blend")


# ---------------------------------------------------------------- Session 17
def build_17():
    print("Session 17 is a planning session -- see session-17/storyboard.md, no .blend needed.")


# ---------------------------------------------------------------- Session 18
def build_18():
    clear_scene()
    coll_a = new_collection("Character_A")
    coll_b = new_collection("Character_B")

    bpy.ops.mesh.primitive_cylinder_add(radius=0.3, depth=1.6, location=(-1.5, 0, 0.8))
    char_a = bpy.context.active_object
    char_a.name = "Character_A_Stub"
    move_to_collection(char_a, coll_a)

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=0.5, location=(1.5, 0, 0.5))
    char_b = bpy.context.active_object
    char_b.name = "Character_B_Stub"
    move_to_collection(char_b, coll_b)

    bpy.ops.mesh.primitive_plane_add(size=10)
    bpy.context.active_object.name = "Ground"

    scn = bpy.context.scene
    scn.frame_start = 1
    scn.frame_end = 300  # ~12s at 25fps, resize to taste once the story is locked

    add_sun()
    cam = add_camera((4, -5, 2), (math.radians(72), 0, math.radians(40)))
    scn.camera = cam

    scn.sequence_editor_create()
    se = scn.sequence_editor
    se.strips.new_effect("Shot_01", type='COLOR', channel=1, frame_start=1, length=100)
    se.strips.new_effect("Shot_02", type='COLOR', channel=1, frame_start=101, length=100)
    se.strips.new_effect("Shot_03", type='COLOR', channel=1, frame_start=201, length=100)

    txt = bpy.data.texts.new("session-18-notes")
    txt.write(
        "Capstone skeleton: two placeholder characters/objects, a ground plane, a camera,\n"
        "and a 3-shot VSE timeline block already set to your Session 17 storyboard length.\n"
        "Replace the stub meshes with your real modeled/rigged/animated characters, render\n"
        "each shot, drop the renders into the VSE in place of the color strips, add audio,\n"
        "and export.\n"
    )
    show_text(txt)
    save("session-18/session-18-start.blend")


BUILDERS = {
    1: build_01, 2: build_02, 3: build_03, 4: build_04, 5: build_05,
    6: build_06, 7: build_07, 8: build_08, 9: build_09, 10: build_10,
    11: build_11, 12: build_12, 13: build_13, 14: build_14, 15: build_15,
    16: build_16, 17: build_17, 18: build_18,
}

if __name__ == "__main__":
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    if not argv:
        print("Usage: blender --background --python build_session.py -- <session_number>")
        sys.exit(1)
    n = int(argv[0])
    BUILDERS[n]()
