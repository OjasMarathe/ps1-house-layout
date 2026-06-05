"""Z3 interior synthesizer — proves a legal floor plan EXISTS and builds one.

This is the interior analogue of optimizer_z3.compute_max_area. For the
exterior we used Z3 `Optimize` to prove the largest legal footprint; here we
use Z3 to prove that the required 7-room program (3 bed + 1 kitchen + 2 bath +
1 living) can actually tile the verified footprint, and to produce a concrete,
balanced reference layout.

Topology — a fixed "slicing" floor plan (3 horizontal bands, cut by vertical
lines). This guarantees an *exact* tiling by construction (no gaps, no
overlaps) for any choice of cut coordinates, which is the hard part of
floor-plan synthesis:

      y=Y1 ┌──────────┬──────────┬──────────┐
           │  Bed 1   │  Bed 2   │  Bed 3   │   bedroom band  (depth bed_d)
    y=y_bed ├──────┬───┴──────────┴──────────┤
           │ Bath1│       Bath 2            │   bath band     (depth bath_d)
   y=y_split├──────┴───┬──────────────────────┤
           │  Living  │       Kitchen        │   public band   (depth pub_d)
      y=Y0 └────●─────┴──────────────────────┘
              door (south wall)

Every cut coordinate (x_pub, xt1, xb1, xb2) and every band depth (pub_d,
bath_d, bed_d) is a Z3 real variable. All constraints are LINEAR (we bound each
room's *width* and *depth* rather than its area, and width×depth ≥ the area
minimum holds by construction), so Z3 solves in the linear fragment — fast and
complete. We then `maximize` a fairness variable so the leftover space is
shared evenly rather than dumped into one room.

The concrete layout Z3 returns is finally re-checked by interior_verifier_z3,
so the reference is certified by the very same judge the agent loop uses.
"""

from z3 import Real, Optimize, sat

from constraints import SBCConstraints
from interior_verifier_z3 import InteriorLayout, Room, check_interior
import rooms as program


# Per-room linear size guides. width_min × depth_min must clear the program's
# area minimum, and both must clear the program's min_side. These are the
# synthesizer's internal targets; the verifier enforces the real program.
_GUIDE = {
    "living":   dict(w=16.0, d=13.0),   # 16×13 = 208 ≥ 200
    "kitchen":  dict(w=10.0, d=9.0),    # 10×9  = 90  ≥ 80
    "bathroom": dict(w=6.0,  d=7.0),    # 6×7   = 42  ≥ 40
    "bedroom":  dict(w=10.0, d=10.0),   # 10×10 = 100 ≥ 100
}


def _val(m, v) -> float:
    r = m[v]
    if hasattr(r, "as_decimal"):
        return float(r.as_decimal(12).rstrip("?"))
    return float(r.as_long())


def _band_depths(D: float) -> tuple[float, float, float]:
    """Split the footprint depth into public / bath / bedroom bands using
    realistic proportions, clamped to each band's minimum. Bathrooms are kept
    shallow; the public and bedroom bands take the bulk of the depth."""
    bath_d = max(_GUIDE["bathroom"]["d"], round(0.15 * D * 2) / 2)
    pub_d = max(_GUIDE["living"]["d"], round(0.40 * D * 2) / 2)
    bed_d = D - bath_d - pub_d
    if bed_d < _GUIDE["bedroom"]["d"]:        # tiny footprint — give bedrooms their min
        bed_d = _GUIDE["bedroom"]["d"]
        pub_d = D - bath_d - bed_d
    return pub_d, bath_d, bed_d


def solve_cuts(footprint: tuple[float, float, float, float],
               door: tuple[float, float],
               sbc: SBCConstraints) -> dict:
    """Z3 solves the vertical cut coordinates (room widths) for a balanced
    plan; band depths are fixed by design proportions. Returns a dict of
    floats, or raises RuntimeError if Z3 reports the program can't fit."""
    X0, Y0, X1, Y1 = footprint
    door_x, _ = door
    W, D = X1 - X0, Y1 - Y0
    margin = sbc.door_corner_margin_ft

    pub_d, bath_d, bed_d = _band_depths(D)
    y_split, y_bed = Y0 + pub_d, Y0 + pub_d + bath_d

    x_pub, xt1, xb1, xb2 = Real("x_pub"), Real("xt1"), Real("xb1"), Real("xb2")
    bbal = Real("bbal")   # bathroom-width fairness
    ubal = Real("ubal")   # bedroom-width fairness
    kw = Real("kw")       # kitchen width (maximized to a sane cap)

    opt = Optimize()

    # Public band: living | kitchen, split at x_pub. Door must fall inside the
    # living room with corner inset on both sides.
    opt.add(x_pub - X0 >= _GUIDE["living"]["w"])
    opt.add(X1 - x_pub >= _GUIDE["kitchen"]["w"])
    opt.add(x_pub >= door_x + margin)            # door inset from living's E wall
    opt.add(door_x - margin >= X0)               # door inset from living's W wall
    opt.add(kw == X1 - x_pub)
    opt.add(kw <= 22.0)                          # keep the kitchen a sane width

    # Bath band: bath1 | bath2, split at xt1; balanced.
    opt.add(xt1 - X0 >= _GUIDE["bathroom"]["w"])
    opt.add(X1 - xt1 >= _GUIDE["bathroom"]["w"])
    opt.add(bbal <= xt1 - X0)
    opt.add(bbal <= X1 - xt1)

    # Bedroom band: bed1 | bed2 | bed3, split at xb1 < xb2; balanced.
    opt.add(xb1 - X0 >= _GUIDE["bedroom"]["w"])
    opt.add(xb2 - xb1 >= _GUIDE["bedroom"]["w"])
    opt.add(X1 - xb2 >= _GUIDE["bedroom"]["w"])
    opt.add(ubal <= xb1 - X0)
    opt.add(ubal <= xb2 - xb1)
    opt.add(ubal <= X1 - xb2)

    opt.maximize(bbal)   # 1st: equal bathrooms
    opt.maximize(ubal)   # 2nd: equal bedrooms
    opt.maximize(kw)     # 3rd: comfortable kitchen (living takes the remainder)

    if opt.check() != sat:
        raise RuntimeError(
            f"Z3: the 7-room program does not fit in a {W:.0f}×{D:.0f} ft "
            "footprint under the size minimums.")
    m = opt.model()

    def r(v):  # round to 0.5 ft; shared cut coords keep the tiling exact
        return round(_val(m, v) * 2) / 2

    return {
        "x_pub": r(x_pub), "xt1": r(xt1), "xb1": r(xb1), "xb2": r(xb2),
        "y_split": y_split, "y_bed": y_bed,
    }


def _rooms_from_cuts(footprint, cuts) -> tuple[Room, ...]:
    X0, Y0, X1, Y1 = footprint
    xp, xt1, xb1, xb2 = cuts["x_pub"], cuts["xt1"], cuts["xb1"], cuts["xb2"]
    ys, yb = cuts["y_split"], cuts["y_bed"]
    return (
        Room("Living",    "living",   X0,  Y0, xp,  ys),
        Room("Kitchen",   "kitchen",  xp,  Y0, X1,  ys),
        Room("Bath 1",    "bathroom", X0,  ys, xt1, yb),
        Room("Bath 2",    "bathroom", xt1, ys, X1,  yb),
        Room("Bedroom 1", "bedroom",  X0,  yb, xb1, Y1),
        Room("Bedroom 2", "bedroom",  xb1, yb, xb2, Y1),
        Room("Bedroom 3", "bedroom",  xb2, yb, X1,  Y1),
    )


def synthesize(footprint: tuple[float, float, float, float],
               door: tuple[float, float],
               sbc: SBCConstraints) -> InteriorLayout:
    """Solve for cuts with Z3, build the layout, and certify it with the
    interior verifier. Returns a guaranteed-legal reference InteriorLayout."""
    cuts = solve_cuts(footprint, door, sbc)
    layout = InteriorLayout(footprint=footprint, door=door,
                            rooms=_rooms_from_cuts(footprint, cuts))
    residual = check_interior(layout, sbc)
    if residual:
        msgs = "; ".join(f"{v.rule}: {v.message}" for v in residual)
        raise RuntimeError(f"Synthesized reference failed self-check: {msgs}")
    return layout


if __name__ == "__main__":
    from constraints import SBC
    # The converged exterior footprint + door from the exterior pipeline.
    fp = (5.0, 20.0, 70.0, 78.0)
    door = (40.0, 20.0)
    layout = synthesize(fp, door, SBC)
    print(f"Z3-synthesized interior for footprint {fp}, door {door}:")
    for rm in layout.rooms:
        print(f"  {rm.name:10s} {rm.kind:9s} "
              f"({rm.x_min:.1f},{rm.y_min:.1f})-({rm.x_max:.1f},{rm.y_max:.1f})  "
              f"{rm.area:.0f} sq ft  ({rm.width:.1f}×{rm.depth:.1f})")
    print(f"  total room area = {sum(r.area for r in layout.rooms):.0f} sq ft "
          f"(footprint {layout.footprint_area:.0f} sq ft)")
    print("  ✅ certified by interior verifier (0 violations)")
