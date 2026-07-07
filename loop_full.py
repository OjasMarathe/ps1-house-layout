"""Full automated workflow — Phase 1 (exterior) ➜ Phase 2 (interior).

    python loop_full.py

Phase 1 reuses the existing exterior pipeline (Z3 Optimize target ➜ A1 Gemini
➜ parser ➜ Z3 verifier ➜ A2 Groq) to converge on an SBC-legal house footprint.
Phase 2 subdivides that footprint into the 8-room program (living, kitchen,
corridor, 3 bedrooms, 2 ensuite bathrooms) with a MILP / cutting-plane solver
(PuLP + CBC) — generate-and-guarantee — and the same Z3 judge confirms the
full interior constraint set. Set INTERIOR_MODE=llm to instead run the Gemini
verify-and-fix loop with the MILP layout as the guaranteed fallback. The run
always ends with a complete, Z3-verified .dxf of plot + tree + house + rooms.

Env (.env): GEMINI_API_KEY, GROQ_API_KEY,
            optional GEMINI_MODEL, GROQ_MODEL, MAX_ITERATIONS, INTERIOR_MODE
Neither A1 script is ever executed — geometry comes from the magic comments,
and the .dxf is rendered deterministically from the verified numbers.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from plot import PLOT
from constraints import SBC

# Phase 1 (exterior)
import agent1_gemini
import agent2_groq
import geometry_parser
import verifier_z3
import optimizer_z3
from verifier_z3 import HouseGeometry

# Phase 2 (interior)
import agent1_interior_gemini
import agent2_interior_groq
import interior_parser
import interior_verifier_z3
import interior_milp
from interior_verifier_z3 import InteriorLayout

import dxf_full

OUTPUT_DIR = Path(__file__).parent / "output"
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))


def _save(name: str, text: str) -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / name).write_text(text)


def _footprint_of(house: HouseGeometry) -> tuple[float, float, float, float]:
    xs = [c[0] for c in house.corners]
    ys = [c[1] for c in house.corners]
    return (min(xs), min(ys), max(xs), max(ys))


# --------------------------------------------------------------------------- #
#  Phase 1 — exterior footprint
# --------------------------------------------------------------------------- #
def run_exterior(max_area: float) -> HouseGeometry:
    feedback: str | None = None
    for it in range(1, MAX_ITERATIONS + 1):
        print(f"--- [exterior] iter {it}: A1 (Gemini) generating ---")
        code = agent1_gemini.generate(feedback=feedback, iteration=it)
        _save(f"ext_iter_{it:02d}_a1.py", code)
        try:
            geom = geometry_parser.parse(code)
        except geometry_parser.GeometryParseError as e:
            print(f"  parse error: {e}")
            feedback = f"PARSE ERROR: {e}\nRe-emit both magic comment lines exactly."
            continue
        print(f"  parsed corners={geom.corners} door={geom.door}")
        violations = verifier_z3.check(geom, PLOT, SBC, max_legal_area=max_area)
        if not violations:
            print(f"✅ [exterior] all SBC constraints satisfied on iter {it}.\n")
            return geom
        print(f"  ❌ {len(violations)} violation(s):")
        for v in violations:
            print(f"     - {v.rule}: {v.message}")
        feedback = agent2_groq.explain(violations, it)
        _save(f"ext_iter_{it:02d}_a2.txt", feedback)

    # Fallback: use the Z3-optimal footprint so the workflow still completes.
    print("⚠️  [exterior] A1 did not converge — falling back to the "
          "Z3-optimal footprint.\n")
    _, c = optimizer_z3.compute_max_area(PLOT, SBC)
    door_x = (c["x_min"] + c["x_max"]) / 2
    return HouseGeometry(
        corners=((c["x_min"], c["y_min"]), (c["x_max"], c["y_min"]),
                 (c["x_max"], c["y_max"]), (c["x_min"], c["y_max"])),
        door=(door_x, c["y_min"]))


# --------------------------------------------------------------------------- #
#  Phase 2 — interior layout
# --------------------------------------------------------------------------- #
def run_interior(footprint, door, reference: InteriorLayout) -> InteriorLayout:
    feedback: str | None = None
    for it in range(1, MAX_ITERATIONS + 1):
        print(f"--- [interior] iter {it}: A1 (Gemini) generating ---")
        code = agent1_interior_gemini.generate_interior(
            footprint, door, feedback=feedback, iteration=it)
        _save(f"int_iter_{it:02d}_a1.py", code)
        try:
            rooms = interior_parser.parse(code)
        except interior_parser.InteriorParseError as e:
            print(f"  parse error: {e}")
            feedback = f"PARSE ERROR: {e}\nRe-emit the `# ROOMS:` line exactly."
            continue
        layout = InteriorLayout(footprint=footprint, door=door, rooms=rooms)
        print(f"  parsed {len(rooms)} rooms")
        violations = interior_verifier_z3.check_interior(
            layout, SBC, require_full_coverage=False)
        if not violations:
            print(f"✅ [interior] all rules satisfied on iter {it}.\n")
            return layout
        print(f"  ❌ {len(violations)} violation(s):")
        for v in violations:
            print(f"     - {v.rule}: {v.message}")
        feedback = agent2_interior_groq.explain_interior(violations, it)
        _save(f"int_iter_{it:02d}_a2.txt", feedback)

    print("⚠️  [interior] A1 did not converge — using the MILP-generated "
          "(CBC) layout.\n")
    return reference


# --------------------------------------------------------------------------- #
def main() -> int:
    load_dotenv()
    print(f"== PS1 — FULL automated workflow (max {MAX_ITERATIONS} iters/phase) ==\n")

    # Phase 1 target.
    print("== Z3 Optimize: theoretical max-area footprint ==")
    max_area, opt_corners = optimizer_z3.compute_max_area(PLOT, SBC)
    print(f"   max {max_area:.0f} sq ft at {opt_corners}")
    print(f"   threshold ({SBC.min_area_fraction_of_max*100:.0f}% of max): "
          f"{max_area * SBC.min_area_fraction_of_max:.0f} sq ft\n")

    print("===== PHASE 1 — EXTERIOR =====")
    house = run_exterior(max_area)
    footprint = _footprint_of(house)
    fx0, fy0, fx1, fy1 = footprint
    area = (fx1 - fx0) * (fy1 - fy0)
    print(f"   footprint: {fx1-fx0:.0f} × {fy1-fy0:.0f} ft = {area:.0f} sq ft "
          f"({area/max_area*100:.1f}% of Z3 max), door {house.door}\n")

    print("===== PHASE 2 — INTERIOR (MILP / cutting-plane) =====")
    print("== CBC: generating a guaranteed-valid 8-room floor plan ==")
    try:
        milp = interior_milp.solve_layout(footprint, house.door, SBC)
    except RuntimeError as e:
        print(f"❌ {e}", file=sys.stderr)
        return 2
    reference = milp.layout
    residual = interior_verifier_z3.check_interior(reference, SBC, require_full_coverage=False)
    if residual:
        print("❌ MILP layout failed Z3 verification:", file=sys.stderr)
        for v in residual:
            print(f"     - {v.rule}: {v.message}", file=sys.stderr)
        return 2
    print(f"   CBC {milp.status}: {len(reference.rooms)} rooms, "
          f"{milp.fill_frac*100:.0f}% fill — Z3-verified (0 violations).\n")

    # Default: trust the MILP (generate-and-guarantee). Set INTERIOR_MODE=llm to
    # instead run the Gemini verify-and-fix loop, falling back to the MILP layout.
    mode = os.environ.get("INTERIOR_MODE", "milp").lower()
    if mode == "llm":
        interior = run_interior(footprint, house.door, reference)
    else:
        interior = reference

    # Final combined artifact.
    dxf_path = OUTPUT_DIR / "final_full_layout.dxf"
    dxf_full.emit_full_dxf(house, interior, PLOT, dxf_path)

    print("===== RESULT =====")
    print(f"   house {fx1-fx0:.0f}×{fy1-fy0:.0f} ft, {area:.0f} sq ft, "
          f"{len(interior.rooms)} rooms (all Z3-verified):")
    for r in interior.rooms:
        print(f"     - {r.name:10s} {r.kind:9s} {r.area:5.0f} sq ft  "
              f"({r.width:.0f}×{r.depth:.0f})")
    print(f"   .dxf → {dxf_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
