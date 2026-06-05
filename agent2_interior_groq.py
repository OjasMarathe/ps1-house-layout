"""Agent 2 (interior) — Groq verifier-explainer for the floor plan.

Z3 (interior_verifier_z3.py) is the judge. This agent rewrites Z3's raw
interior-violation list into short, prioritized, actionable feedback for A1,
exactly like agent2_groq.py does for the exterior. Has the same offline
fallback so the loop still runs without a GROQ_API_KEY.
"""

import os
from textwrap import dedent

from groq import Groq

from interior_verifier_z3 import InteriorViolation

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")

# 10 interior rules — see interior_verifier_z3 docstring.
TOTAL_RULES = 10


def _format(violations: list[InteriorViolation]) -> str:
    return "\n".join(
        f"- [{v.rule}] {v.message} "
        f"(measured={v.measured_ft:.2f}, required={v.required_ft:.2f})"
        for v in violations)


def _header(violations: list[InteriorViolation]) -> str:
    missed = {v.rule for v in violations}
    return (f"Out of {TOTAL_RULES} interior rules, you missed "
            f"{len(missed)} — fix and regenerate.")


def explain_interior(violations: list[InteriorViolation], iteration: int) -> str:
    if not violations:
        return ""

    header = _header(violations)
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        return f"{header}\n\n{_format(violations)}"

    client = Groq(api_key=api_key)
    sys = dedent("""
        You are a code-review assistant for an LLM that generates architectural
        floor plans. A Z3 SMT solver produced a list of constraint violations on
        a proposed room layout. Rewrite them as a short, prioritized, actionable
        feedback list for the generator. Be concrete and remember the rooms must
        TILE the footprint — if you tell it to grow one room, remind it to shrink
        the neighbour so no gap/overlap appears. Do NOT invent constraints not in
        the list. Output ONLY the feedback list, no preamble or sign-off.
        """).strip()
    user = dedent(f"""
        Iteration {iteration}. Z3 reports these interior violations:

        {_format(violations)}

        Rewrite as actionable feedback for the floor-plan generator.
        """).strip()

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": user}],
        temperature=0.2,
    )
    return f"{header}\n\n{resp.choices[0].message.content.strip()}"
