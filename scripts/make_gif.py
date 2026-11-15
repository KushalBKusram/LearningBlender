"""Renders the capstone (every Nth frame) and encodes an animated GIF with no external tools.

Run: Blender --background session-18/session-18-start.blend --python scripts/make_gif.py
Output: docs/lamp_keeper.gif

Blender has numpy but no GIF writer, so this does its own median-cut-free palette
(k-means on a pixel sample) + LZW encoding. Slow-ish but dependency-free.
"""
import os
import struct
import sys
import time

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = ROOT + "/docs/lamp_keeper.gif"
STEP = 3            # every 3rd frame of a 24 fps shot -> 8 fps
W, H = 480, 270
SAMPLES = 16
COLORS = 128


def render_frames():
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = W, H, 100
    sc.cycles.samples = SAMPLES
    sc.render.use_sequencer = False
    sc.render.image_settings.file_format = 'PNG'
    frames = []
    t0 = time.time()
    for f in range(1, 301, STEP):
        sc.frame_set(f)
        marks = sorted([m for m in sc.timeline_markers if m.frame <= f], key=lambda m: m.frame)
        sc.camera = marks[-1].camera
        path = f"/tmp/gif_frame_{f:03d}.png"
        sc.render.filepath = path
        bpy.ops.render.render(write_still=True)
        img = bpy.data.images.load(path)
        px = np.array(img.pixels[:], dtype=np.float32).reshape(H, W, 4)[::-1, :, :3]   # GIF is top-down
        frames.append((np.clip(px, 0, 1) * 255).astype(np.uint8))
        bpy.data.images.remove(img)
        os.remove(path)
        print("RENDERED", f, round(time.time() - t0), "s", flush=True)
    return frames


def build_palette(frames):
    rng = np.random.default_rng(1)
    sample = np.concatenate([fr.reshape(-1, 3)[rng.integers(0, W * H, 3000)] for fr in frames]).astype(np.float32)
    centers = sample[rng.choice(len(sample), COLORS, replace=False)]
    for _ in range(12):
        d = ((sample[:, None, :] - centers[None, :, :]) ** 2).sum(-1)
        idx = d.argmin(1)
        for k in range(COLORS):
            m = sample[idx == k]
            if len(m):
                centers[k] = m.mean(0)
    return centers.astype(np.uint8)


def quantize(frame, palette):
    flat = frame.reshape(-1, 3).astype(np.int32)
    pal = palette.astype(np.int32)
    out = np.empty(len(flat), np.uint8)
    for i in range(0, len(flat), 20000):
        chunk = flat[i:i + 20000]
        d = ((chunk[:, None, :] - pal[None, :, :]) ** 2).sum(-1)
        out[i:i + 20000] = d.argmin(1)
    return out


def lzw(indices, min_code=7):
    clear, end = 1 << min_code, (1 << min_code) + 1
    code_size = min_code + 1
    table = {bytes([i]): i for i in range(clear)}
    next_code = end + 1
    out, bits, nbits = bytearray(), 0, 0

    def emit(code):
        nonlocal bits, nbits
        bits |= code << nbits
        nbits += code_size
        while nbits >= 8:
            out.append(bits & 0xFF)
            bits >>= 8
            nbits -= 8

    emit(clear)
    cur = b""
    for b in indices.tobytes():
        nxt = cur + bytes([b])
        if nxt in table:
            cur = nxt
        else:
            emit(table[cur])
            table[nxt] = next_code
            next_code += 1
            if next_code > (1 << code_size) and code_size < 12:
                code_size += 1
            if next_code >= 4096:
                emit(clear)
                table = {bytes([i]): i for i in range(clear)}
                next_code, code_size = end + 1, min_code + 1
            cur = bytes([b])
    emit(table[cur])
    emit(end)
    if nbits:
        out.append(bits & 0xFF)
    return bytes(out)


def write_gif(frames, palette, path, delay_cs):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pal_bytes = palette.tobytes() + bytes(3 * (256 - len(palette))) if len(palette) < 128 else palette.tobytes()
    with open(path, "wb") as fh:
        fh.write(b"GIF89a" + struct.pack("<HHBBB", W, H, 0x80 | 0x70 | 6, 0, 0))   # 128-colour global table
        fh.write(pal_bytes)
        fh.write(b"\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00")                   # loop forever
        for i, fr in enumerate(frames):
            idx = quantize(fr, palette)
            fh.write(b"\x21\xF9\x04\x04" + struct.pack("<H", delay_cs) + b"\x00\x00")
            fh.write(b"\x2C" + struct.pack("<HHHHB", 0, 0, W, H, 0))
            fh.write(bytes([7]))
            data = lzw(idx)
            for j in range(0, len(data), 255):
                chunk = data[j:j + 255]
                fh.write(bytes([len(chunk)]) + chunk)
            fh.write(b"\x00")
            print("ENCODED", i + 1, "/", len(frames), flush=True)
        fh.write(b"\x3B")


if __name__ == "__main__":
    frames = render_frames()
    pal = build_palette(frames)
    write_gif(frames, pal, OUT, delay_cs=int(round(100 * STEP / 24)))
    print("GIF_DONE", OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB")
