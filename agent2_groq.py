"""Agent 2 — Groq verifier-explainer.

Z3 is the actual judge (see verifier_z3.py). This agent's job is to take Z3's
raw violation list and rewrite it as prioritized, actionable feedback for A1.
It also gets to add domain-aware suggestions ("move house 3 ft north" rather
than just "south setback is 17, need 20").
"""

import os
from textwrap import dedent

from groq import Groq

from verifier_z3 import Violation

MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


TOTAL_RULES = 9  # SBC rules (8 hard + min_area_coverage)


def _format_violations(violations: list[Violation]) -> str:
    lines = []
    for v in violations:
        lines.append(
            f"- [{v.rule}] {v.message} "
            f"(measured={v.measured_ft:.2f}, required={v.required_ft:.2f})"
        )
    return "\n".join(lines)


def _header(violations: list[Violation]) -> str:
    """Match the brief's expected feedback format (§1.2):
       'Out of N constraints, you missed X — fix and regenerate.'"""
    rules_missed = {v.rule for v in violations}
    return (f"Out of {TOTAL_RULES} SBC constraints, you missed "
            f"{len(rules_missed)} — fix and regenerate.")


def explain(violations: list[Violation], iteration: int) -> str:
    """Return a feedback string suitable for passing back to A1."""
    if not violations:
        return ""

    header = _header(violations)
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Graceful offline fallback: header + raw messages
        return f"{header}\n\n{_format_violations(violations)}"

    client = Groq(api_key=api_key)

    sys = dedent("""
        You are a code-review assistant for an LLM that generates engineering
        drawings. The Z3 SMT solver has produced a list of constraint
        violations on a proposed house layout. Rewrite them as a short,
        prioritized, actionable feedback list for the generator. Be concrete:
        when possible, suggest specific coordinate moves (e.g. "shift the
        south wall north by 3 ft"). Do NOT invent constraints not in the list.
        Output ONLY the feedback list, no preamble or sign-off.
        """).strip()

    user = dedent(f"""
        Iteration {iteration}. Z3 reports these violations:

        {_format_violations(violations)}

        Rewrite as actionable feedback for the generator.
        """).strip()

    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": sys},
                  {"role": "user", "content": user}],
        temperature=0.2,
    )
    body = resp.choices[0].message.content.strip()
    return f"{header}\n\n{body}"
