#!/bin/bash
# Rebuilds every session file from scratch, in dependency order. Log: scripts/rebuild_all.log
cd "$(dirname "$0")/.." || exit 1
B="${BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"   # set BLENDER=... on other systems
LOG=scripts/rebuild_all.log
: > "$LOG"

run() {  # run <label> <blender args...>
  label="$1"; shift
  start=$(date +%s)
  out=$("$B" --background "$@" 2>&1)
  code=$?
  if echo "$out" | grep -q "Traceback"; then code=99; fi
  echo "[$(( $(date +%s) - start ))s] $label -> exit $code" | tee -a "$LOG"
  if [ $code -ne 0 ]; then echo "$out" | grep -B2 -A12 "Traceback" | head -30 >> "$LOG"; fi
}

for n in 1 2 3 4 5 6 7; do run "session $n" --python scripts/build_session.py -- $n; done
run "session 8"  --python scripts/session_08.py
run "session 9"  --python scripts/session_09.py
run "session 10" --python scripts/session_10.py
run "session 11" --python scripts/session_11.py
run "session 12" --python scripts/session_12.py
run "session 13" --python scripts/session_13.py
run "session 13 filmstrip" session-13/session-13-start.blend --python scripts/session_13.py -- filmstrip
run "session 14" --python scripts/session_14.py
run "session 15" --python scripts/session_15.py
for c in 1 2 3; do run "session 16 clip $c" --python scripts/session_16.py -- clips $c; done
run "session 16 vse" --python scripts/session_16.py -- vse
run "session 16 preview" session-16/session-16-start.blend --python scripts/session_16.py -- preview
for p in 1 2 3 4 5 6; do run "session 17 panel $p" --python scripts/session_17.py -- panel $p; done
run "session 17 sheet" --python scripts/session_17.py -- sheet
python3 scripts/audio_18.py | tee -a "$LOG"
run "session 18 build" --python scripts/session_18.py -- build
run "session 18 preview" session-18/session-18-start.blend --python scripts/session_18.py -- preview
run "session 18 dense" session-18/session-18-start.blend --python scripts/session_18.py -- dense
run "session 18 glow" session-18/session-18-start.blend --python scripts/session_18.py -- glow
echo "ALL DONE" | tee -a "$LOG"
