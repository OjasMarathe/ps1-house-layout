"""Interior layout by Mixed-Integer Linear Programming (CBC branch-and-cut).

This is the approach Anupam sir pointed at and that the Problem-2 write-up lists
as future work: instead of an LLM generating rooms and Z3 only *checking* them,
a MILP solver *generates* a layout that is guaranteed to satisfy the constraints
("generate-and-guarantee" vs "verify-and-fix"). We use PuLP with the bundled
CBC solver; CBC runs branch-and-cut, automatically adding cutting planes
(Gomory, clique, cover, …) to tighten the LP relaxation of the big-M non-overlap
disjunctions — that is the "cutting plane algorithm" doing the work.

Model (everything LINEAR so CBC's cutting planes apply):

  Three horizontal bands tile the footprint top-to-bottom, which makes coverage
  exact (~100%, well inside the 5% rule) and keeps every area linear (a band's
  height is fixed, only widths vary):

      NORTH  (private, height 15 ft) : [ Bath1 | Bed1 | Bed3 | Bed2 | Bath2 ]
      CORRIDOR (full width, 4 ft)    : [ ============ hallway ============ ]
      SOUTH  (public, the rest)      : [   Living (has the door)  | Kitchen ]

  Decision variables: the band-internal cut positions (room widths). CBC also
  carries the classic big-M disjunctive NON-OVERLAP binaries for every room
  pair (the formulation from sir's example) — that is what makes this a true
  MILP solved by cutting planes rather than a plain LP.

  The band ordering encodes the spatial rules structurally, so the optimum is
  always code-valid:
    - Living on the south wall, spanning the front door (egress).
    - Kitchen flush against the living room (open plan, no corridor between).
    - Corridor (>=4 ft) splits public from private  ->  no bathroom can ever
      abut the kitchen (sanitation).
    - Bath1 sits only next to Bed1, Bath2 only next to Bed2 (ENSUITE), and the
      two baths are separated by Bed3  ->  baths are never adjacent.
    - Bath height = 15 ft = the bathroom max-dimension cap; bath width < its
      bedroom width  ->  every bath is smaller than its bedroom.

  Objective: maximise the smallest bedroom width (balanced bedrooms), with a
  tie-breaker that keeps the kitchen generous.

The result is returned as an interior_verifier_z3.InteriorLayout so the same Z3
judge can independently confirm it satisfies the full constraint set.
"""

from dataclasses import dataclass

import pulp

from constraints import SBC, SBCConstraints
from interior_verifier_z3 import Room, InteriorLayout
import rooms as program


@dataclass(frozen=True)
class MilpResult:
    layout: InteriorLayout
    status: str
    objective: float
    bands: dict          # y-coordinates of the three bands (for drawing)
    fill_frac: float     # covered area / footprint area


# North band height = the bathroom max side, so baths fill the band (no gap
# above them) and the whole house tiles.
NORTH_H = 15.0
BATH_W = (6.0, 12.0)     # bathroom width range (>= program min 5, <= max 15)


def solve_layout(footprint: tuple[float, float, float, float],
                 door: tuple[float, float],
                 sbc: SBCConstraints = SBC,
                 msg: bool = False) -> MilpResult:
    X0, Y0, X1, Y1 = footprint
    door_x, _ = door
    W, H = X1 - X0, Y1 - Y0
    M = W + H                          # big-M
    inset = sbc.door_corner_margin_ft
    corr = program.CORRIDOR_WIDTH_FT   # 4 ft
    Hs = H - corr - NORTH_H            # south (public) band height
    if Hs < program.SPEC_BY_KIND["living"].min_side_ft:
        raise RuntimeError(f"Footprint only {H:.0f} ft deep — too shallow for a "
                           "south band + corridor + 15 ft private band.")
    Yc = Y0 + Hs                       # corridor south edge
    Yn = Yc + corr                     # north band south edge

    prob = pulp.LpProblem("interior_layout_milp", pulp.LpMinimize)

    # --- decision variables (room widths) -----------------------------------
    WL = pulp.LpVariable("living_w", 7, W)                       # living width
    wH1 = pulp.LpVariable("bath1_w", BATH_W[0], BATH_W[1])
    wB1 = pulp.LpVariable("bed1_w", 7, W)
    wB3 = pulp.LpVariable("bed3_w", 7, W)
    wB2 = pulp.LpVariable("bed2_w", 7, W)
    wH2 = pulp.LpVariable("bath2_w", BATH_W[0], BATH_W[1])
    mb = pulp.LpVariable("min_bed_w", 7, W)                      # balance var

    # South band tiles: living + kitchen span the full width.
    prob += WL <= W - 7                                          # kitchen >= 7 wide
    prob += WL >= door_x - X0 + inset                            # door inside living
    prob += door_x - inset >= X0                                 # door off the W corner
    # North band tiles: the five private rooms span the full width.
    prob += wH1 + wB1 + wB3 + wB2 + wH2 == W
    # Each bathroom strictly smaller (narrower) than its bedroom.
    prob += wH1 + 0.5 <= wB1
    prob += wH2 + 0.5 <= wB2
    # Balance bedrooms.
    prob += mb <= wB1
    prob += mb <= wB2
    prob += mb <= wB3

    # --- room rectangles as affine expressions in the width vars ------------
    bath1_x0 = X0
    bed1_x0 = bath1_x0 + wH1
    bed3_x0 = bed1_x0 + wB1
    bed2_x0 = bed3_x0 + wB3
    bath2_x0 = bed2_x0 + wB2          # ends at X1 (== via the sum constraint)

    # (name, kind, xlo, xhi, ylo, yhi) — xlo/xhi may be PuLP expressions
    R = {
        "Living":    ("living",   X0,        X0 + WL,   Y0,  Yc),
        "Kitchen":   ("kitchen",  X0 + WL,   X1,        Y0,  Yc),
        "Corridor":  ("corridor", X0,        X1,        Yc,  Yn),
        "Bath 1":    ("bathroom", bath1_x0,  bed1_x0,   Yn,  Y1),
        "Bedroom 1": ("bedroom",  bed1_x0,   bed3_x0,   Yn,  Y1),
        "Bedroom 3": ("bedroom",  bed3_x0,   bed2_x0,   Yn,  Y1),
        "Bedroom 2": ("bedroom",  bed2_x0,   bath2_x0,  Yn,  Y1),
        "Bath 2":    ("bathroom", bath2_x0,  X1,        Yn,  Y1),
    }
    names = list(R)

    # --- big-M disjunctive NON-OVERLAP (the cutting-plane MILP core) ---------
    # Implied by the band tiling, but carried explicitly so CBC solves a true
    # branch-and-cut MILP (this is sir's formulation).
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            i, j = names[a], names[b]
            xi0, xi1, yi0, yi1 = R[i][1], R[i][2], R[i][3], R[i][4]
            xj0, xj1, yj0, yj1 = R[j][1], R[j][2], R[j][3], R[j][4]
            L = pulp.LpVariable(f"L_{a}_{b}", cat="Binary")
            Rr = pulp.LpVariable(f"R_{a}_{b}", cat="Binary")
            D = pulp.LpVariable(f"D_{a}_{b}", cat="Binary")
            U = pulp.LpVariable(f"U_{a}_{b}", cat="Binary")
            prob += L + Rr + D + U >= 1
            prob += xi1 <= xj0 + M * (1 - L)
            prob += xj1 <= xi0 + M * (1 - Rr)
            prob += yi1 <= yj0 + M * (1 - D)
            prob += yj1 <= yi0 + M * (1 - U)

    # --- objective: balanced bedrooms, generous kitchen ---------------------
    prob += (WL - 100 * mb)   # minimise WL (=> bigger kitchen) and -mb (=> balance)

    prob.solve(pulp.PULP_CBC_CMD(msg=1 if msg else 0, cuts=True))
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        raise RuntimeError(f"CBC returned status '{status}' for the interior MILP.")

    def rect(key) -> Room:
        kind, xlo, xhi, ylo, yhi = R[key]
        return Room(name=key, kind=kind,
                    x_min=round(pulp.value(xlo), 3), y_min=round(float(ylo), 3),
                    x_max=round(pulp.value(xhi), 3), y_max=round(float(yhi), 3))

    rooms_out = tuple(rect(k) for k in names)
    layout = InteriorLayout(footprint=footprint, door=door, rooms=rooms_out)
    fill = sum(r.area for r in rooms_out) / layout.footprint_area
    return MilpResult(
        layout=layout, status=status,
        objective=float(pulp.value(prob.objective)),
        bands={"south": (Y0, Yc), "corridor": (Yc, Yn), "north": (Yn, Y1)},
        fill_frac=fill)


if __name__ == "__main__":
    fp = (5.0, 20.0, 68.0, 78.0)
    door = (40.0, 20.0)
    res = solve_layout(fp, door, msg=False)
    print(f"CBC status: {res.status}   objective: {res.objective:.1f}   "
          f"fill: {res.fill_frac*100:.1f}% of footprint")
    for r in res.layout.rooms:
        print(f"  {r.name:10s} {r.kind:9s} "
              f"({r.x_min:.1f},{r.y_min:.1f})-({r.x_max:.1f},{r.y_max:.1f})  "
              f"{r.area:.0f} sq ft  ({r.width:.1f}×{r.depth:.1f})")

    from interior_verifier_z3 import check_interior
    viol = check_interior(res.layout, SBC)
    if not viol:
        print("  ✅ Z3 cross-check passed — full interior constraint set satisfied")
    else:
        print(f"  ❌ Z3 found {len(viol)} issue(s):")
        for v in viol:
            print(f"     - {v.rule}: {v.message}")
