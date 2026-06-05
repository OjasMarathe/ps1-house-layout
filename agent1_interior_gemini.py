"""Agent 1 (interior) — Gemini generator for the floor plan.

Phase 2 of the pipeline. Given the SBC-verified house footprint and front-door
position from Phase 1, this proposes how to subdivide the interior into the
required 7 rooms. It emits ONE magic comment line that interior_parser keys on:

    # ROOMS: [(name, kind, x_min, y_min, x_max, y_max), ...]

Mirrors agent1_gemini.py: minimalist system prompt, thinking disabled, short
timeout, exponential backoff, "forget your previous solution" retry prompt.
"""

import os
import time
from textwrap import dedent

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

import rooms as program

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "4"))


def _program_lines() -> str:
    out = []
    for s in program.PROGRAM:
        out.append(f"        - {s.count}× {s.kind:8s}: each ≥ {s.min_area_ft2:.0f} "
                   f"sq ft, every side ≥ {s.min_side_ft:.0f} ft")
    return "\n".join(out)


def _system_prompt(footprint: tuple[float, float, float, float],
                   door: tuple[float, float]) -> str:
    x0, y0, x1, y1 = footprint
    dx, dy = door
    W, D = x1 - x0, y1 - y0
    return dedent(f"""
        You are an architectural floor-plan assistant. The exterior of a house
        is already fixed and SBC-verified. Your job: subdivide its interior into
        rooms. A Z3 SMT solver will check your layout exactly.

        # The house footprint (fixed — do NOT change it)
        Axis-aligned rectangle, units = feet, +x East / +y North:
            x from {x0:.1f} to {x1:.1f}   ({W:.0f} ft wide, E-W)
            y from {y0:.1f} to {y1:.1f}   ({D:.0f} ft deep, N-S)
        Front door is on the SOUTH wall at ({dx:.1f}, {dy:.1f}).

        # Required rooms (the program — emit EXACTLY these 7)
{_program_lines()}

        # HARD RULES (Z3 will reject any violation)
        1. Every room is an axis-aligned rectangle fully inside the footprint.
        2. Rooms must TILE the footprint: no overlaps, and NO GAPS. Every square
           foot of the footprint belongs to exactly one room. (Sum of room areas
           must equal the footprint area, {W * D:.0f} sq ft.)
        3. The front door must open into the LIVING room: the living room sits on
           the south wall (its y_min = {y0:.1f}) and spans across x={dx:.1f},
           inset ≥ 2 ft from its own side walls.
        4. The kitchen must share a wall (≥ 2.5 ft) with the living room.
        5. WET WALL: the kitchen must share a wall (≥ 2.5 ft) with at least one
           bathroom (shared plumbing).
        6. Every room must connect to the rest through a wall ≥ 2.5 ft wide
           (you can physically walk between all rooms).

        # A LAYOUT THAT ALWAYS WORKS (recommended structure — pick the cut
        # positions yourself, but this banding makes tiling trivial)
        Three horizontal bands, south to north:
          • PUBLIC band (south, touching the door): LIVING on the west half,
            KITCHEN on the east half. The living room contains the door.
          • BATH band (middle): the 2 bathrooms side by side, full width.
          • BEDROOM band (north): the 3 bedrooms side by side, full width.
        Each band spans the full {W:.0f} ft width; you choose the band heights
        (south→north they must sum to {D:.0f} ft) and the vertical split points.

        # OUTPUT FORMAT — MANDATORY
        Output ONLY a Python script (no markdown fence, no prose).
        The FIRST LINE must be the magic comment with ACTUAL NUMBERS:

            # ROOMS: [("Living","living",{x0:.1f},{y0:.1f},X,Y), ("Kitchen","kitchen",...), ...]

        Rules for that line:
        - It is STATIC metadata read by a regex; use literal numbers only (no
          variables, no expressions, no f-strings).
        - 7 entries, each (name, kind, x_min, y_min, x_max, y_max).
        - kind ∈ {{"living","kitchen","bathroom","bedroom"}} (lowercase).
        After it, write a short ezdxf script that draws the footprint and each
        room rectangle, then `doc.saveas(os.environ.get("DXF_OUT","output/interior.dxf"))`.
        No other side effects.
        """).strip()


def _user_prompt(feedback: str | None, iteration: int) -> str:
    if not feedback:
        return ("Generate the first interior layout. Make the rooms generous and "
                "balanced while satisfying every rule above.")
    return dedent(f"""
        Iteration {iteration}. Forget your previous layout.

        Current facts:
        1. Your previous ROOMS list is STALE — do not reuse it as a starting
           point. The footprint, the door, and the rules above are the only
           ground truth.
        2. The Z3 SMT solver (not the verifier LLM) reports these violations:

        {feedback}

        Before emitting code:
        - Restate which assumption(s) in your previous layout were wrong.
        - List the move that fixes EACH violation (watch tiling: if you grow one
          room you must shrink its neighbour so there is no gap or overlap).
        - Then output the full script with an updated `# ROOMS:` line on top.
        """).strip()


def generate_interior(footprint: tuple[float, float, float, float],
                      door: tuple[float, float],
                      feedback: str | None = None,
                      iteration: int = 1) -> str:
    """Return Python source code (string) whose first line is `# ROOMS: [...]`."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in .env")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60_000),
    )
    cfg = types.GenerateContentConfig(
        system_instruction=_system_prompt(footprint, door),
        temperature=0.2,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  calling Gemini interior (attempt {attempt}/{MAX_RETRIES})...",
                  flush=True)
            resp = client.models.generate_content(
                model=MODEL, contents=_user_prompt(feedback, iteration), config=cfg)
            break
        except genai_errors.APIError as e:
            status = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status in (429, 503) and attempt < MAX_RETRIES:
                wait = 2 ** attempt
                print(f"  Gemini {status}; retrying in {wait}s...", flush=True)
                time.sleep(wait)
                last_err = e
                continue
            raise
    else:
        raise RuntimeError(f"Gemini exhausted retries: {last_err}")

    code = (resp.text or "").strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else code
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0]
    return code.strip()
