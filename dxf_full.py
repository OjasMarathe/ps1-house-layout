"""Emit a single .dxf showing the whole design: plot + tree + house + rooms.

This is the Phase-2 counterpart of dxf_emitter.py. Once both the exterior
footprint and the interior layout are Z3-verified, we render them together from
the verified numbers (we never run the LLM's script). Layers/colors:

  PLOT   — red     plot boundary
  TREE   — green   protected tree + buffer ring
  HOUSE  — black   outer house wall (thick)
  ROOM_* — per kind, the interior partition walls
  DOOR   — blue    main door on the south wall
  LABELS — black   room names + areas, dimensions, north arrow
"""

from pathlib import Path

import ezdxf
from ezdxf.colors import RED, GREEN, BLUE, BLACK, CYAN, MAGENTA

from plot import Plot
from verifier_z3 import HouseGeometry
from interior_verifier_z3 import InteriorLayout

_KIND_COLOR = {
    "living":   CYAN,
    "kitchen":  MAGENTA,
    "corridor": 8,        # grey (ACI 8)
    "bathroom": BLUE,
    "bedroom":  GREEN,
}
_KIND_LAYER = {
    "living":   "ROOM_LIVING",
    "kitchen":  "ROOM_KITCHEN",
    "corridor": "CORRIDOR",
    "bathroom": "ROOM_BATH",
    "bedroom":  "ROOM_BEDROOM",
}


def emit_full_dxf(house: HouseGeometry, interior: InteriorLayout,
                  plot: Plot, path: Path) -> Path:
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # --- Plot boundary --------------------------------------------------------
    msp.add_lwpolyline(list(plot.boundary) + [plot.boundary[0]], close=True,
                       dxfattribs={"layer": "PLOT", "color": RED})

    # --- Tree + buffer --------------------------------------------------------
    tcx, tcy = plot.tree_center
    msp.add_circle((tcx, tcy), plot.tree_radius,
                   dxfattribs={"layer": "TREE", "color": GREEN})
    msp.add_circle((tcx, tcy), plot.tree_radius + 3.0,
                   dxfattribs={"layer": "TREE", "color": GREEN, "linetype": "DASHED"})

    # --- House outer wall (thick) --------------------------------------------
    msp.add_lwpolyline(list(house.corners) + [house.corners[0]], close=True,
                       dxfattribs={"layer": "HOUSE", "color": BLACK, "lineweight": 50})

    # --- Interior rooms -------------------------------------------------------
    for r in interior.rooms:
        ring = [(r.x_min, r.y_min), (r.x_max, r.y_min),
                (r.x_max, r.y_max), (r.x_min, r.y_max)]
        msp.add_lwpolyline(ring + [ring[0]], close=True,
                           dxfattribs={"layer": _KIND_LAYER[r.kind],
                                       "color": _KIND_COLOR[r.kind]})
        cx, cy = r.center
        msp.add_text(r.name, height=1.3,
                     dxfattribs={"layer": "LABELS", "color": BLACK}
                     ).set_placement((cx - len(r.name) * 0.45, cy + 0.8))
        msp.add_text(f"{r.area:.0f} sq ft", height=1.0,
                     dxfattribs={"layer": "LABELS", "color": BLACK}
                     ).set_placement((cx - 4, cy - 2.0))

    # --- Door (south wall) ----------------------------------------------------
    dx, dy = interior.door
    msp.add_line((dx - 1.5, dy), (dx + 1.5, dy),
                 dxfattribs={"layer": "DOOR", "color": BLUE, "lineweight": 70})
    msp.add_text("MAIN DOOR", height=1.0,
                 dxfattribs={"layer": "LABELS", "color": BLUE}
                 ).set_placement((dx - 6, dy - 3))

    # --- North arrow + title --------------------------------------------------
    px_min, py_min, px_max, py_max = plot.bbox
    nx, ny = px_min - 5, py_max - 2
    msp.add_line((nx, ny), (nx, ny + 4),
                 dxfattribs={"layer": "LABELS", "color": BLACK})
    msp.add_text("N", height=1.4,
                 dxfattribs={"layer": "LABELS", "color": BLACK}
                 ).set_placement((nx - 0.5, ny + 5))
    fx0, fy0, fx1, fy1 = interior.footprint
    msp.add_text(
        f"PS1 — Complete layout (Z3-verified)  |  house {fx1-fx0:.0f}x{fy1-fy0:.0f} ft, "
        f"{len(interior.rooms)} rooms, {interior.footprint_area:.0f} sq ft",
        height=1.8, dxfattribs={"layer": "LABELS", "color": BLACK}
    ).set_placement((px_min, py_min - 6))

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(path))
    return path


if __name__ == "__main__":
    from plot import PLOT
    from constraints import SBC
    from interior_milp import solve_layout

    fp = (5.0, 20.0, 68.0, 78.0)
    door = (40.0, 20.0)
    house = HouseGeometry(corners=((fp[0], fp[1]), (fp[2], fp[1]),
                                   (fp[2], fp[3]), (fp[0], fp[3])), door=door)
    interior = solve_layout(fp, door, SBC).layout
    out = emit_full_dxf(house, interior, PLOT, Path("output/full_layout_demo.dxf"))
    print(f"wrote {out}")
