"""Z3 self-verifier for the Roof Plan Agent.

The Roof Plan Agent verifies its own output before handing it to the DXF
Generator (same propose->prove pattern the Site Plan Generator uses with the Z3
Verifier tool). Numeric comparisons go through `verifier_z3._violated` so the
verdicts are deterministic proofs, not guesses.

Checks (maps to the acceptance checklist):
  roof_matches_footprint   outline == top-floor footprint (no overhang error / gap)   [item 1]
  stepped_roof_downward    lower level's ridge never rises above the upper eave        [item 2]
  roof_eave_setback        with an overhang, the eave stays within setbacks (fire)     [item 4]
  pitch_specified          every section has a real drainage slope                     [item 5]
  drainage_specified       every plane names a drainage direction                      [item 5]
"""
from dataclasses import dataclass

from verifier_z3 import _violated
from roof_agent import _bbox, _area
from plot import PLOT
from constraints import SBC

MIN_PITCH_RATIO = 0.02           # ~0.24:12 — at/below this a roof won't drain (flat = 0.25:12 passes)


@dataclass(frozen=True)
class RoofViolation:
    rule: str
    measured: float
    required: float
    message: str


def check_roof(roof: dict, levels, sbc=SBC, plot=PLOT, match_tol_ft=0.01) -> list:
    """Return a list of RoofViolation; empty list == a valid, well-formed roof."""
    v = []
    lv_by = {lv.get("level", i + 1): lv for i, lv in enumerate(levels)}
    sections = roof["roof_sections"]

    for s in sections:
        name = s["name"]
        oh = float(s.get("overhang_ft", 0.0))

        # --- item 1: roof outline matches the top-floor footprint -------------
        lv = lv_by.get(s["level"])
        if lv is not None:
            fp = [[float(x), float(y)] for x, y in lv["footprint"]]
            fa, ra = _area(fp), _area(s["outline"])
            if oh == 0:
                if abs(ra - fa) > max(match_tol_ft, 1e-3 * fa):
                    v.append(RoofViolation("roof_matches_footprint", round(ra, 2), round(fa, 2),
                        f"'{name}' roof area {ra:.0f} != footprint {fa:.0f} sq ft — overhang/gap."))
                fb, rb = _bbox(fp), _bbox(s["outline"])
                if max(abs(a - b) for a, b in zip(fb, rb)) > match_tol_ft:
                    v.append(RoofViolation("roof_matches_footprint", 0.0, 0.0,
                        f"'{name}' roof outline does not line up with the footprint boundary."))
            else:
                if _violated(ra, fa):                 # roof smaller than footprint -> gap
                    v.append(RoofViolation("roof_no_gap", round(ra, 2), round(fa, 2),
                        f"'{name}' roof {ra:.0f} < footprint {fa:.0f} sq ft — a gap is exposed."))

        # --- item 5: pitch + drainage are actually specified ------------------
        if _violated(s["pitch_ratio"], MIN_PITCH_RATIO):
            v.append(RoofViolation("pitch_specified", round(s["pitch_ratio"], 4), MIN_PITCH_RATIO,
                f"'{name}' has essentially no pitch; a roof needs a drainage slope."))
        if not s.get("drainage"):
            v.append(RoofViolation("drainage_specified", 0.0, 1.0,
                f"'{name}' has no drainage direction."))
        for pl in s.get("planes", []):
            if not pl.get("drains_to"):
                v.append(RoofViolation("drainage_specified", 0.0, 1.0,
                    f"Plane '{pl.get('id')}' in '{name}' has no drainage direction."))

        # --- item 4: with an overhang, the eave must stay within setbacks -----
        if oh > 0:
            x0, y0, x1, y1 = _bbox(s["outline"])
            px0, py0, px1, py1 = plot.bbox
            for rule, measured, req, side in [
                ("roof_eave_setback_west",  (x0 - oh) - px0, sbc.side_setback_ft,  "West"),
                ("roof_eave_setback_east",  px1 - (x1 + oh), sbc.side_setback_ft,  "East"),
                ("roof_eave_setback_south", (y0 - oh) - py0, sbc.front_setback_ft, "South"),
                ("roof_eave_setback_north", py1 - (y1 + oh), sbc.rear_setback_ft,  "North"),
            ]:
                if _violated(measured, req):
                    v.append(RoofViolation(rule, round(measured, 2), round(req, 2),
                        f"'{name}' {oh:.1f} ft eave breaks the {side} clearance "
                        f"({measured:.1f} ft < {req:.0f} ft) — fire/setback."))

        # --- skylights (sunroofs) must sit within the roof outline -----------
        ox0, oy0, ox1, oy1 = _bbox(s["outline"])
        for sk in s.get("skylights", []):
            sx0, sy0, sx1, sy1 = _bbox(sk["outline"])
            if (sx0 < ox0 - match_tol_ft or sy0 < oy0 - match_tol_ft
                    or sx1 > ox1 + match_tol_ft or sy1 > oy1 + match_tol_ft):
                v.append(RoofViolation("skylight_within_roof", 0.0, 0.0,
                    f"Skylight over '{sk.get('room')}' extends outside the '{name}' roof outline."))

    # --- item 2: multi-level steps must go DOWNWARD (no collision) ------------
    if len(sections) > 1:
        ordered = sorted(sections, key=lambda s: s["eave_height_ft"])
        for lo, hi in zip(ordered, ordered[1:]):
            if lo["eave_height_ft"] < hi["eave_height_ft"] and \
                    _violated(hi["eave_height_ft"], lo["ridge_height_ft"]):
                v.append(RoofViolation("stepped_roof_downward",
                    round(lo["ridge_height_ft"], 2), round(hi["eave_height_ft"], 2),
                    f"Lower section '{lo['name']}' ridge {lo['ridge_height_ft']:.1f} ft rises above "
                    f"upper section '{hi['name']}' eave {hi['eave_height_ft']:.1f} ft — steps must go down."))
    return v
