#!/bin/bash
# Restart Recurve UI without blocking the caller.
pkill -f '/home/rp/Desktop/Recurve/Run_Screen_1b.py' 2>/dev/null || true
sleep 1
export DISPLAY=:0
export XAUTHORITY=/home/rp/.Xauthority
cd /home/rp/Desktop/Recurve
setsid bash /home/rp/Desktop/Recurve/start_recurve.sh </dev/null >/tmp/recurve-restart.log 2>&1 &
echo "spawned $!"
sleep 5
if pgrep -f 'Run_Screen_1b.py' >/dev/null; then
  echo UI_UP
  pgrep -af 'Run_Screen_1b.py'
  fuser /dev/ttyGS0 2>&1 || echo ttyGS0_free
else
  echo UI_DOWN
  tail -40 /home/rp/recurve_start.log 2>/dev/null || true
  tail -40 /tmp/recurve-restart.log 2>/dev/null || true
  exit 1
fi
