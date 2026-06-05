"""Emit a clean .dxf from Z3-verified geometry.

Once Z3 reports zero violations, we don't need to run Gemini's `ezdxf`
script — the geometry is already known and verified. This module turns
(plot, house) into a deterministic .dxf so every successful loop run
produces a viewable artifact regardless of whether A1's Python actually
executed.

Layers match the sketch convention used by Anupam:
  PLOT   — red,   plot boundary polygon (and a north arrow)
  TREE   — green, protected tree circle + buffer ring
  HOUSE  — green, house outline (the SBC-compliant rectangle)
  DOOR   — blue,  short segment marking the main door on the south wall
  LABELS — black, dimension labels
"""

from pathlib import Path

import ezdxf
from ezdxf.colors import RED, GREEN, BLUE, BLACK, MAGENTA

from plot import Plot
from verifier_z3 import HouseGeometry


def emit_dxf(house: HouseGeometry, plot: Plot, path: Path,
             max_legal_area: float | None = None) -> Path:
    """Write a DXF showing plot + tree + house + door. Returns the path."""
    doc = ezdxf.new("R2010")
    msp = doc.modelspace()

    # --- Plot boundary --------------------------------------------------------
    msp.add_lwpolyline(
        list(plot.boundary) + [plot.boundary[0]],  # close
        close=True,
        dxfattribs={"layer": "PLOT", "color": RED},
    )

    # --- Tree (trunk + buffer ring) ------------------------------------------
    tcx, tcy = plot.tree_center
    msp.add_circle(
        (tcx, tcy), plot.tree_radius,
        dxfattribs={"layer": "TREE", "color": GREEN},
    )
    msp.add_circle(
        (tcx, tcy), plot.tree_radius + 3.0,  # SBC buffer
        dxfattribs={"layer": "TREE", "color": GREEN, "linetype": "DASHED"},
    )
    msp.add_text(
        "TREE (protected)",
        height=0.8,
        dxfattribs={"layer": "LABELS", "color": GREEN},
    ).set_placement((tcx + plot.tree_radius + 0.5, tcy))

    # --- House outline --------------------------------------------------------
    msp.add_lwpolyline(
        list(house.corners) + [house.corners[0]],
        close=True,
        dxfattribs={"layer": "HOUSE", "color": GREEN},
    )

    # --- Door (short blue segment on south wall) ------------------------------
    dx, dy = house.door
    msp.add_line(
        (dx - 1.5, dy), (dx + 1.5, dy),
        dxfattribs={"layer": "DOOR", "color": BLUE, "lineweight": 50},
    )
    msp.add_text(
        "MAIN DOOR + PARKING",
        height=0.8,
        dxfattribs={"layer": "LABELS", "color": BLUE},
    ).set_placement((dx - 8, dy - 2))

    # --- Annotations ----------------------------------------------------------
    xs = [c[0] for c in house.corners]; ys = [c[1] for c in house.corners]
    x_min, x_max = min(xs), max(xs); y_min, y_max = min(ys), max(ys)
    w, d = x_max - x_min, y_max - y_min
    area = w * d
    label = f"HOUSE: {w:.0f} x {d:.0f} ft = {area:.0f} sq ft"
    if max_legal_area:
        label += f"  ({area/max_legal_area*100:.1f}% of Z3 max {max_legal_area:.0f})"
    msp.add_text(
        label, height=1.2,
        dxfattribs={"layer": "LABELS", "color": BLACK},
    ).set_placement(((x_min + x_max) / 2 - 18, (y_min + y_max) / 2))

    # North arrow + compass marker (top-left of plot)
    px_min, py_min, px_max, py_max = plot.bbox
    nx, ny = px_min - 5, py_max - 2
    msp.add_line((nx, ny), (nx, ny + 4),
                 dxfattribs={"layer": "LABELS", "color": BLACK})
    msp.add_text("N", height=1.2,
                 dxfattribs={"layer": "LABELS", "color": BLACK}
                 ).set_placement((nx - 0.5, ny + 5))

    # Title block
    msp.add_text(
        "PS1 — House Layout (Z3-verified)",
        height=1.8,
        dxfattribs={"layer": "LABELS", "color": BLACK},
    ).set_placement((px_min, py_min - 5))

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.saveas(str(path))
    return path


if __name__ == "__main__":
    # Standalone demo: emit a .dxf using the Z3-optimal house
    from plot import PLOT
    from constraints import SBC
    from optimizer_z3 import compute_max_area

    max_area, corners = compute_max_area(PLOT, SBC)
    house = HouseGeometry(
        corners=(
            (corners["x_min"], corners["y_min"]),
            (corners["x_max"], corners["y_min"]),
            (corners["x_max"], corners["y_max"]),
            (corners["x_min"], corners["y_max"]),
        ),
        door=((corners["x_min"] + corners["x_max"]) / 2, corners["y_min"]),
    )
    out = emit_dxf(house, PLOT, Path("output/z3_optimal_demo.dxf"),
                   max_legal_area=max_area)
    print(f"wrote {out}  ({max_area:.0f} sq ft Z3-optimal house)")
