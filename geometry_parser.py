"""Extract house corners + door position from A1's generated Python code.

A1 is instructed to emit two structured comment lines that this parser keys on:

    # HOUSE_CORNERS: [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]   # CW or CCW, axis-aligned rect
    # DOOR: (x, y)

This avoids executing untrusted LLM code while still giving the verifier
concrete numbers. If the markers are missing or malformed, raise — the loop
will treat that as a parse failure and ask A1 to re-emit.
"""

import ast
import re

from verifier_z3 import HouseGeometry

_HOUSE_RE = re.compile(r"#\s*HOUSE_CORNERS\s*:\s*(\[.*?\])", re.IGNORECASE)
_DOOR_RE = re.compile(r"#\s*DOOR\s*:\s*(\([^)]*\))", re.IGNORECASE)


class GeometryParseError(ValueError):
    pass


def parse(code: str) -> HouseGeometry:
    m_house = _HOUSE_RE.search(code)
    if not m_house:
        raise GeometryParseError(
            "Missing `# HOUSE_CORNERS: [...]` marker in generated code.")
    m_door = _DOOR_RE.search(code)
    if not m_door:
        raise GeometryParseError(
            "Missing `# DOOR: (x, y)` marker in generated code.")

    try:
        corners = ast.literal_eval(m_house.group(1))
        door = ast.literal_eval(m_door.group(1))
    except (ValueError, SyntaxError) as e:
        raise GeometryParseError(f"Could not eval geometry literals: {e}")

    if not (isinstance(corners, list) and len(corners) == 4
            and all(isinstance(c, tuple) and len(c) == 2 for c in corners)):
        raise GeometryParseError(
            f"HOUSE_CORNERS must be 4 (x,y) tuples; got {corners!r}.")
    if not (isinstance(door, tuple) and len(door) == 2):
        raise GeometryParseError(f"DOOR must be a 2-tuple; got {door!r}.")

    return HouseGeometry(
        corners=tuple((float(x), float(y)) for x, y in corners),
        door=(float(door[0]), float(door[1])),
    )
