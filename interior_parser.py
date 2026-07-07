"""Extract the room rectangles from A1's generated interior code.

Same security posture as geometry_parser.py: we never execute the LLM's
Python. A1 is told to emit ONE structured comment line that this parser keys
on, and we read it with a regex + ast.literal_eval:

    # ROOMS: [("Living","living",5,20,48,43), ("Kitchen","kitchen",48,20,70,43), ...]

Each entry is (name, kind, x_min, y_min, x_max, y_max). On any structural
problem we raise InteriorParseError; the loop treats that as a failed
iteration and asks A1 to re-emit.
"""

import ast
import re

from interior_verifier_z3 import Room
import rooms as program

_ROOMS_RE = re.compile(r"#?\s*ROOMS\s*:\s*(\[.*?\])", re.IGNORECASE | re.DOTALL)
_ALLOWED_KINDS = set(program.REQUIRED_COUNT)


class InteriorParseError(ValueError):
    pass


def parse(code: str) -> tuple[Room, ...]:
    m = _ROOMS_RE.search(code)
    if not m:
        raise InteriorParseError(
            "Missing `# ROOMS: [...]` marker as the first line of the script.")
    try:
        raw = ast.literal_eval(m.group(1))
    except (ValueError, SyntaxError) as e:
        raise InteriorParseError(f"Could not eval the ROOMS literal: {e}")

    if not isinstance(raw, (list, tuple)) or not raw:
        raise InteriorParseError(f"ROOMS must be a non-empty list; got {raw!r}.")

    out: list[Room] = []
    for i, entry in enumerate(raw):
        if not (isinstance(entry, (list, tuple)) and len(entry) == 6):
            raise InteriorParseError(
                f"Room #{i} must be (name, kind, x_min, y_min, x_max, y_max); "
                f"got {entry!r}.")
        name, kind, x0, y0, x1, y1 = entry
        if not isinstance(name, str) or not isinstance(kind, str):
            raise InteriorParseError(
                f"Room #{i}: name and kind must be strings; got {entry!r}.")
        kind = kind.strip().lower()
        if kind not in _ALLOWED_KINDS:
            raise InteriorParseError(
                f"Room #{i} '{name}': kind '{kind}' not allowed. Use one of "
                f"{sorted(_ALLOWED_KINDS)}.")
        try:
            x0, y0, x1, y1 = float(x0), float(y0), float(x1), float(y1)
        except (TypeError, ValueError):
            raise InteriorParseError(
                f"Room #{i} '{name}': coordinates must be numbers; got {entry!r}.")
        if x1 <= x0 or y1 <= y0:
            raise InteriorParseError(
                f"Room #{i} '{name}': need x_min<x_max and y_min<y_max; "
                f"got ({x0},{y0})-({x1},{y1}).")
        out.append(Room(name=name.strip(), kind=kind,
                        x_min=x0, y_min=y0, x_max=x1, y_max=y1))

    return tuple(out)
