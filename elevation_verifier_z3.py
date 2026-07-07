"""Z3 verifier for side-view / facade elevations (Cluster 4, Side Views Agent).

Consumes the Side View Agent's `compiled_coordinates.json` DIRECTLY and
auto-converts metres->feet, so the caller passes their output as-is. Driven by the
Constraint Engine ruleset (max_height_ft + room_specs.requires_exterior_window).

Checks:
  height_within_max        building height <= zoning max_height_ft
  opening_within_wall       every door/window: sill + height <= its wall height
  room_within_footprint     every room polygon lies inside the building footprint
  requires_exterior_window  rooms whose room_spec needs a window actually have one

Numeric comparisons go through verifier_z3._violated (deterministic Z3 proofs).
"""
from dataclasses import dataclass

from verifier_z3 import _violated

M_TO_FT = 3.280839895


@dataclass(frozen=True)
class ElevationViolation:
    rule: str
    measured: float
    required: float
    message: str


def _scale(view) -> float:
    """metres -> feet if the payload says so, else 1.0."""
    u = str(view.get("units", "feet")).lower()
    return M_TO_FT if u in ("metres", "meters", "m") else 1.0


def _footprint_ft(view, s):
    fp = view.get("footprint") or {}
    if {"x_min", "y_min", "x_max", "y_max"} <= set(fp):
        return fp["x_min"] * s, fp["y_min"] * s, fp["x_max"] * s, fp["y_max"] * s
    b = view.get("boundary_3d") or view.get("boundary") or []
    xs = [p[0] * s for p in b]; ys = [p[1] * s for p in b]
    return min(xs), min(ys), max(xs), max(ys)


def check_elevation(view: dict, max_height_ft=None, room_specs=None, tol_ft: float = 0.1) -> list:
    """Return a list of ElevationViolation; empty == a legal, consistent side view."""
    v = []
    s = _scale(view)
    fx0, fy0, fx1, fy1 = _footprint_ft(view, s)
    rooms = view.get("rooms", [])
    room_specs = room_specs or {}

    # building height = tallest ceiling (+ roof rise if a roof is attached)
    ceil_ft = max((float(r.get("ceiling_z_m", r.get("ceiling_z_ft", 0)) if "ceiling_z_m" in r
                         else r.get("ceiling_z_ft", 0)) * (s if "ceiling_z_m" in r else 1.0)
                   for r in rooms), default=0.0)
    roof = view.get("roof") or {}
    rise = max(float(roof.get("ridge_height_ft", 0)) - float(roof.get("eave_height_ft", 0)), 0.0)
    height = ceil_ft + rise

    # 1) height within the zoning maximum
    if max_height_ft is not None and _violated(float(max_height_ft), height):
        v.append(ElevationViolation("height_within_max", round(height, 2), round(float(max_height_ft), 2),
            f"Building height {height:.1f} ft exceeds zoning max {float(max_height_ft):.0f} ft."))

    # 2) every opening fits under its wall (sill + height <= wall height)
    by_name = {r.get("name"): r for r in rooms}

    def wall_ht(room_name):
        r = by_name.get(room_name)
        if r and "ceiling_z_m" in r:
            return (float(r["ceiling_z_m"]) - float(r.get("floor_z_m", 0))) * s
        return ceil_ft

    for kind, items in (("door", view.get("doors", [])), ("window", view.get("windows", []))):
        for op in items:
            rn = op.get("room") or (op.get("rooms") or [None])[0]
            top = float(op.get("sill_height_ft", 0)) + float(op.get("height_ft", 0))
            wh = wall_ht(rn)
            if _violated(wh, top):
                v.append(ElevationViolation("opening_within_wall", round(top, 2), round(wh, 2),
                    f"{kind} in {rn}: sill+height {top:.1f} ft exceeds its {wh:.1f} ft wall."))

    # 3) every room lies within the footprint
    for r in rooms:
        for pt in r.get("polygon_3d", r.get("polygon", [])):
            X, Y = pt[0] * s, pt[1] * s
            if X < fx0 - tol_ft or X > fx1 + tol_ft or Y < fy0 - tol_ft or Y > fy1 + tol_ft:
                v.append(ElevationViolation("room_within_footprint", 0.0, 0.0,
                    f"{r.get('name')} vertex ({X:.1f},{Y:.1f}) ft is outside the footprint "
                    f"[{fx0:.1f},{fy0:.1f}]-[{fx1:.1f},{fy1:.1f}] ft."))
                break

    # 4) ruleset-driven: rooms whose spec needs an exterior window must have one
    if room_specs:
        wins = {}
        for w in view.get("windows", []):
            wins[w.get("room")] = wins.get(w.get("room"), 0) + 1
        for r in rooms:
            spec = room_specs.get(r.get("type"), {})
            if spec.get("requires_exterior_window") and wins.get(r.get("name"), 0) < 1:
                v.append(ElevationViolation("requires_exterior_window", 0.0, 1.0,
                    f"{r.get('name')} ({r.get('type')}) requires an exterior window but has none."))
    return v
