"""Bass-320 Excel field mapping for Recurve measurement rows.

Tree columns (after Index) depend on Prox Left / cone_flip:

  cone_flip False (default): Dist OD, Dist Cone, Body, A1, A2, A3, Prox Cone, Prox OD
  cone_flip True:            Prox OD, Prox Cone, Body, A1, A2, A3, Dist Cone, Dist OD

Bass-320 template columns C–J are always distal→proximal order.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple, Union

# Bass-320 C–J labels (documentation / tests).
BASS320_FIELD_LABELS = (
    "Dist. OD (inch)",
    "Dist. Cone Length (mm)",
    "Body Length (mm)",
    "ΦA1 (mm)",
    "ΦA2 (mm)",
    "ΦA3 (mm)",
    "Prox. Cone Length (mm)",
    "Prox.OD (inch)",
)

BASS320_FIELD_COUNT = 8

# When cone_flip is True, tree measurement indices remapped to Bass-320 C–J.
_CONE_FLIP_TO_BASS320 = (7, 6, 2, 3, 4, 5, 1, 0)


def format_cell_value(value: object) -> str:
    """Format a tree cell for Excel / serial transfer (empty string for blanks)."""
    if value is None:
        return ""
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return ""
        try:
            return format_cell_value(float(s))
        except ValueError:
            return s
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if value != value:  # NaN
            return ""
        if value == int(value) and abs(value) < 1e12:
            return str(int(value))
        # Prefer compact decimals; strip trailing zeros.
        text = f"{value:.6f}".rstrip("0").rstrip(".")
        return text if text else "0"
    return str(value).strip()


def _measurement_values(row_values: Sequence[object]) -> List[object]:
    """Return the 8 measurement cells from a tree row (skip Index at [0])."""
    values = list(row_values)
    if len(values) >= BASS320_FIELD_COUNT + 1:
        return values[1 : 1 + BASS320_FIELD_COUNT]
    if len(values) == BASS320_FIELD_COUNT:
        return values
    # Pad short rows so callers always get 8 slots.
    padded = values[1:] if len(values) > 1 else list(values)
    while len(padded) < BASS320_FIELD_COUNT:
        padded.append("")
    return padded[:BASS320_FIELD_COUNT]


def tree_row_to_bass320_fields(
    row_values: Sequence[object],
    cone_flip: bool = False,
) -> Tuple[str, ...]:
    """Map one tree row to 8 Bass-320 C–J string fields."""
    meas = _measurement_values(row_values)
    if cone_flip:
        ordered = [meas[i] for i in _CONE_FLIP_TO_BASS320]
    else:
        ordered = meas
    return tuple(format_cell_value(v) for v in ordered)


def last_tree_row_values(tree) -> Optional[Tuple[object, ...]]:
    """Return values of the last tree row, or None if empty."""
    children = tree.get_children()
    if not children:
        return None
    last_iid = children[-1]
    values = tree.item(last_iid, "values")
    if values is None:
        return None
    return tuple(values)


def last_row_to_bass320_fields(tree, cone_flip: bool = False) -> Optional[Tuple[str, ...]]:
    """Convenience: last tree row → Bass-320 fields, or None if no data."""
    row = last_tree_row_values(tree)
    if row is None:
        return None
    return tree_row_to_bass320_fields(row, cone_flip=cone_flip)


def format_ok_response(fields: Iterable[str]) -> str:
    """Build protocol OK line (without trailing newline)."""
    parts = ["OK"] + [str(f) for f in fields]
    if len(parts) != 1 + BASS320_FIELD_COUNT:
        raise ValueError(
            f"expected {BASS320_FIELD_COUNT} fields, got {len(parts) - 1}"
        )
    return "\t".join(parts)


def format_err_response(message: str) -> str:
    """Build protocol ERR line (without trailing newline)."""
    msg = (message or "error").replace("\t", " ").replace("\n", " ").strip()
    return f"ERR\t{msg}"


def handle_get_last_row_command(
    tree,
    cone_flip: bool = False,
) -> str:
    """Process GET_LAST_ROW; return response line without newline."""
    fields = last_row_to_bass320_fields(tree, cone_flip=cone_flip)
    if fields is None:
        return format_err_response("No data")
    return format_ok_response(fields)


def parse_request_line(line: Union[str, bytes]) -> str:
    """Normalize a request line to an uppercase command name."""
    if isinstance(line, bytes):
        line = line.decode("utf-8", errors="replace")
    return line.strip().upper()
