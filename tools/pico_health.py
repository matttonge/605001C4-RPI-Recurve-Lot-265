#!/usr/bin/env python3
"""Pico health check — see 605002C2-pico-6-17-2026/tools/pico_health.py"""

from pathlib import Path
import runpy

_PICO_TOOLS = (
    Path(__file__).resolve().parents[2]
    / "605002C2-pico-6-17-2026"
    / "tools"
    / "pico_health.py"
)
runpy.run_path(str(_PICO_TOOLS), run_name="__main__")
