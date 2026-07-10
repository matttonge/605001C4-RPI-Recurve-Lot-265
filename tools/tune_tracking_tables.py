#!/usr/bin/env python3
"""Launcher for Pico tools/tune_tracking_tables.py"""
from __future__ import annotations
import runpy
import sys
from pathlib import Path

script = Path(__file__).resolve().parent.parent.parent / "605002C2-pico-6-17-2026" / "tools" / "tune_tracking_tables.py"
if not script.is_file():
    print(f"Not found: {script}", file=sys.stderr)
    raise SystemExit(1)
runpy.run_path(str(script), run_name="__main__")
