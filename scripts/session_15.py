"""Session 15 -- Compositing Basics.

Run: Blender --background --python scripts/session_15.py
Builds session-15/session-15-start.blend: studio-lit lamp with a compositor node
group (Render Layers > Glare > Color Balance > Lens Distortion > Vignette > Output),
then renders before/after stills to prove the compositor is applied.

Blender 5.3 compositor notes (shared with other forks):
 * No CompositorNodeComposite / CompositorNodeMix / CompositorNodeMath any more.
   Scene output is a NodeGroupOutput bound to an interface socket named "Image".
   Use the generic ShaderNodeMix (data_type='RGBA') for mixing colors.
 * Node options are input sockets (e.g. glare.inputs['Type'].default_value = 'Fog Glow').
 * Assign with scene.compositing_node_group = node_group.
"""
import os
import sys
import math
import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_session as bs

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDERS = f"{ROOT}/session-15/renders"


def mix_rgba(nt, blend='MIX', factor=1.0, a=None, b=None):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = 'RGBA'
    n.blend_type = blend
    n.inputs["Factor"].default_value = factor
    if a is not None:
        n.inputs["A"].default_value = a
    if b is not None:
        n.inputs["B"].default_value = b
    return n


def mix_sockets(node):
    """(factor, A, B, result) sockets of an RGBA ShaderNodeMix, skipping hidden ones."""
    ins = [s for s in node.inputs if s.enabled]
    fac = next(s for s in ins if s.name == "Factor")
    a = next(s for s in ins if s.name == "A")
    b = next(s for s in ins if s.name == "B")
    res = next(s for s in node.outputs if s.enabled)
    return fac, a, b, res


def build_compositor(scene):
    nt = bpy.data.node_groups.new("Lamp_Comp", 'CompositorNodeTree')
    nt.interface.new_socket(name="Image", in_out='OUTPUT', socket_type='NodeSocketColor')

    rl = nt.nodes.new("CompositorNodeRLayers")
    rl.location = (-900, 0)

    glare = nt.nodes.new("CompositorNodeGlare")
    glare.label = "Glow"
    glare.location = (-650, 0)
    glare.inputs["Type"].default_value = 'Fog Glow'
    glare.inputs["Threshold"].default_value = 0.9
    glare.inputs["Strength"].default_value = 0.5
    glare.inputs["Size"].default_value = 7

    cb = nt.nodes.new("CompositorNodeColorBalance")
    cb.label = "Warm grade"
    cb.location = (-400, 0)
    # Lift/Gamma/Gain flavor: teal shadows, warm highlights.
    for s in cb.inputs:
        if s.name == "Type" and s.type == 'MENU':
            s.default_value = 'Lift/Gamma/Gain'
    lifts = [s for s in cb.inputs if s.name == "Lift" and s.type == 'RGBA']
    gains = [s for s in cb.inputs if s.name == "Gain" and s.type == 'RGBA']
    if lifts:
        lifts[0].default_value = (0.92, 1.0, 1.04, 1.0)
    if gains:
        gains[0].default_value = (1.12, 1.0, 0.86, 1.0)

    lens = nt.nodes.new("CompositorNodeLensdist")
    lens.label = "Chromatic fringe"
    lens.location = (-150, 0)
    lens.inputs["Distortion"].default_value = 0.0
    lens.inputs["Dispersion"].default_value = 0.012

    # Vignette: soft ellipse mask -> mix(dark, image).
    ell = nt.nodes.new("CompositorNodeEllipseMask")
    ell.location = (-400, -420)
    ell.inputs["Position"].default_value = (0.5, 0.5)
    ell.inputs["Size"].default_value = (0.9, 0.9)
    ell.inputs["Value"].default_value = 1.0
    ell.inputs["Mask"].default_value = 0.0

    blur = nt.nodes.new("CompositorNodeBlur")
    blur.location = (-150, -420)
    blur.inputs["Size"].default_value = (120.0, 120.0)

    dark = mix_rgba(nt, blend='MULTIPLY', factor=1.0, b=(0.18, 0.18, 0.22, 1.0))
    dark.label = "Darken"
    dark.location = (100, 0)
    vig = mix_rgba(nt, blend='MIX')
    vig.label = "Vignette"
    vig.location = (350, 0)

    out = nt.nodes.new("NodeGroupOutput")
    out.location = (600, 0)

    L = nt.links.new
    L(rl.outputs["Image"], glare.inputs["Image"])
    L(glare.outputs["Image"], cb.inputs["Image"])
    L(cb.outputs["Image"], lens.inputs["Image"])

    d_fac, d_a, d_b, d_res = mix_sockets(dark)
    L(lens.outputs["Image"], d_a)

    L(ell.outputs["Mask"], blur.inputs["Image"])
    v_fac, v_a, v_b, v_res = mix_sockets(vig)
    L(blur.outputs["Image"], v_fac)   # 1 inside the ellipse -> show the graded image (B)
    L(d_res, v_a)                     # outside -> darkened
    L(lens.outputs["Image"], v_b)
    L(v_res, out.inputs["Image"])

    scene.compositing_node_group = nt
    return nt


def build():
    bs.build_05(False)
    bpy.data.objects.remove(bpy.data.objects["Sun"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
    scn = bpy.context.scene
    bs._studio_lighting(scn)
    # Bright emissive sliver so Glare has something to bloom: a hot rim on the shade.
    shade = bpy.data.objects["Lamp_Shade"]
    glow = bs.make_material("Shade_Glow", (1.0, 0.85, 0.6), roughness=0.4)
    bsdf = glow.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.8, 0.5, 1.0)
    bsdf.inputs["Emission Strength"].default_value = 6.0
    shade.data.materials.clear()
    shade.data.materials.append(glow)

    cam, _ = bs._aimed_camera("Camera", (3.3, -4.0, 1.5), (0, 0, 0.9), 32)
    cam.data.show_composition_thirds = False
    scn.camera = cam
    scn.render.resolution_x = 960
    scn.render.resolution_y = 720
    try:
        scn.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scn.render.engine = 'BLENDER_EEVEE'
    build_compositor(scn)

    txt = bpy.data.texts.new("session-15-notes")
    txt.write(
        "Session 15 -- Compositing Basics\n"
        "--------------------------------\n"
        "Open the Compositing workspace tab. The node group 'Lamp_Comp' is wired:\n"
        "  Render Layers > Glare (fog glow) > Color Balance (teal shadows, warm highlights)\n"
        "  > Lens Distortion (chromatic fringe) > Darken x Vignette mask > Group Output.\n"
        "The shade is emissive so the glow has something to bloom.\n\n"
        "TOGGLING THE EFFECT (three ways):\n"
        "  1. Whole chain on/off: Output Properties > Post Processing > Compositing checkbox.\n"
        "     Unchecked = plain render, checked = graded render. Press F12 to re-render.\n"
        "  2. One effect on/off: in the Compositing tab click a node (Glare, Color Balance,\n"
        "     Lens Distortion) and press M to mute it; press M again to restore it.\n"
        "  3. Strength: lower the Glare Strength / Color Balance Factor / vignette Size.\n"
        "renders/before.png vs after.png (and before_after.png) are already included.\n"
        "Try changing Glare Type, Threshold, or the vignette Size.\n"
    )
    bs.show_text(txt)


def render_pair():
    scn = bpy.context.scene
    scn.render.image_settings.file_format = 'PNG'
    scn.render.use_compositing = False
    scn.render.filepath = f"{RENDERS}/before.png"
    bpy.ops.render.render(write_still=True)
    scn.render.use_compositing = True
    scn.render.filepath = f"{RENDERS}/after.png"
    bpy.ops.render.render(write_still=True)


def side_by_side():
    import numpy as np
    imgs = []
    for name in ("before", "after"):
        im = bpy.data.images.load(f"{RENDERS}/{name}.png", check_existing=False)
        w, h = im.size
        arr = np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)
        imgs.append(arr)
    both = np.concatenate(imgs, axis=1)
    out = bpy.data.images.new("before_after", width=both.shape[1], height=both.shape[0])
    out.pixels = both.ravel().tolist()
    out.filepath_raw = f"{RENDERS}/before_after.png"
    out.file_format = 'PNG'
    out.save()
    print("pair diff mean abs:", float(np.abs(imgs[0][..., :3] - imgs[1][..., :3]).mean()))


if __name__ == "__main__":
    import os
    os.makedirs(RENDERS, exist_ok=True)
    build()
    bs.save("session-15/session-15-start.blend")
    render_pair()
    side_by_side()
