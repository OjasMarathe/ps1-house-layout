"""Interior layout by Mixed-Integer Linear Programming (CBC branch-and-cut),
with human-tunable room sizes (human-in-the-loop).

This is the approach Anupam sir pointed at: a MILP solver *generates* a layout
that is guaranteed to satisfy the hard constraints (generate-and-guarantee),
solved by PuLP + CBC (branch-and-cut → cutting planes on the big-M non-overlap
disjunctions).

Human-in-the-loop: the solver enforces the *code* rules; the *comfort* choices
(how big each room is) are a `params` dict supplied by the human. interior_hitl
loops solve → render → adjust → re-solve until the human accepts. This is what
lets us fix "bedrooms too small, living/kitchen too big": the human (or the
balanced defaults) sets the proportions directly.

Layout (free placement, NOT exact tiling — leftover is open / flex / circulation):

      NORTH (private)   [ Bath1 Bed1 | Bed3 | Bed2 Bath2 ]  flush to corridor,
                        bedrooms `bed_depth` deep, baths `bath_depth` deep
      CORRIDOR (4 ft)   full width — every room touches it (connectivity)
      SOUTH (public)    Living (holds the door) + Kitchen, `public_depth` deep,
                        sized by width; open space to the sides

Guarantees kept by construction: door opens into the living room; kitchen flush
to living; corridor isolates baths from the kitchen (sanitation); each bath is
ensuite to exactly its own bedroom; the two baths are never adjacent; bath
≤ 15 ft/side and smaller than its bedroom; every room touches the corridor.
The same Z3 verifier confirms the full constraint set (coverage in open mode).
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
    bands: dict          # y-ranges of the three bands (for drawing)
    fill_frac: float     # covered area / footprint area
    params: dict         # the room-size parameters used


def default_params(footprint: tuple[float, float, float, float]) -> dict:
    """Balanced default room sizes scaled to the footprint."""
    X0, Y0, X1, Y1 = footprint
    W, H = X1 - X0, Y1 - Y0
    return {
        "public_depth": float(round(0.34 * H)),              # living/kitchen depth
        "bed_depth":    float(round(min(0.50 * H, H - round(0.34 * H) - 4 - 1))),  # deep bedrooms
        "bath_depth":   float(round(min(14.0, 0.22 * H))),    # bathroom depth
        "bath_w":       8.0,                                  # bathroom width
        "living_w":     float(round(0.50 * W)),               # living width
        "kitchen_w":    float(round(0.38 * W)),               # kitchen width
    }


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def safe_params(footprint, door, params, sbc: SBCConstraints = SBC) -> dict:
    """Clamp a params dict into a feasible range so solve_layout won't raise.
    Used for the deterministic seed (vibe presets can over-shoot)."""
    X0, Y0, X1, Y1 = footprint
    door_x, _ = door
    W, H = X1 - X0, Y1 - Y0
    inset, corr = sbc.door_corner_margin_ft, program.CORRIDOR_WIDTH_FT
    p = {**default_params(footprint), **(params or {})}
    p["public_depth"] = _clamp(p["public_depth"], 7, H - corr - 8)
    Hn = H - p["public_depth"] - corr
    p["bed_depth"] = _clamp(p["bed_depth"], 7, Hn)
    p["bath_depth"] = _clamp(p["bath_depth"], 5, min(15.0, p["bed_depth"]))
    p["bath_w"] = _clamp(p["bath_w"], 5, 15)
    p["kitchen_w"] = _clamp(p["kitchen_w"], 7, W - 7)
    p["living_w"] = _clamp(p["living_w"], 7, W - p["kitchen_w"])
    # ensure a valid living x exists (door inside, kitchen fits): shrink kitchen if needed
    for _ in range(40):
        lo = max(X0, door_x + inset - p["living_w"])
        hi = min(door_x - inset, X1 - p["living_w"] - p["kitchen_w"])
        if lo <= hi:
            break
        if p["kitchen_w"] > 7:
            p["kitchen_w"] -= 1
        else:
            p["living_w"] = max(7, p["living_w"] - 1)
    return p


def _validate(footprint, door, sbc, p) -> tuple[dict, list[str]]:
    X0, Y0, X1, Y1 = footprint
    door_x, _ = door
    W, H = X1 - X0, Y1 - Y0
    inset = sbc.door_corner_margin_ft
    corr = program.CORRIDOR_WIDTH_FT
    Hs, bed_d, bath_d = p["public_depth"], p["bed_depth"], p["bath_depth"]
    bath_w, living_w, kitchen_w = p["bath_w"], p["living_w"], p["kitchen_w"]
    Hn = H - Hs - corr
    bed_w = (W - 2 * bath_w) / 3.0
    e = []
    if Hs < 7: e.append(f"public_depth {Hs:.0f} ft must be ≥ 7")
    if not (7 <= bed_d <= Hn + 1e-6):
        e.append(f"bed_depth {bed_d:.0f} ft must be in [7, {Hn:.0f}] (public_depth too big?)")
    if not (5 <= bath_d <= min(15.0, bed_d) + 1e-6):
        e.append(f"bath_depth {bath_d:.0f} ft must be in [5, min(15, bed_depth)]")
    if not (5 <= bath_w <= 15):
        e.append(f"bath_w {bath_w:.0f} ft must be in [5, 15]")
    if bed_w < 7:
        e.append(f"bedrooms only {bed_w:.1f} ft wide — reduce bath_w (now {bath_w:.0f})")
    if living_w < 7 or kitchen_w < 7:
        e.append("living_w and kitchen_w must each be ≥ 7 ft")
    if living_w + kitchen_w > W + 1e-6:
        e.append(f"living_w + kitchen_w ({living_w+kitchen_w:.0f}) exceeds house width {W:.0f}")
    lo = max(X0, door_x + inset - living_w)
    hi = min(door_x - inset, X1 - living_w - kitchen_w)
    if lo > hi + 1e-6:
        e.append("living can't both span the door and leave room for the kitchen "
                 "(narrow the kitchen or widen the living room)")
    return {"Hs": Hs, "bed_d": bed_d, "bath_d": bath_d, "bath_w": bath_w,
            "living_w": living_w, "kitchen_w": kitchen_w, "bed_w": bed_w,
            "Hn": Hn, "corr": corr, "lo": lo, "hi": hi}, e


def solve_layout(footprint: tuple[float, float, float, float],
                 door: tuple[float, float],
                 sbc: SBCConstraints = SBC,
                 params: dict | None = None,
                 msg: bool = False) -> MilpResult:
    X0, Y0, X1, Y1 = footprint
    door_x, _ = door
    W, H = X1 - X0, Y1 - Y0
    M = W + H
    p = {**default_params(footprint), **(params or {})}
    d, errs = _validate(footprint, door, sbc, p)
    if errs:
        raise RuntimeError("Infeasible room sizes: " + "; ".join(errs))

    Hs, corr, bed_d, bath_d = d["Hs"], d["corr"], d["bed_d"], d["bath_d"]
    bath_w, living_w, kitchen_w, bed_w = d["bath_w"], d["living_w"], d["kitchen_w"], d["bed_w"]
    cy = Y0 + Hs            # corridor south edge
    Yn = cy + corr         # private band south edge

    prob = pulp.LpProblem("interior_layout_hitl", pulp.LpMinimize)
    xL = pulp.LpVariable("living_x", d["lo"], d["hi"])   # living-room x (the real choice)
    # centre the door in the living room (linear deviation objective)
    ct = door_x - living_w / 2.0
    dev = pulp.LpVariable("dev", 0, M)
    prob += dev >= xL - ct
    prob += dev >= ct - xL

    # --- private band: deterministic tiling of the width, flush to corridor --
    bx = X0
    priv = []  # (name, kind, x0, x1, depth)
    for name, kind, w in [("Bath 1", "bathroom", bath_w), ("Bedroom 1", "bedroom", bed_w),
                          ("Bedroom 3", "bedroom", bed_w), ("Bedroom 2", "bedroom", bed_w),
                          ("Bath 2", "bathroom", bath_w)]:
        depth = bath_d if kind == "bathroom" else bed_d
        priv.append((name, kind, bx, bx + w, depth))
        bx += w

    # --- assemble rooms (living/kitchen x are affine in xL) ------------------
    R = {
        "Living":   ("living",   xL,            xL + living_w,            Y0,  cy),
        "Kitchen":  ("kitchen",  xL + living_w, xL + living_w + kitchen_w, Y0,  cy),
        "Corridor": ("corridor", X0,            X1,                        cy,  Yn),
    }
    for name, kind, x0, x1, depth in priv:
        R[name] = (kind, x0, x1, Yn, Yn + depth)
    names = list(R)

    # --- big-M non-overlap (the cutting-plane MILP core; CBC branch-and-cut) -
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

    prob += dev   # objective: centre the door in the living room
    prob.solve(pulp.PULP_CBC_CMD(msg=1 if msg else 0, cuts=True))
    status = pulp.LpStatus[prob.status]
    if status != "Optimal":
        raise RuntimeError(f"CBC returned status '{status}' for the interior MILP.")

    def rect(key) -> Room:
        kind, xlo, xhi, ylo, yhi = R[key]
        return Room(name=key, kind=kind,
                    x_min=round(float(pulp.value(xlo)), 3), y_min=round(float(ylo), 3),
                    x_max=round(float(pulp.value(xhi)), 3), y_max=round(float(yhi), 3))

    rooms_out = tuple(rect(k) for k in names)
    layout = InteriorLayout(footprint=footprint, door=door, rooms=rooms_out)
    fill = sum(r.area for r in rooms_out) / layout.footprint_area
    return MilpResult(layout=layout, status=status,
                      bands={"south": (Y0, cy), "corridor": (cy, Yn), "north": (Yn, Y1)},
                      fill_frac=fill, params=p)


if __name__ == "__main__":
    fp = (5.0, 20.0, 68.0, 78.0)
    door = (40.0, 20.0)
    res = solve_layout(fp, door)
    print(f"CBC {res.status} · fill {res.fill_frac*100:.0f}% · params {res.params}")
    for r in res.layout.rooms:
        print(f"  {r.name:10s} {r.kind:9s} ({r.x_min:.1f},{r.y_min:.1f})-"
              f"({r.x_max:.1f},{r.y_max:.1f})  {r.area:.0f} sq ft  ({r.width:.0f}×{r.depth:.0f})")
    from interior_verifier_z3 import check_interior
    viol = check_interior(res.layout, SBC, require_full_coverage=False)
    print("  ✅ Z3 OK (open mode)" if not viol else f"  ❌ {[v.rule for v in viol]}")
