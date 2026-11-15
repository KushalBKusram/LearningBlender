"""Synthesises the 'Lamp Keeper' soundtrack (stdlib only) -> session-18/audio/lamp_keeper_audio.wav

Follows session-17/storyboard.md: footsteps, squeak, startle, hop boings, chain click,
warm rising tone when the lamp glows, and a soft pad under everything that fades out at the end.
Frame numbers match scripts/session_18.py (24 fps, 300 frames).
"""
import math
import os
import random
import struct
import wave

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 44100
FPS = 24
DUR = 300 / FPS + 0.5
N = int(SR * DUR)
buf = [0.0] * N
random.seed(7)


def t_of(frame):
    return (frame - 1) / FPS


def add(start, samples, gain=1.0):
    i0 = int(start * SR)
    for i, s in enumerate(samples):
        j = i0 + i
        if 0 <= j < N:
            buf[j] += s * gain


def env(n, attack=0.005, decay=0.12):
    a = max(1, int(attack * SR))
    return [min(1.0, i / a) * math.exp(-i / (decay * SR)) for i in range(n)]


def tone(freq, dur, gain=1.0, decay=0.15, f_end=None):
    n = int(dur * SR)
    e = env(n, 0.004, decay)
    out, ph = [], 0.0
    for i in range(n):
        f = freq if f_end is None else freq + (f_end - freq) * i / n
        ph += 2 * math.pi * f / SR
        out.append(math.sin(ph) * e[i] * gain)
    return out


def tick(dur=0.05, gain=0.6):
    n = int(dur * SR)
    e = env(n, 0.001, 0.012)
    return [(random.uniform(-1, 1) * 0.6 + math.sin(2 * math.pi * 160 * i / SR) * 0.8) * e[i] * gain
            for i in range(n)]


def pad(start, end, freqs, gain):
    n = int((end - start) * SR)
    out = []
    for i in range(n):
        t = i / SR
        fade = min(1.0, t / 1.5, (end - start - t) / 1.0)
        v = sum(math.sin(2 * math.pi * f * t + k) * (1.0 / (k + 1)) for k, f in enumerate(freqs))
        out.append(v * fade * gain * (0.8 + 0.2 * math.sin(2 * math.pi * 0.25 * t)))
    return out


# Soft pad (A minor / F major feel) under the whole piece; warmer once the lamp is on.
add(0, pad(0, t_of(300), [110, 164.8, 220], 0.045))
add(t_of(209), pad(0, t_of(300) - t_of(209), [174.6, 261.6, 349.2], 0.04))

# Footsteps: A walks in (frames 6..90), one tick per half second.
for f in range(6, 91, 12):
    add(t_of(f), tick(0.05, 0.55))

# S03: B's rising squeak as it peeks, plus a tiny second one on the blink.
add(t_of(100), tone(620, 0.22, 0.35, 0.18, f_end=1100))
add(t_of(126), tone(900, 0.12, 0.2, 0.08, f_end=1300))

# S04: startle blip, then a boing per take-off and a soft thud per landing.
add(t_of(134), tone(1400, 0.10, 0.4, 0.05, f_end=500))
for c in (136, 152, 168, 184):
    add(t_of(c + 3), tone(520, 0.28, 0.45, 0.14, f_end=170))
    add(t_of(c + 14), tick(0.06, 0.35))

# S05: chain click, warm rising tone as the shade glows.
add(t_of(208), tick(0.03, 0.9))
add(t_of(209), tick(0.03, 0.6))
add(t_of(212), tone(261.6, 2.0, 0.22, 1.2, f_end=523.2))
add(t_of(212), tone(392.0, 2.0, 0.12, 1.2, f_end=784.0))

# S06: B's small hops home (quieter), then a settling sigh.
for c in (246, 260, 274):
    add(t_of(c + 3), tone(420, 0.25, 0.25, 0.12, f_end=200))
add(t_of(290), tone(330, 0.6, 0.12, 0.35, f_end=220))

# Master fade-out over the final 12 frames, then normalise to -3 dB.
fade_start = int(t_of(289) * SR)
for i in range(fade_start, N):
    buf[i] *= max(0.0, 1 - (i - fade_start) / max(1, (N - fade_start)))
peak = max(abs(x) for x in buf) or 1.0
scale = 0.7 / peak

os.makedirs(f"{ROOT}/session-18/audio", exist_ok=True)
out = f"{ROOT}/session-18/audio/lamp_keeper_audio.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, x * scale)) * 32767)) for x in buf))
print("WROTE", out, round(DUR, 2), "s")
