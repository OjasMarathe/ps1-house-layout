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

MODEL = os.environ.get("GROQ_MODEL", "moonshotai/kimi-k2-instruct")


def _format_violations(violations: list[Violation]) -> str:
    lines = []
    for v in violations:
        lines.append(
            f"- [{v.rule}] {v.message} "
            f"(measured={v.measured_ft:.2f}, required={v.required_ft:.2f})"
        )
    return "\n".join(lines)


def explain(violations: list[Violation], iteration: int) -> str:
    """Return a feedback string suitable for passing back to A1."""
    if not violations:
        return ""

    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        # Graceful offline fallback: just join the raw messages
        return _format_violations(violations)

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
    return resp.choices[0].message.content.strip()
