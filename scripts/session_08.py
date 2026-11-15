"""Session 8 -- Rendering Engines & Settings. Run:
Blender --background --python scripts/session_08.py
"""
import sys
import time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import build_session as bs

ROOT = bs.ROOT
OUT = f"{ROOT}/session-08/renders"
os.makedirs(OUT, exist_ok=True)

bs.build_05(False)
bpy.data.objects.remove(bpy.data.objects["Sun"], do_unlink=True)
bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
eevee = bpy.context.scene
eevee.name = "Scene_Eevee"
bs._studio_lighting(eevee)
wide, _ = bs._aimed_camera("Cam_Wide", (3.3, -4.0, 1.5), (0, 0, 0.9), 32)
eevee.camera = wide
wide.data.show_composition_thirds = False

# Duplicate (linked objects -> identical content), find the new scene by set difference.
before = set(bpy.data.scenes)
bpy.ops.scene.new(type='LINK_COPY')
cycles = (set(bpy.data.scenes) - before).pop()
cycles.name = "Scene_Cycles"
cycles.camera = wide


def configure(sc, engine, path):
    sc.render.resolution_x = 640
    sc.render.resolution_y = 480
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = 'PNG'
    sc.render.filepath = path
    sc.render.engine = engine
    if engine == 'CYCLES':
        sc.cycles.device = 'CPU'
        sc.cycles.samples = 64
        sc.cycles.use_denoising = True
    else:
        sc.eevee.taa_render_samples = 64


try:
    ee_engine = 'BLENDER_EEVEE_NEXT'
    eevee.render.engine = ee_engine
except TypeError:
    ee_engine = 'BLENDER_EEVEE'
configure(eevee, ee_engine, f"{OUT}/eevee.png")
configure(cycles, 'CYCLES', f"{OUT}/cycles.png")

times = {}
for sc in (eevee, cycles):
    t0 = time.time()
    bpy.ops.render.render(write_still=True, scene=sc.name)
    times[sc.name] = time.time() - t0
    print("RENDER", sc.name, round(times[sc.name], 2), "s")

txt = bpy.data.texts.new("session-08-notes")
txt.write(
    "Session 8 -- Rendering Engines & Settings\n"
    "------------------------------------------\n"
    "Two scenes with identical content (linked copies of the lamp, same studio\n"
    "lights, same camera): Scene_Eevee and Scene_Cycles. Switch with the scene\n"
    "dropdown at the top right.\n\n"
    "Both are set to 640x480 PNG, 64 samples. I already rendered both:\n"
    "  session-08/renders/eevee.png   (%.1f s in headless run)\n"
    "  session-08/renders/cycles.png  (%.1f s in headless run, CPU, denoised)\n\n"
    "Compare them: Cycles traces real light, so you get softer contact shadows\n"
    "and true reflections in the metal; Eevee is a fast rasterizer that\n"
    "approximates them. Timings depend on your machine -- re-render with F12.\n\n"
    "Your turn:\n"
    "1. Render Properties tab: change samples (try 8, 64, 256) and watch noise/time.\n"
    "2. Try Cycles with Denoise off, then on.\n"
    "3. Change resolution %% to 50 and note the speed change.\n"
    "4. Render > Render Image (F12), then Image > Save As to keep your favorite.\n"
    % (times["Scene_Eevee"], times["Scene_Cycles"])
)
bs.show_text(txt)
bpy.context.window_manager  # noqa
bs.save("session-08/session-08-start.blend")
