"""Z3 Verifier — the deterministic constraint-checking tool.

This is the single, stable entry point the product calls. It is a *direct tool
call*: generators (Site Plan Agent, etc.) import `verify_site` / `optimize_area`
and call them straight, with no Agent-Manager routing in between. It is also a
standalone CLI for local debugging:

    python verifier_tool.py cities
    python verifier_tool.py optimize  --city seattle
    python verifier_tool.py verify    --city seattle [--layout house.json] [--json]
    python verifier_tool.py interior  --city seattle  --layout interior.json [--json]

Guarantees (see DECISION_constraints.md and the acceptance checklist):
  * provable pass/fail per constraint (Z3), never a probabilistic guess;
  * an "optimize" mode that computes the provable maximum buildable area;
  * a configurable floating-point tolerance (loaded per city) so near-exact
    matches do not produce false failures;
  * city-agnostic, config-driven constraints (JSON under citycodes/);
  * reports solve time so the < 5 s budget is verifiable.
"""
import argparse
import json
import sys
from time import perf_counter

import verifier_z3
from verifier_z3 import HouseGeometry, check
from optimizer_z3 import compute_max_area
from interior_verifier_z3 import Room, InteriorLayout, check_interior
from plot import PLOT
from constraints import SBC
import rooms as program
from codeloader import load_city, available_cities, sbc_from_dict

# Canonical exterior rule set, so a clean run reports every constraint as PASS
# (not just the failures). Matches the rule names emitted by verifier_z3.check.
EXTERIOR_RULES = [
    "front_setback_south", "rear_setback_north", "side_setback_west",
    "side_setback_east", "min_width_ew", "min_depth_ns", "tree_buffer",
    "door_on_south_wall", "door_corner_margin", "door_within_entry_segment",
    "corner_inside_plot", "min_area_coverage", "max_lot_coverage",
]

# Interior rule names the checker can emit — used by the rules= subset filter
# and documented in Z3_TOOL_DESIGN.md so the Verifier Agent knows what exists.
INTERIOR_RULES = [
    "room_count", "room_in_footprint", "room_min_area", "room_min_side",
    "room_max_side", "no_overlap", "coverage", "corridor_fraction",
    "ensuite_attached", "bath_smaller", "bath_not_adj_kitchen",
    "baths_not_adjacent", "living_near_south", "living_gt_bedroom",
    "door_in_living", "kitchen_by_living", "connected",
]


def _house(obj) -> HouseGeometry:
    if isinstance(obj, HouseGeometry):
        return obj
    return HouseGeometry(
        corners=tuple((float(x), float(y)) for x, y in obj["corners"]),
        door=(float(obj["door"][0]), float(obj["door"][1])))


def optimize_area(city: str = None, *, constraints: dict = None, plot=PLOT) -> dict:
    """OPTIMIZE mode — provable max buildable area for a city OR a constraint dict."""
    sbc, _tol, source = _resolve_exterior(city, constraints, None)
    t0 = perf_counter()
    area, corners = compute_max_area(plot, sbc)
    dt = perf_counter() - t0
    return {
        "source": source, "mode": "optimize",
        "max_buildable_area_sqft": round(area, 1),
        "optimal_corners": {k: round(v, 2) for k, v in corners.items()},
        "coverage_threshold_sqft": round(area * sbc.min_area_fraction_of_max, 1),
        "solve_time_s": round(dt, 4),
    }


def _resolve_exterior(city, constraints, tolerance_ft):
    """Return (sbc, tolerance_ft, source) from EITHER a city name OR a
    constraints dict (the Constraint Engine's ruleset) — modular input."""
    if constraints is not None:
        ext = constraints.get("exterior", constraints)   # full schema or bare block
        tol = (tolerance_ft if tolerance_ft is not None
               else float(constraints.get("tolerance_ft", verifier_z3.FLOAT_TOL)))
        return sbc_from_dict(ext), tol, constraints.get("jurisdiction", "custom-constraints")
    if city is not None:
        cc = load_city(city)
        return cc.sbc, (tolerance_ft if tolerance_ft is not None else cc.tolerance_ft), cc.city
    raise ValueError("pass either city=... or constraints=...")


def _resolve_interior(city, constraints, tolerance_ft):
    """Like _resolve_exterior, plus the two interior thresholds the Constraint
    Engine can override (corridor cap, coverage tolerance)."""
    corridor_max, cov_tol = program.CORRIDOR_MAX_FRAC, program.COVERAGE_TOL_FRAC
    if constraints is not None:
        interior = constraints.get("interior", {})
        corridor_max = float(interior.get("corridor_max_fraction_of_usable", corridor_max))
        cov_tol = float(interior.get("coverage_tol_fraction", cov_tol))
        ext = constraints.get("exterior", {})
        sbc = sbc_from_dict(ext) if ext else SBC
        tol = (tolerance_ft if tolerance_ft is not None
               else float(constraints.get("tolerance_ft", verifier_z3.FLOAT_TOL)))
        return sbc, tol, constraints.get("jurisdiction", "custom-constraints"), corridor_max, cov_tol
    if city is not None:
        cc = load_city(city)
        tol = tolerance_ft if tolerance_ft is not None else cc.tolerance_ft
        return cc.sbc, tol, cc.city, corridor_max, cov_tol
    return SBC, (tolerance_ft if tolerance_ft is not None else verifier_z3.FLOAT_TOL), \
        "IRC-default", corridor_max, cov_tol


def verify_site(house, city: str = None, *, constraints: dict = None,
                rules=None, tolerance_ft: float = None, plot=PLOT) -> dict:
    """Verify a site/exterior layout against a city OR a constraint dict.

      house       : {"corners": [[x,y] x4], "door": [x,y]}
      city        : a configured city (loads citycodes/<city>.json), OR
      constraints : a ruleset dict (Constraint Engine output) used directly.
      rules       : optional subset of rule names to check/report (None = all).

    Returns sat/unsat ("ok"), a per-rule pass/fail list, and the failure count.
    """
    sbc, tol, source = _resolve_exterior(city, constraints, tolerance_ft)
    verifier_z3.FLOAT_TOL = tol
    geom = _house(house)
    want = set(rules) if rules else None
    t0 = perf_counter()
    max_area, _ = compute_max_area(plot, sbc)
    violations = check(geom, plot, sbc, max_legal_area=max_area)
    dt = perf_counter() - t0

    vmap = {}
    for vi in violations:
        vmap.setdefault(vi.rule.split("[")[0], vi)    # group corner_inside_plot[i]
    report = []
    for r in EXTERIOR_RULES:
        if want and r not in want:                    # subset filter
            continue
        vi = vmap.get(r)
        report.append({
            "rule": r, "pass": vi is None,
            "measured": round(vi.measured_ft, 3) if vi else None,
            "required": round(vi.required_ft, 3) if vi else None,
            "message": vi.message if vi else "satisfied",
        })
    return {
        "source": source, "mode": "site/exterior",
        "ok": all(c["pass"] for c in report),
        "n_checked": len(report),
        "n_failed": sum(1 for c in report if not c["pass"]),
        "constraints": report,
        "unknown_rules": sorted(want - set(EXTERIOR_RULES)) if want else [],
        "max_buildable_area_sqft": round(max_area, 1),
        "tolerance_ft": tol, "solve_time_s": round(dt, 4),
    }


def verify_interior(layout: dict, city: str = None, *, constraints: dict = None,
                    rules=None, mode: str = "freeform", tolerance_ft: float = None) -> dict:
    """Verify an interior layout against the room rules.

      layout      : {"footprint":[x0,y0,x1,y1], "door":[x,y],
                     "rooms":[[name,kind,x_min,y_min,x_max,y_max], ...]}
      constraints : optional ruleset dict; may override corridor cap + coverage tol.
      rules       : optional subset of rule names to report (None = all).

    Returns sat/unsat ("ok"), the list of violations, and the failure count.
    """
    sbc, tol, source, corr_max, cov_tol = _resolve_interior(city, constraints, tolerance_ft)
    verifier_z3.FLOAT_TOL = tol
    lay = InteriorLayout(
        footprint=tuple(layout["footprint"]), door=tuple(layout["door"]),
        rooms=tuple(Room(*r) for r in layout["rooms"]))
    want = set(rules) if rules else None
    t0 = perf_counter()
    viol = check_interior(lay, sbc, mode=mode, require_full_coverage=False,
                          coverage_tol_frac=cov_tol, corridor_max_frac=corr_max)
    dt = perf_counter() - t0
    if want:                                          # subset filter
        viol = [v for v in viol if v.rule.split("[")[0] in want]
    return {
        "source": source, "mode": f"interior/{mode}",
        "ok": not viol, "n_failed": len({v.rule for v in viol}),
        "violations": [{"rule": v.rule, "measured": round(v.measured_ft, 3),
                        "required": round(v.required_ft, 3), "message": v.message}
                       for v in viol],
        "unknown_rules": sorted(want - set(INTERIOR_RULES)) if want else [],
        "tolerance_ft": tol, "solve_time_s": round(dt, 4),
    }


def verify_elevation(view: dict, city: str = None, *, constraints: dict = None, rules=None) -> dict:
    """Verify a side-view / facade ELEVATION (for the Side Views Agent).

    Consumes the Side View Agent's compiled_coordinates.json DIRECTLY (auto
    metres->feet). `view` has: units, footprint / boundary_3d, rooms[] (with
    polygon_3d, floor_z_m, ceiling_z_m, type), doors[], windows[].

    Driven by the ruleset: exterior.max_height_ft + interior.room_specs
    (requires_exterior_window). Returns sat/unsat ("ok") + violations.
    """
    from elevation_verifier_z3 import check_elevation
    max_h, room_specs, source = None, None, "IRC-default"
    if constraints is not None:
        max_h = constraints.get("exterior", constraints).get("max_height_ft")
        room_specs = (constraints.get("interior") or {}).get("room_specs")
        source = constraints.get("jurisdiction", "custom-constraints")
    elif city is not None:
        cc = load_city(city)
        max_h = cc.raw.get("exterior", {}).get("max_height_ft")
        room_specs = cc.raw.get("interior", {}).get("room_specs")
        source = cc.city
    t0 = perf_counter()
    viol = check_elevation(view, max_height_ft=max_h, room_specs=room_specs)
    dt = perf_counter() - t0
    want = set(rules) if rules else None
    if want:
        viol = [x for x in viol if x.rule in want]
    return {
        "source": source, "mode": "elevation", "units_in": view.get("units", "feet"),
        "ok": not viol, "n_failed": len(viol),
        "violations": [{"rule": x.rule, "measured": x.measured,
                        "required": x.required, "message": x.message} for x in viol],
        "max_height_ft": max_h,
        "solve_time_s": round(dt, 4),
    }


def verify_windows(windows, rooms, city: str = None, *, constraints: dict = None, rules=None) -> dict:
    """Verify WINDOW code compliance — the shift-left, deterministic layer.

      windows : [{room, type, width_ft, height_ft, sill_height_ft, operable_type,
                  tempered, adjacent_to_door, egress_clear_sqft?}, ...]
      rooms   : [{id/name, type, floor_area_sqft}, ...]

    Grounded in IRC R310 (egress) / R303 (light+vent) / R308 (safety glazing).
    Deterministic; the same rules can be given to the generator as constraints.
    """
    from window_verifier_z3 import check_windows
    import window_rules as R
    source = "IRC-default"
    if constraints is not None:
        source = constraints.get("jurisdiction", "custom-constraints")
        params = R.params_from_ruleset(constraints)
    elif city is not None:
        cc = load_city(city); source = cc.city
        params = R.params_from_ruleset(cc.raw)
    else:
        params = R.params_from_ruleset(None)
    t0 = perf_counter()
    viol = check_windows(windows, rooms, params=params)
    dt = perf_counter() - t0
    want = set(rules) if rules else None
    if want:
        viol = [x for x in viol if x.rule in want]
    return {
        "source": source, "mode": "windows",
        "ok": not viol, "n_failed": len(viol),
        "violations": [{"rule": x.rule, "measured": x.measured,
                        "required": x.required, "message": x.message} for x in viol],
        "solve_time_s": round(dt, 4),
    }


# --------------------------------------------------------------------------- #
#  CLI
# --------------------------------------------------------------------------- #
def _print_site(res):
    print(f"\n  Z3 VERIFIER — {res['source']} — site/exterior")
    print(f"  tolerance = {res['tolerance_ft']} ft   "
          f"max buildable = {res['max_buildable_area_sqft']} sq ft")
    print(f"  {'constraint':27s}{'result':8s}{'measured':>11s}{'required':>11s}")
    print("  " + "-" * 57)
    for c in res["constraints"]:
        m = "" if c["measured"] is None else f"{c['measured']}"
        rq = "" if c["required"] is None else f"{c['required']}"
        print(f"  {c['rule']:27s}{'PASS' if c['pass'] else 'FAIL':8s}{m:>11s}{rq:>11s}")
    verdict = "ALL CONSTRAINTS SATISFIED" if res["ok"] else f"{res['n_failed']} CONSTRAINT(S) FAILED"
    print(f"  " + "-" * 57)
    print(f"  => {verdict}   ({res['solve_time_s']}s, "
          f"{'OK' if res['solve_time_s'] < 5 else 'SLOW'} vs 5s budget)\n")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Z3 deterministic layout verifier")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cities", help="list supported cities")
    po = sub.add_parser("optimize", help="provable maximum buildable area")
    po.add_argument("--city", required=True)
    pv = sub.add_parser("verify", help="verify a site/exterior layout")
    pv.add_argument("--city", required=True)
    pv.add_argument("--layout", help="house JSON {corners:[[x,y]x4], door:[x,y]}")
    pv.add_argument("--json", action="store_true", help="print raw JSON")
    pi = sub.add_parser("interior", help="verify an interior layout")
    pi.add_argument("--city", required=True)
    pi.add_argument("--layout", required=True)
    pi.add_argument("--json", action="store_true")
    a = p.parse_args(argv)

    if a.cmd == "cities":
        print("Supported cities:", ", ".join(available_cities()))
        return 0

    if a.cmd == "optimize":
        res = optimize_area(a.city)
        print(json.dumps(res, indent=2))
        return 0

    if a.cmd == "verify":
        if a.layout:
            house = json.loads(open(a.layout).read())
        else:                                    # demo: the Z3-optimal house (should pass)
            opt = optimize_area(a.city)["optimal_corners"]
            house = {"corners": [[opt["x_min"], opt["y_min"]], [opt["x_max"], opt["y_min"]],
                                 [opt["x_max"], opt["y_max"]], [opt["x_min"], opt["y_max"]]],
                     "door": [(opt["x_min"] + opt["x_max"]) / 2, opt["y_min"]]}
        res = verify_site(house, a.city)
        print(json.dumps(res, indent=2) if a.json else "", end="")
        if not a.json:
            _print_site(res)
        return 0 if res["ok"] else 1

    if a.cmd == "interior":
        res = verify_interior(json.loads(open(a.layout).read()), a.city)
        print(json.dumps(res, indent=2))
        return 0 if res["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
