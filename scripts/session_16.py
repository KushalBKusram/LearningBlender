"""
Session 16 builder.
  blender --background --python scripts/session_16.py -- clips   # render 3 real MP4 clips
  blender --background --python scripts/session_16.py -- vse     # assemble the VSE timeline
  blender --background --python scripts/session_16.py -- preview # render preview frames + MP4
"""
import os
import sys, math, struct, wave, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
import build_session as bs

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session-16")
FOOTAGE = f"{ROOT}/footage"
RES = (640, 360)
FPS = 24


def set_video_output(scene, path, audio=False):
    scene.render.resolution_x, scene.render.resolution_y = RES
    scene.render.resolution_percentage = 100
    scene.render.fps = FPS
    try:
        scene.render.engine = 'BLENDER_EEVEE_NEXT'
    except TypeError:
        scene.render.engine = 'BLENDER_EEVEE'
    s = scene.render.image_settings
    s.media_type = 'VIDEO'
    s.file_format = 'FFMPEG'
    scene.render.ffmpeg.format = 'MPEG4'
    scene.render.ffmpeg.codec = 'H264'
    scene.render.ffmpeg.constant_rate_factor = 'MEDIUM'
    if audio:
        # Without an audio codec the MP4 has NO audio track, whatever is on the timeline.
        scene.render.ffmpeg.audio_codec = 'AAC'
        scene.render.ffmpeg.audio_bitrate = 128
        scene.render.ffmpeg.audio_mixrate = 44100
        scene.render.ffmpeg.audio_channels = 'STEREO'
    scene.render.filepath = path


def lamp_scene():
    bs.build_05(False)
    bpy.data.objects.remove(bpy.data.objects["Sun"], do_unlink=True)
    bpy.data.objects.remove(bpy.data.objects["Camera"], do_unlink=True)
    scn = bpy.context.scene
    bs._studio_lighting(scn)
    return scn


def render_clip(scn, name, frames):
    scn.frame_start, scn.frame_end = 1, frames
    set_video_output(scn, f"{FOOTAGE}/{name}.mp4")
    bpy.ops.render.render(animation=True)
    print("CLIP:", name, frames)


def clip_turntable():
    scn = lamp_scene()
    pivot = bpy.data.objects.new("Pivot", None)
    scn.collection.objects.link(pivot)
    pivot.location = (0, 0, 0.9)
    cam, _ = bs._aimed_camera("Cam", (3.3, -4.0, 1.5), (0, 0, 0.9), 32)
    cam.parent = pivot
    cam.matrix_parent_inverse = pivot.matrix_world.inverted()
    pivot.rotation_euler = (0, 0, 0)
    pivot.keyframe_insert("rotation_euler", frame=1)
    pivot.rotation_euler = (0, 0, math.radians(180))
    pivot.keyframe_insert("rotation_euler", frame=60)
    for fc in pivot.animation_data.action.fcurves if hasattr(pivot.animation_data.action, "fcurves") else []:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
    scn.camera = cam
    render_clip(scn, "clip1_turntable", 60)


def clip_dolly():
    scn = lamp_scene()
    cam, tgt = bs._aimed_camera("Cam", (3.0, -3.4, 1.9), (0, 0, 1.6), 50)
    cam.location = (3.0, -3.4, 1.9)
    cam.keyframe_insert("location", frame=1)
    cam.location = (1.5, -1.9, 1.85)
    cam.keyframe_insert("location", frame=48)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_object = tgt
    cam.data.dof.aperture_fstop = 2.0
    scn.camera = cam
    render_clip(scn, "clip2_dolly", 48)


def clip_bounce():
    scn = lamp_scene()
    for n in ("Lamp_Root", "Lamp_Base", "Lamp_Pole", "Lamp_Shade", "Lamp_Base_Ridge", "Ridge_Offset"):
        o = bpy.data.objects.get(n)
        if o:
            bpy.data.objects.remove(o, do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(-2.5, 0, 1.6))
    ball = bpy.context.active_object
    ball.data.materials.append(bs.make_material("Ball_Red", (0.85, 0.12, 0.1), roughness=0.3))
    bpy.ops.object.shade_smooth()
    keys = [(1, (-2.5, 0, 1.6), (1, 1, 1)), (10, (-1.3, 0, 0.4), (1.25, 1.25, 0.7)),
            (14, (-1.0, 0, 0.55), (0.92, 0.92, 1.12)), (26, (0.2, 0, 1.4), (1, 1, 1)),
            (38, (1.4, 0, 0.4), (1.25, 1.25, 0.7)), (42, (1.7, 0, 0.55), (0.92, 0.92, 1.12)),
            (54, (2.6, 0, 1.0), (1, 1, 1))]
    for f, loc, sc in keys:
        ball.location, ball.scale = loc, sc
        ball.keyframe_insert("location", frame=f)
        ball.keyframe_insert("scale", frame=f)
    cam, _ = bs._aimed_camera("Cam", (0, -7, 1.4), (0, 0, 1.0), 35)
    scn.camera = cam
    render_clip(scn, "clip3_bounce", 54)


def make_click_track(path):
    rate = 44100
    seconds = 7   # timeline is ~6.1 s; leave headroom so the strip is never shorter
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        frames = bytearray()
        for i in range(rate * seconds):
            t = i / rate
            beat = (t * 2) % 1.0  # 120 bpm click
            env = max(0.0, 1.0 - beat * 12)
            tone = math.sin(2 * math.pi * 880 * t) * env * 0.5
            pad = math.sin(2 * math.pi * 220 * t) * 0.08
            frames += struct.pack("<h", int((tone + pad) * 32000))
        w.writeframes(bytes(frames))


def build_vse():
    bs.clear_scene()
    scn = bpy.context.scene
    set_video_output(scn, f"{ROOT}/renders/timeline_preview.mp4", audio=True)
    scn.sequence_editor_create()
    se = scn.sequence_editor

    clips = [("clip1_turntable", 1, "S1 Turntable"), ("clip2_dolly", 2, "S2 Dolly"),
             ("clip3_bounce", 1, "S3 Bounce")]
    overlap = 8
    start = 1
    strips = []
    for name, channel, label in clips:
        s = se.strips.new_movie(label, f"{FOOTAGE}/{name}.mp4", channel=channel, frame_start=start)
        s.color_tag = 'COLOR_04'
        strips.append(s)
        start = s.frame_final_end - overlap
    # crossfades live on channel 3, above both inputs, spanning each overlap
    for i in range(len(strips) - 1):
        a, b = strips[i], strips[i + 1]
        xf = se.strips.new_effect(f"XFade S{i+1}-S{i+2}", 'CROSS', channel=3,
                                  frame_start=b.frame_final_start, length=overlap, input1=a, input2=b)
        xf.color_tag = 'COLOR_03'

    total = strips[-1].frame_final_end - 1
    scn.frame_start, scn.frame_end = 1, total

    title = se.strips.new_effect("Title", 'TEXT', channel=4, frame_start=1, length=40)
    title.color_tag = 'COLOR_05'
    title.text = "LEARNING BLENDER  /  SESSION 16"
    title.font_size = 20
    title.location = (0.5, 0.88)
    title.color = (1, 1, 1, 1)
    title.use_shadow = True

    wav = f"{FOOTAGE}/click_track.wav"
    make_click_track(wav)
    snd = se.strips.new_sound("Audio - click track 120bpm", wav, channel=5, frame_start=1)
    snd.volume = 0.6
    snd.color_tag = 'COLOR_01'
    if snd.frame_final_end - 1 > total:
        snd.frame_final_end = total + 1

    for ch, label in ((1, "Clips A"), (2, "Clips B"), (3, "Transitions"), (4, "Titles"), (5, "Audio")):
        se.channels[ch].name = label

    txt = bpy.data.texts.new("session-16-notes")
    txt.write(
        "Session 16 -- Video Editing Timeline (VSE)\n"
        "------------------------------------------\n"
        "Pre-built: three REAL rendered MP4 clips (turntable, dolly, bouncing ball) loaded\n"
        "as movie strips with 8-frame cross-fades, a title text strip, and a 120bpm click\n"
        "audio strip. Open the Video Editing workspace (or switch an editor to Video\n"
        "Sequencer) to see them.\n\n"
        "Your job: re-time the cuts (grab strip edges / press K to cut), shorten or extend\n"
        "the cross-fades, retype the title, change its position/size, add a Fade-out\n"
        "(Add > Effect Strip > Color Mix / Gamma Cross), and re-render:\n"
        "Render > Render Animation (output is MP4/H.264 + AAC audio in renders/, so the\n"
        "click track is baked into the video).\n\n"
        "Layout: channel 1/2 'Clips A/B' (blue strips alternate so cuts can overlap),\n"
        "3 'Transitions' (cross-fades, green), 4 'Titles' (purple), 5 'Audio' (red).\n"
    )
    bs.show_text(txt)
    scn.sequence_editor.strips  # keep reference
    bs.save("session-16/session-16-start.blend")
    print("TIMELINE_FRAMES:", total)


def preview():
    bpy.ops.wm.open_mainfile(filepath=f"{ROOT}/session-16-start.blend")
    scn = bpy.context.scene
    set_video_output(scn, f"{ROOT}/renders/timeline_preview.mp4", audio=True)
    total = scn.frame_end
    picks = [1, 20, 57, 80, 97, 120]
    old = scn.render.image_settings.media_type
    s = scn.render.image_settings
    s.media_type = 'IMAGE'
    s.file_format = 'PNG'
    for f in picks:
        scn.frame_set(f)
        scn.render.filepath = f"{ROOT}/renders/vse_frame_{f:03d}.png"
        bpy.ops.render.render(write_still=True)
    set_video_output(scn, f"{ROOT}/renders/timeline_preview.mp4", audio=True)
    bpy.ops.render.render(animation=True)
    print("PREVIEW_DONE")


if __name__ == "__main__":
    mode = sys.argv[sys.argv.index("--") + 1]
    if mode == "clips":
        which = sys.argv[sys.argv.index("--") + 2:] or ["1", "2", "3"]
        {"1": clip_turntable, "2": clip_dolly, "3": clip_bounce}[which[0]]()
    elif mode == "vse":
        build_vse()
    elif mode == "preview":
        preview()
