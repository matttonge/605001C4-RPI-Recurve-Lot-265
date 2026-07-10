#!/bin/bash
# Launches the Recurve application. Logs to /home/rp/recurve_start.log.

exec > /home/rp/recurve_start.log 2>&1
set -x   # echo every command into the log for easy debugging
echo "=== start_recurve.sh booting at $(date) ==="

# Make sure DISPLAY points somewhere even if the session env didn't set it.
export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/rp/.Xauthority}"

cd /home/rp/Desktop/Recurve

# Launch a minimal WM so X11 routes keyboard focus to overrideredirect Toplevels.
if command -v openbox >/dev/null 2>&1; then
  openbox &
fi

# Auto-hide the mouse cursor after 1s of inactivity.
if command -v unclutter >/dev/null 2>&1; then
  unclutter -idle 1 -root &
fi

# Wait for X11 to be ready before issuing xrandr (autostart can fire early).
for i in 1 2 3 4 5 6 7 8 9 10; do
  xrandr --query >/dev/null 2>&1 && break
  echo "(waiting for X11... attempt $i)"
  sleep 0.5
done

# Force display to 1024x600 (the resolution the Recurve UI is built for).
# Monitor's EDID doesn't list 1024x600, so we define a custom CVT modeline.
# Errors are NOT silenced - they end up in recurve_start.log for debugging.
if command -v xrandr >/dev/null 2>&1; then
  echo "--- xrandr setup ---"
  xrandr --query
  OUTPUT="$(xrandr --query | awk '/ connected/{print $1; exit}')"
  echo "Detected output: '$OUTPUT'"
  if [ -n "$OUTPUT" ]; then
    xrandr --newmode "1024x600_60.00" 49.00 \
        1024 1072 1168 1312 \
         600  603  613  624 -hsync +vsync || echo "(newmode: already exists, OK)"
    xrandr --addmode "$OUTPUT" "1024x600_60.00" || echo "(addmode: already added, OK)"
    xrandr --output "$OUTPUT" --mode "1024x600_60.00" || \
        echo "ERROR: xrandr could not switch $OUTPUT to 1024x600"
  else
    echo "ERROR: no connected output detected; xrandr will not change resolution"
  fi
fi

set +x
echo "=== launching Python at $(date) ==="
source /home/rp/Desktop/Recurve/venv/bin/activate
exec python3 /home/rp/Desktop/Recurve/Run_Screen_1b.py
