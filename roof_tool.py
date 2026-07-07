"""Roof Plan Agent — entry point (Cluster 4, Output & Export). Owner: Ojas.

Pipeline wiring (from The Big Picture / pipeline I/O reference):
  INPUT  <- top-floor footprint(s) + elevation data
            (Elevation / Multi-floor cluster, via the Agent Manager)
  OUTPUT -> roof polygon set tagged "view_type": "roof"
            -> DXF Generator (Harshit/Devam) + a distinct artifact in the PDF report.

`roof_plan(payload)` generates the roof, SELF-VERIFIES it with Z3 (roof matches
footprint, pitch/drainage present, eave setbacks, downward steps), and returns the
tagged output. Same propose->prove pattern the generators use with the Z3 tool.

CLI:
  python roof_tool.py --demo [--dxf] [--png]
  python roof_tool.py --input roof_in.json [--dxf] [--png] [--json]
"""
import argparse
import json
import sys

from roof_agent import generate_roof
from roof_verifier_z3 import check_roof
from constraints import SBC
from codeloader import sbc_from_dict


def _sbc(payload):
    c = payload.get("constraints")
    if c:
        return sbc_from_dict(c.get("exterior", c))
    return SBC


def _levels(payload):
    if "levels" in payload:
        return payload["levels"]
    # convenience: a single-floor payload
    return [{"level": payload.get("level", 1), "name": payload.get("name", "main"),
             "footprint": payload["footprint"], "top_height_ft": payload.get("top_height_ft", 0.0)}]


def _top_rooms(payload):
    """Top-floor rooms + their daylight scores (from the Window/Livability Agent),
    used to place skylights over the under-lit ones."""
    levels = _levels(payload)
    if not levels:
        return []
    top = max(levels, key=lambda lv: lv.get("top_height_ft", lv.get("level", 0)))
    rooms = [dict(r) for r in top.get("rooms", [])]
    scores = {}
    for r in (payload.get("daylight") or {}).get("rooms", []):
        scores[r.get("id", r.get("name"))] = r.get("daylight_score", r.get("daylight"))
    for r in rooms:
        key = r.get("name", r.get("id"))
        if "daylight_score" not in r and key in scores:
            r["daylight_score"] = scores[key]
    return rooms


def _schedule(roof):
    """Roof feature schedule — types, total area, ventilation totals, skylights, attic access."""
    secs = roof.get("roof_sections", [])
    skylights = [{"room": sk["room"], "size_ft": f"{sk['width_ft']:.0f}x{sk['length_ft']:.0f}",
                  "on_plane": sk["on_plane"]} for s in secs for sk in s.get("skylights", [])]
    vents = [s.get("ventilation", {}) for s in secs]
    return {
        "roof_types": sorted({s["type"] for s in secs}),
        "total_roof_area_sqft": round(sum(s.get("roof_area_sqft", 0) for s in secs), 1),
        "ventilation": {
            "total_roof_jacks_7x7": sum(v.get("roof_jacks_7x7", 0) for v in vents),
            "total_eave_birdblock_lf": round(sum(v.get("eave_birdblock_lf", 0) for v in vents), 1),
            "all_sections_ok": all(v.get("ok", True) for v in vents),
        },
        "skylights": skylights,
        "attic_access": "min 22 in x 30 in, insulated & weather-stripped (IRC R807.1)",
    }


def roof_plan(payload: dict, emit_dxf=None, emit_svg=None) -> dict:
    """Generate + self-verify a roof plan. Returns the tagged 'view_type':'roof' output."""
    levels = _levels(payload)
    roof = generate_roof(levels, payload.get("roof_spec", {}), payload.get("session_id"))
    top_rooms = _top_rooms(payload)          # skylights from Window-Agent daylight scores
    if top_rooms:
        from roof_agent import add_skylights
        add_skylights(roof, top_rooms)
    viol = check_roof(roof, levels, sbc=_sbc(payload))
    roof["verified"] = not viol
    roof["n_failed"] = len(viol)
    roof["violations"] = [{"rule": x.rule, "measured": x.measured,
                           "required": x.required, "message": x.message} for x in viol]
    roof["schedule"] = _schedule(roof)
    from roof_elevations import elevation_profiles
    roof["elevation_profiles"] = elevation_profiles(roof)   # for the Side-View Agent
    artifacts = {}
    if emit_dxf:
        from roof_dxf import write_roof_dxf
        artifacts["dxf"] = write_roof_dxf(roof, emit_dxf if isinstance(emit_dxf, str) else "output/roof_plan.dxf")
    if emit_svg:
        from roof_render import render_roof
        artifacts["svg"] = render_roof(roof, emit_svg if isinstance(emit_svg, str) else "output/roof_plan.svg")
    if artifacts:
        roof["artifacts"] = artifacts
    return roof


DEMO = {
    "session_id": "demo-001",
    # main house (gable) + a stepped garage at a lower level (shed) — non-overlapping
    "levels": [
        {"level": 1, "name": "main", "top_height_ft": 20.0,
         "footprint": [[24, 20], [66, 20], [66, 63], [24, 63]],
         "rooms": [   # top-floor rooms + daylight scores from the Window Agent (Aadi)
             {"name": "family_room", "type": "family_room", "daylight_score": 34,
              "polygon": [[44, 30], [62, 30], [62, 55], [44, 55]]},
             {"name": "bedroom_up", "type": "bedroom", "daylight_score": 71,
              "polygon": [[26, 30], [40, 30], [40, 55], [26, 55]]}]},
        {"level": 0, "name": "garage", "top_height_ft": 10.0,
         "footprint": [[6, 20], [21, 20], [21, 42], [6, 42]],
         "roof_spec": {"type": "shed", "drain_side": "W"}},
    ],
    "roof_spec": {"type": "gable", "pitch": "5:12", "overhang_ft": 0.0},
}


def _print(roof):
    v = "VERIFIED ✓" if roof["verified"] else f"{roof['n_failed']} VIOLATION(S)"
    print(f"\n  ROOF PLAN — {roof['n_sections']} section(s) — {v}")
    for s in roof["roof_sections"]:
        print(f"   · {s['name']:8s} {s['type']:5s} {s['pitch']:6s}  eave {s['eave_height_ft']:.1f}ft  "
              f"ridge {s['ridge_height_ft']:.1f}ft  drains {'/'.join(s['drainage'])}  "
              f"planes {len(s['planes'])}")
        for sk in s.get("skylights", []):
            print(f"     ☀ skylight over {sk['room']} on the {sk['on_plane']} plane "
                  f"(faces {sk['faces']}) — {sk['reason']}")
    for x in roof["violations"]:
        print(f"     ✗ {x['rule']}: {x['message']}")
    if roof.get("artifacts"):
        for k, p in roof["artifacts"].items():
            print(f"   → {k}: {p}")
    print()


def main(argv=None):
    p = argparse.ArgumentParser(description="Roof Plan Agent")
    p.add_argument("--input", help="input JSON {levels, roof_spec, constraints}")
    p.add_argument("--demo", action="store_true", help="run the built-in stepped-roof demo")
    p.add_argument("--dxf", nargs="?", const="output/roof_plan.dxf", help="emit DXF artifact")
    p.add_argument("--svg", nargs="?", const="output/roof_plan.svg", help="emit SVG plan render")
    p.add_argument("--json", action="store_true", help="print raw JSON output")
    a = p.parse_args(argv)
    if not a.input and not a.demo:
        p.error("pass --input <file> or --demo")
    payload = DEMO if a.demo else json.loads(open(a.input).read())
    roof = roof_plan(payload, emit_dxf=a.dxf, emit_svg=a.svg)
    if a.json:
        print(json.dumps(roof, indent=2))
    else:
        _print(roof)
    return 0 if roof["verified"] else 1


if __name__ == "__main__":
    sys.exit(main())
