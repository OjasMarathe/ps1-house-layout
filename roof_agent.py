"""Roof Plan Agent — geometry engine (Cluster 4, Output & Export).

Owner: Ojas.  Input: top-floor footprint(s) + elevation data (from the
Elevation / Multi-floor cluster, via the Agent Manager).  Output: a roof polygon
set tagged "view_type": "roof" that goes to the DXF Generator.

Design goals (the acceptance checklist):
  1. Roof outline matches the top-floor footprint EXACTLY (no overhang error / gap).
  2. Handles multi-floor & uneven elevation — one stepped roof *section* per level.
  3. Emitted as its own artifact (see roof_dxf.py / roof_render.py).
  4. Respects roof setback / fire clearance (checked in roof_verifier_z3.py).
  5. Pitch + drainage direction are specified per plane, never just a flat outline.

Compass (matches plot.py): +x = East, +y = North.  Units = feet.
Roof types: gable | hip | shed (mono-pitch) | flat (min drainage slope).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from math import atan, degrees, hypot

from verifier_z3 import _point_in_polygon   # reuse the ray-cast point-in-polygon
from roof_vents import ventilation, slope_factor

# compass azimuth (degrees) that water flows for each drain side
_AZ = {"N": 0.0, "E": 90.0, "S": 180.0, "W": 270.0}


def _bbox(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return min(xs), min(ys), max(xs), max(ys)


def _area(poly):
    s = 0.0
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        s += x1 * y2 - x2 * y1
    return abs(s) / 2.0


def _is_rect(poly, tol=1e-6):
    """True if poly is a 4-corner axis-aligned rectangle."""
    if len(poly) != 4:
        return False
    x0, y0, x1, y1 = _bbox(poly)
    corners = {(round(x0, 6), round(y0, 6)), (round(x1, 6), round(y0, 6)),
               (round(x1, 6), round(y1, 6)), (round(x0, 6), round(y1, 6))}
    got = {(round(px, 6), round(py, 6)) for px, py in poly}
    return got == corners and abs(_area(poly) - (x1 - x0) * (y1 - y0)) < 1e-4


def parse_pitch(pitch):
    """'4:12' -> (rise, run, ratio, slope_pct, angle_deg). Also accepts a float ratio."""
    if isinstance(pitch, (int, float)):
        ratio = float(pitch); rise, run = ratio * 12, 12.0
    else:
        rise, run = (float(x) for x in str(pitch).split(":"))
        ratio = rise / run
    return rise, run, ratio, ratio * 100.0, degrees(atan(ratio))


def _rect(poly):
    return _bbox(poly)


def _rectangle_outline(x0, y0, x1, y1):
    return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]


# --------------------------------------------------------------------------- #
#  Roof-type builders (rectangular footprint) — return the geometry payload
# --------------------------------------------------------------------------- #
def _gable(x0, y0, x1, y1, top_h, pr, axis):
    W, D = x1 - x0, y1 - y0
    if axis == "auto":
        axis = "ew" if W >= D else "ns"     # ridge along the longer dimension
    if axis == "ew":                        # ridge runs E-W, planes slope N & S
        ym = (y0 + y1) / 2
        rise = (D / 2) * pr
        ridge = [[x0, ym], [x1, ym]]
        planes = [
            {"id": "south", "polygon": _rectangle_outline(x0, y0, x1, ym), "drains_to": "S"},
            {"id": "north", "polygon": _rectangle_outline(x0, ym, x1, y1), "drains_to": "N"},
        ]
    else:                                   # ridge runs N-S, planes slope E & W
        xm = (x0 + x1) / 2
        rise = (W / 2) * pr
        ridge = [[xm, y0], [xm, y1]]
        planes = [
            {"id": "west", "polygon": _rectangle_outline(x0, y0, xm, y1), "drains_to": "W"},
            {"id": "east", "polygon": _rectangle_outline(xm, y0, x1, y1), "drains_to": "E"},
        ]
    return dict(ridge=ridge, hips=[], planes=planes,
                ridge_height_ft=round(top_h + rise, 3), eave_height_ft=round(top_h, 3))


def _hip(x0, y0, x1, y1, top_h, pr, axis):
    W, D = x1 - x0, y1 - y0
    if axis == "auto":
        axis = "ew" if W >= D else "ns"
    xm, ym = (x0 + x1) / 2, (y0 + y1) / 2
    rise = (min(W, D) / 2) * pr
    if axis == "ew":                        # ridge shortened along E-W, hips at E & W ends
        rx0, rx1 = x0 + D / 2, x1 - D / 2
        ridge = [[rx0, ym], [rx1, ym]]
        hips = [[[x0, y0], [rx0, ym]], [[x1, y0], [rx1, ym]],
                [[x0, y1], [rx0, ym]], [[x1, y1], [rx1, ym]]]
        planes = [
            {"id": "south", "polygon": [[x0, y0], [x1, y0], [rx1, ym], [rx0, ym]], "drains_to": "S"},
            {"id": "north", "polygon": [[x0, y1], [x1, y1], [rx1, ym], [rx0, ym]], "drains_to": "N"},
            {"id": "west", "polygon": [[x0, y0], [x0, y1], [rx0, ym]], "drains_to": "W"},
            {"id": "east", "polygon": [[x1, y0], [x1, y1], [rx1, ym]], "drains_to": "E"},
        ]
    else:                                   # ridge along N-S, hips at N & S ends
        ry0, ry1 = y0 + W / 2, y1 - W / 2
        ridge = [[xm, ry0], [xm, ry1]]
        hips = [[[x0, y0], [xm, ry0]], [[x1, y0], [xm, ry0]],
                [[x0, y1], [xm, ry1]], [[x1, y1], [xm, ry1]]]
        planes = [
            {"id": "west", "polygon": [[x0, y0], [x0, y1], [xm, ry1], [xm, ry0]], "drains_to": "W"},
            {"id": "east", "polygon": [[x1, y0], [x1, y1], [xm, ry1], [xm, ry0]], "drains_to": "E"},
            {"id": "south", "polygon": [[x0, y0], [x1, y0], [xm, ry0]], "drains_to": "S"},
            {"id": "north", "polygon": [[x0, y1], [x1, y1], [xm, ry1]], "drains_to": "N"},
        ]
    return dict(ridge=ridge, hips=hips, planes=planes,
                ridge_height_ft=round(top_h + rise, 3), eave_height_ft=round(top_h, 3))


def _shed(x0, y0, x1, y1, top_h, pr, low_side):
    """Single plane, high edge (ridge) opposite the low (drainage) side."""
    W, D = x1 - x0, y1 - y0
    run = D if low_side in ("N", "S") else W
    rise = run * pr
    high = {"N": [[x0, y1], [x1, y1]], "S": [[x0, y0], [x1, y0]],
            "E": [[x1, y0], [x1, y1]], "W": [[x0, y0], [x0, y1]]}
    ridge = high[{"N": "S", "S": "N", "E": "W", "W": "E"}[low_side]]   # high edge is opposite low
    planes = [{"id": "slope", "polygon": _rectangle_outline(x0, y0, x1, y1), "drains_to": low_side}]
    return dict(ridge=ridge, hips=[], planes=planes,
                ridge_height_ft=round(top_h + rise, 3), eave_height_ft=round(top_h, 3))


def _section_geometry(x0, y0, x1, y1, top_h, rtype, pr, axis, low_side):
    if rtype == "gable":
        return _gable(x0, y0, x1, y1, top_h, pr, axis)
    if rtype == "hip":
        return _hip(x0, y0, x1, y1, top_h, pr, axis)
    # shed and flat are both single-plane mono-pitch (flat just uses a tiny pitch)
    return _shed(x0, y0, x1, y1, top_h, pr, low_side)


def build_section(level: dict, roof_spec: dict) -> dict:
    """Build one roof section for one building level.

    A level may carry its own `roof_spec` that overrides the global one — so a
    stepped design can have e.g. a gable over the house and a shed over the garage.
    """
    roof_spec = {**(roof_spec or {}), **level.get("roof_spec", {})}
    poly = [[float(x), float(y)] for x, y in level["footprint"]]
    top_h = float(level.get("top_height_ft", 0.0))
    x0, y0, x1, y1 = _bbox(poly)

    rtype = roof_spec.get("type", "gable")
    # a genuinely flat roof still needs drainage — model it as a shallow mono-pitch
    pitch = roof_spec.get("pitch", "0.25:12" if rtype == "flat" else "4:12")
    _, _, pr, slope_pct, angle = parse_pitch(pitch)
    axis = roof_spec.get("ridge_axis", "auto")
    low_side = roof_spec.get("drain_side", "N")
    overhang = float(roof_spec.get("overhang_ft", 0.0))

    geo = _section_geometry(x0, y0, x1, y1, top_h,
                            "gable" if rtype not in ("gable", "hip", "shed", "flat") else rtype,
                            pr, axis, low_side)
    # annotate each plane with slope + azimuth
    for pl in geo["planes"]:
        pl["slope_pct"] = round(slope_pct, 1)
        pl["azimuth_deg"] = _AZ[pl["drains_to"]]

    outline = poly if not _is_rect(poly) else _rectangle_outline(x0, y0, x1, y1)
    # sloped roof area + eave overhang line + code ventilation (IRC R806.2)
    flat_area = _area(outline)
    roof_area = flat_area * slope_factor(pr)
    perim = sum(hypot(outline[i][0] - outline[i - 1][0], outline[i][1] - outline[i - 1][1])
                for i in range(len(outline)))
    eave = float(roof_spec.get("eave_overhang_ft", 1.5))          # 1'-6" default, like a real sheet
    eo = [[round(x0 - eave, 2), round(y0 - eave, 2)], [round(x1 + eave, 2), round(y0 - eave, 2)],
          [round(x1 + eave, 2), round(y1 + eave, 2)], [round(x0 - eave, 2), round(y1 + eave, 2)]]
    return {
        "level": level.get("level", 1),
        "name": level.get("name", f"level_{level.get('level', 1)}"),
        "type": rtype,
        "pitch": pitch,
        "pitch_ratio": round(pr, 5),
        "slope_pct": round(slope_pct, 1),
        "slope_angle_deg": round(angle, 1),
        "outline": [[round(px, 3), round(py, 3)] for px, py in outline],
        "overhang_ft": overhang,
        "eave_overhang_ft": eave,
        "eave_outline": eo,
        "roof_area_sqft": round(roof_area, 1),
        "ventilation": ventilation(roof_area, perim),
        "is_rectangular": _is_rect(poly),
        "drainage": sorted({pl["drains_to"] for pl in geo["planes"]}),
        **geo,
    }


def generate_roof(levels, roof_spec=None, session_id=None) -> dict:
    """Generate the full roof plan: one section per building level (stepped)."""
    roof_spec = roof_spec or {}
    sections = [build_section(lv, roof_spec) for lv in levels]
    return {
        "session_id": session_id,
        "view_type": "roof",
        "generated_by": "roof_plan_agent",
        "n_sections": len(sections),
        "roof_sections": sections,
    }


# --------------------------------------------------------------------------- #
#  Skylights / sunroofs — driven by the Window/Livability daylight scores
# --------------------------------------------------------------------------- #
SKYLIGHT_MIN_SCORE = 45.0                          # Aadi's "poor" daylight cutoff (0-100)
SKYLIGHT_SIZE_FT = 4.0                             # a ~4 x 4 ft skylight
BRIGHT_SECTORS = ("S", "SE", "SW", "E", "W")       # sun-facing roof planes (N. hemisphere)


def _centroid(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _best_plane(section, x, y):
    """The roof plane covering (x, y); prefer a sun-facing one so the skylight gains light."""
    hits = [pl for pl in section["planes"] if _point_in_polygon((x, y), pl["polygon"])]
    if not hits:
        hits = list(section["planes"])
    hits.sort(key=lambda pl: (pl["drains_to"] not in BRIGHT_SECTORS, pl["drains_to"] != "S"))
    return hits[0] if hits else None


def add_skylights(roof, top_rooms, min_score=SKYLIGHT_MIN_SCORE, size_ft=SKYLIGHT_SIZE_FT):
    """Place a skylight over each UNDER-LIT top-floor room, on its sunniest roof plane.

    `top_rooms`: [{name/id, type, polygon, daylight_score}]  — the daylight_score comes
    from the Window / Livability Agent (Aadi). Rooms scoring below `min_score` are the
    ones that need extra daylight, so the roof puts a sunroof above them.
    """
    sections = roof.get("roof_sections") or []
    roof["n_skylights"] = 0
    if not sections or not top_rooms:
        return roof
    top = max(sections, key=lambda s: s["eave_height_ft"])   # topmost section
    fx0, fy0, fx1, fy1 = _bbox(top["outline"])
    sky = []
    for room in top_rooms:
        score = room.get("daylight_score", room.get("daylight"))
        if score is None or float(score) >= min_score:
            continue
        poly = [[float(x), float(y)] for x, y in room.get("polygon", [])]
        if not poly:
            continue
        cx, cy = _centroid(poly)
        pl = _best_plane(top, cx, cy)
        if pl is None:
            continue
        h = size_ft / 2.0
        cx = min(max(cx, fx0 + h), fx1 - h)          # keep it inside the roof outline
        cy = min(max(cy, fy0 + h), fy1 - h)
        sky.append({
            "room": room.get("name", room.get("id")), "type": "skylight",
            "center": [round(cx, 2), round(cy, 2)],
            "width_ft": size_ft, "length_ft": size_ft,
            "outline": [[round(cx - h, 2), round(cy - h, 2)], [round(cx + h, 2), round(cy - h, 2)],
                        [round(cx + h, 2), round(cy + h, 2)], [round(cx - h, 2), round(cy + h, 2)]],
            "on_plane": pl["id"], "faces": pl["drains_to"],
            "reason": f"low daylight (score {int(float(score))}) — sunroof added for extra light",
        })
    top["skylights"] = sky
    roof["n_skylights"] = len(sky)
    return roof


if __name__ == "__main__":
    # quick self-demo: a main house + a stepped garage at a lower level
    demo = generate_roof(
        levels=[
            {"level": 1, "name": "main", "footprint": [[13.96, 20], [66.04, 20], [66.04, 63.15], [13.96, 63.15]], "top_height_ft": 20.0},
            {"level": 0, "name": "garage", "footprint": [[5, 5], [25, 5], [25, 18], [5, 18]], "top_height_ft": 10.0},
        ],
        roof_spec={"type": "gable", "pitch": "5:12"},
    )
    for s in demo["roof_sections"]:
        print(f"{s['name']:8s} {s['type']:5s} pitch {s['pitch']} eave {s['eave_height_ft']}ft "
              f"ridge {s['ridge_height_ft']}ft drains {s['drainage']} planes {len(s['planes'])}")
