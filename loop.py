"""Orchestrator: A1 (Gemini) ⇄ parser ⇄ Z3 ⇄ A2 (Groq) ⇄ A1 ...

Run with:
    python loop.py
Env vars (in .env):
    GEMINI_API_KEY, GROQ_API_KEY,
    optional: GEMINI_MODEL, GROQ_MODEL, MAX_ITERATIONS, DXF_OUT
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from plot import PLOT
from constraints import SBC
import agent1_gemini
import agent2_groq
import geometry_parser
import verifier_z3
import optimizer_z3
import dxf_emitter

OUTPUT_DIR = Path(__file__).parent / "output"
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))


def _save_iteration_artifacts(iteration: int, code: str, feedback: str | None) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    code_path = OUTPUT_DIR / f"iter_{iteration:02d}_a1_code.py"
    code_path.write_text(code)
    if feedback:
        (OUTPUT_DIR / f"iter_{iteration:02d}_a2_feedback.txt").write_text(feedback)
    return code_path


# NOTE: We deliberately do NOT execute A1's generated script. Once Z3 verifies
# the geometry extracted from the magic comments, dxf_emitter.emit_dxf() writes
# a clean .dxf from the verified numbers. This makes the .dxf output a function
# of the *verified* design rather than of A1's possibly-broken Python.


def main() -> int:
    load_dotenv()
    print(f"== PS1 House Layout — loop (max {MAX_ITERATIONS} iters) ==\n")

    print("== Z3 Optimize: computing theoretical max-area house ==")
    max_area, opt_corners = optimizer_z3.compute_max_area(PLOT, SBC)
    print(f"   Z3-provable maximum: {max_area:.0f} sq ft "
          f"at corners {opt_corners}")
    print(f"   Threshold ({SBC.min_area_fraction_of_max*100:.0f}% of max): "
          f"{max_area * SBC.min_area_fraction_of_max:.0f} sq ft\n")

    feedback: str | None = None

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"--- iter {iteration} : A1 (Gemini) generating ---")
        try:
            code = agent1_gemini.generate(feedback=feedback, iteration=iteration)
        except Exception as e:
            print(f"A1 call failed: {e}", file=sys.stderr)
            return 2
        code_path = _save_iteration_artifacts(iteration, code, feedback)
        print(f"  wrote {code_path}")

        try:
            geom = geometry_parser.parse(code)
        except geometry_parser.GeometryParseError as e:
            print(f"  parse error: {e}")
            feedback = (f"PARSE ERROR: {e}\nRe-emit the script with both magic "
                        "comment lines exactly as specified.")
            continue
        print(f"  parsed corners={geom.corners} door={geom.door}")

        violations = verifier_z3.check(geom, PLOT, SBC, max_legal_area=max_area)
        if not violations:
            print(f"\n✅ Z3: ALL CONSTRAINTS SATISFIED on iter {iteration}.")
            dxf_path = OUTPUT_DIR / f"final_iter_{iteration:02d}.dxf"
            dxf_emitter.emit_dxf(geom, PLOT, dxf_path, max_legal_area=max_area)
            xs = [c[0] for c in geom.corners]; ys = [c[1] for c in geom.corners]
            w, d = max(xs) - min(xs), max(ys) - min(ys)
            area = w * d
            print(f"   house: {w:.0f} × {d:.0f} ft = {area:.0f} sq ft "
                  f"({area/max_area*100:.1f}% of Z3 max)")
            print(f"   .dxf written → {dxf_path}")
            return 0

        print(f"  ❌ Z3: {len(violations)} violation(s)")
        for v in violations:
            print(f"     - {v.rule}: {v.message}")

        print(f"--- iter {iteration} : A2 (Groq) writing feedback ---")
        feedback = agent2_groq.explain(violations, iteration)
        print(f"  feedback:\n{feedback}\n")

    print(f"\n❌ Did not converge in {MAX_ITERATIONS} iterations.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
