"""Orchestrator: A1 (Gemini) ⇄ parser ⇄ Z3 ⇄ A2 (Groq) ⇄ A1 ...

Run with:
    python loop.py
Env vars (in .env):
    GEMINI_API_KEY, GROQ_API_KEY,
    optional: GEMINI_MODEL, GROQ_MODEL, MAX_ITERATIONS, DXF_OUT
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv

from plot import PLOT
from constraints import SBC
import agent1_gemini
import agent2_groq
import geometry_parser
import verifier_z3

OUTPUT_DIR = Path(__file__).parent / "output"
MAX_ITERATIONS = int(os.environ.get("MAX_ITERATIONS", "5"))


def _save_iteration_artifacts(iteration: int, code: str, feedback: str | None) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    code_path = OUTPUT_DIR / f"iter_{iteration:02d}_a1_code.py"
    code_path.write_text(code)
    if feedback:
        (OUTPUT_DIR / f"iter_{iteration:02d}_a2_feedback.txt").write_text(feedback)
    return code_path


def _execute_dxf_script(code: str, dxf_path: Path) -> tuple[bool, str]:
    """Run A1's script in a subprocess to actually emit the .dxf. Returns
    (success, stderr-or-empty). Best-effort: parse errors are surfaced but
    the loop's correctness gate is already Z3, not script execution."""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write(code)
        script_path = f.name
    env = {**os.environ, "DXF_OUT": str(dxf_path)}
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True, text=True, timeout=15, env=env,
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Script timed out after 15 s"
    finally:
        os.unlink(script_path)


def main() -> int:
    load_dotenv()
    print(f"== PS1 House Layout — loop (max {MAX_ITERATIONS} iters) ==\n")
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

        violations = verifier_z3.check(geom, PLOT, SBC)
        if not violations:
            print(f"\n✅ Z3: ALL CONSTRAINTS SATISFIED on iter {iteration}.")
            dxf_path = OUTPUT_DIR / f"final_iter_{iteration:02d}.dxf"
            ok, err = _execute_dxf_script(code, dxf_path)
            if ok and dxf_path.exists():
                print(f"   .dxf written → {dxf_path}")
            else:
                print(f"   (script execution failed: {err.strip()[:200]})")
                print("   But Z3 verified the geometry — see the magic comments "
                      "in the saved code for the final corners.")
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
