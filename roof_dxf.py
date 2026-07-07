"""Roof Plan -> DXF (the distinct Cluster-4 artifact, separate from floor/elevations).

Layers: ROOF_OUTLINE, ROOF_RIDGE, ROOF_HIP, ROOF_SLOPE (drainage arrows), ROOF_TEXT.
This is what the DXF Generator consumes; it is emitted separately from the floor
plan and side views so it never visually contradicts them.
"""
import os

import ezdxf
from ezdxf.colors import RED, CYAN, BLUE, YELLOW, WHITE, GREEN

from roof_agent import _bbox

_DIR = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}


def _centroid(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def write_roof_dxf(roof: dict, path="output/roof_plan.dxf") -> str:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()
    for layer, color in [("ROOF_OUTLINE", WHITE), ("ROOF_RIDGE", RED),
                         ("ROOF_HIP", CYAN), ("ROOF_SLOPE", BLUE), ("ROOF_TEXT", YELLOW),
                         ("ROOF_SKYLIGHT", GREEN)]:
        doc.layers.add(layer, color=color)

    for s in roof["roof_sections"]:
        out = s["outline"]
        x0, y0, x1, y1 = _bbox(out)
        arrow = 0.15 * min(x1 - x0, y1 - y0)

        # outline (matches the footprint exactly)
        msp.add_lwpolyline([tuple(p) for p in out] + [tuple(out[0])],
                           close=True, dxfattribs={"layer": "ROOF_OUTLINE"})
        # ridge
        if s.get("ridge"):
            msp.add_lwpolyline([tuple(p) for p in s["ridge"]], dxfattribs={"layer": "ROOF_RIDGE"})
        # hip lines
        for h in s.get("hips", []):
            msp.add_lwpolyline([tuple(p) for p in h], dxfattribs={"layer": "ROOF_HIP"})
        # drainage arrow + slope label per plane
        for pl in s.get("planes", []):
            cx, cy = _centroid(pl["polygon"])
            dx, dy = _DIR[pl["drains_to"]]
            tx, ty = cx + dx * arrow, cy + dy * arrow
            msp.add_line((cx, cy), (tx, ty), dxfattribs={"layer": "ROOF_SLOPE"})
            # small arrowhead
            hx, hy = -dy, dx           # perpendicular
            a = arrow * 0.3
            msp.add_line((tx, ty), (tx - dx * a + hx * a * 0.6, ty - dy * a + hy * a * 0.6),
                         dxfattribs={"layer": "ROOF_SLOPE"})
            msp.add_line((tx, ty), (tx - dx * a - hx * a * 0.6, ty - dy * a - hy * a * 0.6),
                         dxfattribs={"layer": "ROOF_SLOPE"})
            msp.add_text(f"{pl['slope_pct']:.0f}%", height=arrow * 0.5,
                         dxfattribs={"layer": "ROOF_TEXT"}).set_placement((cx + 0.3, cy + 0.3))
        # skylights (sunroofs)
        for sk in s.get("skylights", []):
            so = sk["outline"]
            msp.add_lwpolyline([tuple(p) for p in so] + [tuple(so[0])], close=True,
                               dxfattribs={"layer": "ROOF_SKYLIGHT"})
            scx, scy = sk["center"]
            msp.add_text(f"skylight: {sk['room']}", height=1.0,
                         dxfattribs={"layer": "ROOF_SKYLIGHT"}).set_placement((scx - 1.8, scy - 0.4))

        # section label
        msp.add_text(f"{s['name']} · {s['type']} · {s['pitch']} · ridge {s['ridge_height_ft']}ft",
                     height=1.4, dxfattribs={"layer": "ROOF_TEXT"}).set_placement((x0 + 0.5, y1 - 2.0))

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    doc.saveas(path)
    return path
