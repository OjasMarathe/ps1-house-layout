"""Roof -> elevation silhouettes (for the Side-View / Elevation Agent, Dhwani).

An elevation is an orthographic side view: we drop one plan axis and draw height (z).
For each of the four cardinal elevations we return the roof's top outline as a simple
polyline of [u, z] points, where `u` is the plan coordinate that runs left-right in
that view and `z` is height in feet. The elevation agent just draws the polyline; no
3D projection on her side, so her side view is guaranteed to match this roof.

Rules (uniform pitch):
  - You look at a gable/hip END  -> triangle (apex at the ridge).
  - You look at a gable SIDE      -> ridge line straight across the top.
  - You look at a hip SIDE        -> trapezoid (ridge inset, hips slope to the corners).
  - shed -> single sloped line (or the high edge, seen end-on). flat -> level line.
"""

# view name -> plan axis that is horizontal on screen, and whether to mirror for an
# outside-looking-in view (east on the right when you face the facade).
VIEWS = [
    ("south", "x", False),   # stand south, look north: +x to the right
    ("north", "x", True),    # stand north, look south: +x to the left (mirror)
    ("east",  "y", False),   # stand east,  look west:  +y to the right
    ("west",  "y", True),    # stand west,  look east:  +y to the left (mirror)
]


def _ridge_axis(sec):
    r = sec.get("ridge") or []
    if len(r) >= 2:
        (ax, ay), (bx, by) = r[0], r[1]
        if abs(ax - bx) < 1e-6 and abs(ay - by) > 1e-6:
            return "y"                     # ridge runs N-S
        if abs(ay - by) < 1e-6 and abs(ax - bx) > 1e-6:
            return "x"                     # ridge runs E-W
    return "x"


def _bbox(sec):
    pts = sec.get("eave_outline") or sec.get("outline") or [[0, 0]]
    xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
    return min(xs), max(xs), min(ys), max(ys)


def _section_profile(sec, haxis):
    """Roof top silhouette for one section in a view whose horizontal axis is `haxis`."""
    eh = float(sec.get("eave_height_ft", 0.0))
    rh = float(sec.get("ridge_height_ft", eh))
    t = sec.get("type", "gable")
    x0, x1, y0, y1 = _bbox(sec)
    lo, hi = (x0, x1) if haxis == "x" else (y0, y1)

    if t == "flat" or abs(rh - eh) < 1e-6:
        return [[lo, eh], [hi, eh]]

    if t == "shed":
        d = (sec.get("drainage") or ["S"])[0]
        slope_axis = "x" if d in ("E", "W") else "y"
        if haxis == slope_axis:
            low_at_lo = d in ("W", "S")    # W=x0 side, S=y0 side is downhill (low)
            return [[lo, eh if low_at_lo else rh], [hi, rh if low_at_lo else eh]]
        return [[lo, rh], [hi, rh]]        # slope goes away from viewer -> high edge

    ra = _ridge_axis(sec)
    rpx = [p[0] for p in sec["ridge"]]; rpy = [p[1] for p in sec["ridge"]]
    end_view = (ra != haxis)               # ridge perpendicular to screen -> we see the END

    if end_view:                           # triangle: eave -> ridge apex -> eave
        apex = rpx[0] if haxis == "x" else rpy[0]
        return [[lo, eh], [apex, rh], [hi, eh]]
    if t == "hip":                         # trapezoid: ridge inset, hips to corners
        r_lo = min(rpx) if haxis == "x" else min(rpy)
        r_hi = max(rpx) if haxis == "x" else max(rpy)
        return [[lo, eh], [r_lo, rh], [r_hi, rh], [hi, eh]]
    return [[lo, rh], [hi, rh]]            # gable side: ridge straight across


def elevation_profiles(roof: dict) -> dict:
    """Build the four-elevation silhouette block for the Side-View Agent."""
    secs = roof.get("roof_sections", [])
    views = {}
    for name, haxis, mirror in VIEWS:
        sections = []
        for s in secs:
            eh = float(s.get("eave_height_ft", 0.0))
            x0, x1, y0, y1 = _bbox(s)
            lo, hi = (x0, x1) if haxis == "x" else (y0, y1)
            sections.append({
                "name": s.get("name"),
                "type": s.get("type"),
                "eave_height_ft": round(eh, 2),
                "ridge_height_ft": round(float(s.get("ridge_height_ft", eh)), 2),
                "roof_silhouette": [[round(u, 2), round(z, 2)] for u, z in _section_profile(s, haxis)],
                "eave_line": [[round(lo, 2), round(eh, 2)], [round(hi, 2), round(eh, 2)]],
                "overhang_ft": s.get("eave_overhang_ft", 0.0),
            })
        views[name] = {
            "horizontal_axis": haxis,      # which plan coord is left-right in this view
            "mirror": mirror,              # flip u for a conventional outside view
            "sections": sections,
        }
    return {
        "note": "Draw each section's roof_silhouette as a polyline: u = horizontal plan "
                "coord (see horizontal_axis), z = height (ft). Walls run from z=0 up to "
                "eave_line; the roof sits on top. If mirror=true, flip u about the facade "
                "centre for an outside-looking-in view.",
        "units": "feet",
        "views": views,
    }
