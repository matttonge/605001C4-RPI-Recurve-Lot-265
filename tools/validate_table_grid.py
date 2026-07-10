#!/usr/bin/env python3
"""Run full-grid table validation on the Pico (see 605002C2-pico tools)."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path

_PICO_TOOLS = (
    Path(__file__).resolve().parents[2]
    / "605002C2-pico-6-17-2026"
    / "tools"
    / "validate_table_grid.py"
)

if not _PICO_TOOLS.is_file():
    print(f"Missing Pico tool: {_PICO_TOOLS}", file=sys.stderr)
    raise SystemExit(1)

sys.argv[0] = str(_PICO_TOOLS)
runpy.run_path(str(_PICO_TOOLS), run_name="__main__")
