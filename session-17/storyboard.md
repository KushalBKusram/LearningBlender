# Session 17 — Capstone Plan: "The Lamp Keeper"

12.5-second narrative short · 300 frames @ 24 fps · 1280x720 final (640x360 for blocking passes)
Contact sheet: `storyboard_panels.png` (blockout renders in `panels/`, rebuilt by `scripts/session_17.py`)

## Logline
A patrolling segmented robot finds a shy round creature hiding behind a lamp. Instead of chasing it, the robot turns the lamp on, and the creature returns to curl up in the light.

## The one story beat: DISCOVERY -> KINDNESS
A discovers B (surprise). B bolts (chase impulse). A answers with a gentle action instead of pursuit: it switches the lamp on (resolution). Everything in the piece serves that single pivot.

## Characters
| | Character A — "Keeper" | Character B — "Mote" |
|---|---|---|
| Design | Segmented robot: box torso, pelvis, head, 2 arms, 2 legs (about 1.3 units tall) | Round orange creature (radius about 0.35), two big eyes, no limbs |
| Motion language | Stiff, deliberate; head turns lead body turns | Squash and stretch; hops; fast, skittish |
| Built in | Session 12 (rig: Root / Spine / Head + limb bones), Session 13 (walk and reach actions) | Session 10 (sculpt a rounded body), Session 11 (bounce / squash-stretch) |
| Prop | Session 4 lamp (base, pole, dome shade, ridge ring); Session 5 materials | |

## Shot list (24 fps, totals 300 frames)
| # | Shot | Frames | Range | Dur | Action |
|---|---|---|---|---|---|
| S01 | Wide establishing | 48 | 001-048 | 2.0s | Empty room, lamp unlit. A enters frame left, walking. |
| S02 | Medium tracking | 48 | 049-096 | 2.0s | Camera follows A past the lamp; A stops, head turns toward the base. |
| S03 | Close-up (B) | 36 | 097-132 | 1.5s | B's eyes peek from behind the lamp base, then blink. |
| S04 | Two-shot | 54 | 133-186 | 2.25s | B startles, hops across the room (squash/stretch). A's arm lifts, then hesitates. |
| S05 | Low angle | 54 | 187-240 | 2.25s | A reaches up and pulls the lamp chain. Shade glows warm; light pool grows. |
| S06 | Wide resolve | 60 | 241-300 | 2.5s | B returns slowly and curls into the light pool. A sits. Hold, then fade to black over the last 12 frames. |

Check: 48 + 48 + 36 + 54 + 54 + 60 = **300**.

## Camera plan
Lenses and positions match the Session 7 vocabulary (`_aimed_camera`: track-to target empties, so cameras can be re-aimed by moving the target).
- S01: 28mm, high wide, at (6, -7, 2.4), target (-0.5, 0, 0.9). Static.
- S02: 40mm, at (-0.5, -5.2, 1.2). Keyframe the camera or its target to trail A over 48 frames.
- S03: 85mm, f/1.4 depth of field focused on B's eyes, at (1.5, -1.7, 0.6).
- S04: 35mm, locked off, at (0, -6, 1.4), so B's hop reads across the frame.
- S05: 22-24mm, low (z = 0.15), looking up at (0, 0, 1.2), for A's reach and the glow.
- S06: 32mm, at (4.5, -5, 1.7). Slow 10% push-in over the shot.

## Lighting plan (Session 6)
- S01-S04: Studio setup (key / fill / rim), slightly dimmed. Lamp shade stays unlit.
- S05: On the glow frame, ramp shade Emission Strength 0 -> 6 and a warm point light (energy 0 -> 300) over about 12 frames.
- S06: Warm key from the lamp only, cool fill from the room. Fade to black by animating world strength and exposure to 0 in the last 12 frames.

## Audio plan
- Tempo: 120 bpm (matches the Session 16 click track `session-16/footage/click_track.wav`), so one beat is 12 frames. Cuts land on beats where possible: S02 at f49 (beat 5), S04 at f133, S06 at f241.
- Footsteps: soft tick on A's foot plants (S01-S02), about every 12 frames.
- S03: a tiny rising "squeak" as B peeks.
- S04: a short bounce "boing" per hop contact.
- S05: a mechanical "click" at the chain pull, then a warm rising tone as the lamp glows.
- S06: sustained soft pad under the final shot, fading with the picture.
- Source: freesound.org / pixabay (CC0 or attributed); record the license of each file in this folder.

## Asset checklist (mapped to sessions)
| Asset | Source session | Status entering Session 18 |
|---|---|---|
| Lamp (base, pole, shade, ridge array) | 4 | Built; re-use `session-04` file |
| Lamp materials (metal, plastic, accent) | 5 | Built; re-use `session-05` |
| Lighting setups | 6 | Studio rig available in `session-06`; copy its lights |
| Camera set | 7 | Cameras scripted; adapt positions per shot list above |
| Character B body (round, sculpted) | 10 | Sculpt a rounded body; blockout sphere is the fallback |
| B squash/stretch hop | 11 | Reuse the bouncing-ball keyframe pattern from `session-11` |
| Character A rig (Root / Spine / Head + limbs) | 12 | Extend the 3-bone rig with arm and leg bones |
| A walk cycle and reach pose | 13 | Cycle (24 frames) for S01-S02; one-off reach for S04-S05 |
| Particle dust / glow motes (optional) | 14 | Nice-to-have for S05-S06; cut first if behind |
| Compositing (glare, grade, vignette) | 15 | Apply once to every shot for a consistent look |
| Edit: movie strips, crossfades, title, audio | 16 | See "VSE handoff" below |

## Schedule (suggested, per remaining session time)
1. Block A and B at final scale; set the six cameras; render 6 blocking stills (compare to `storyboard_panels.png`).
2. Animate A (walk, head turn, reach); animate B (peek, hop, settle).
3. Lighting passes, including the S05 glow ramp; first low-res test renders (640x360, Eevee).
4. Final renders at 1280x720; compositing grade; audio gathering.
5. Edit in the VSE; export MP4; review and polish. Reserve at least 20% of the time for step 5.

## Scope guardrails (cut list, in order)
1. Particle motes (Session 14 extras).
2. Sculpted B (use the smooth sphere with eyes).
3. Walk cycle polish (use a simple slide + bob).
4. Crossfades (use hard cuts).
The five things that must exist: both characters, the lamp, the glow moment, six shots, final audio.

## VSE handoff (for Session 18)
Reuse the Session 16 timeline conventions in `session-16/session-16-start.blend`:
- Channel 1 and 2: alternate shot movie strips (S01 on 1, S02 on 2, ...) so adjacent shots can overlap.
- Channel 3: Cross effect strips spanning each overlap (8-frame overlaps in the demo; cuts on beats are fine here, so use 0-4 frame crossfades, or none).
- Channel 4: title text strip (shorten to the first 24 frames, or remove).
- Channel 5: audio. Place the click-track-aligned music bed here, with one-shot SFX on channel 6+.
- Scene settings: 24 fps, frames 1-300, output MPEG4 / H.264 (set via `render.image_settings.media_type = 'VIDEO'` in Blender 5.3).
- Note for the Session 18 skeleton: `build_18` in `build_session.py` uses placeholder color strips at 25 fps with 3 shots; update it to 24 fps and the six shots above (ranges in the table).
