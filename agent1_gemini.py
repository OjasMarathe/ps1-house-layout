"""Agent 1 — Gemini generator.

Produces a Python script using `ezdxf` that draws the house outline and door.
Must include two magic comment lines that `geometry_parser` keys on:
    # HOUSE_CORNERS: [(x,y), (x,y), (x,y), (x,y)]
    # DOOR: (x, y)
"""

import os
import time
from textwrap import dedent

from google import genai
from google.genai import types
from google.genai import errors as genai_errors

from plot import PLOT, Plot
from constraints import SBC, SBCConstraints

MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "4"))


def _system_prompt(plot: Plot, sbc: SBCConstraints) -> str:
    entry_x = sorted([plot.entry_segment[0][0], plot.entry_segment[1][0]])
    entry_w = entry_x[1] - entry_x[0]
    px_min, py_min, px_max, py_max = plot.bbox

    return dedent(f"""
        You are an engineering-drawing assistant. Write a Python script using
        the `ezdxf` library that draws the outer periphery of a single-family
        house and its main door, following Seattle Building Code (SBC).

        # Plot (high-level)
        Units: feet. +x East, +y North.
        - Roughly L-shaped, overall bounding box {px_max - px_min:.0f} ft (E-W) × {py_max - py_min:.0f} ft (N-S).
        - Most of the area is the main rectangular body.
        - A protected tree sits at the TOP-RIGHT of the plot. It cannot be
          removed or built on (~$50k fine). Treat the top-right corner of the
          plot as off-limits with a generous margin.
        - The ENTRY is on the SOUTH side: a {entry_w:.0f} ft wide segment
          where the driveway, parking, and main door must all be reached.

        # YOUR PRIMARY OBJECTIVE
        **Maximize the house footprint area.** Push the house outward to the
        legal limit of every setback. Do not be conservative — leaving extra
        space beyond setbacks is wasted area. Z3 will verify the geometry.

        # SBC rules (numeric thresholds; the layout itself is your design)
        - Front (south, entry-side) setback ≥ {sbc.front_setback_ft:.0f} ft
        - Rear (north) setback ≥ {sbc.rear_setback_ft:.0f} ft
        - Side (east and west) setbacks ≥ {sbc.side_setback_ft:.0f} ft each
        - Minimum footprint ≥ {sbc.min_house_width_ft:.0f}×{sbc.min_house_depth_ft:.0f} ft
        - Stay clear of the protected tree (top-right area)
        - All four corners must lie inside the plot. If the verifier later
          reports a corner outside, you hit a notch/tab edge of the L-shape —
          pull that corner in.
        - House outline = axis-aligned rectangle, corners in order SW, SE, NE, NW
        - Door on the house's south wall, within the south entry segment,
          inset ≥ {sbc.door_corner_margin_ft:.0f} ft from both house corners
        - **Footprint area ≥ {sbc.min_area_fraction_of_max*100:.0f}% of the
          theoretical maximum** (the Z3 solver computes this max from the
          setbacks alone; you don't need to know it, but a layout that just
          satisfies setbacks with no slack will pass. A layout with slack on
          any setback will fail this rule.)

        # OUTPUT FORMAT — MANDATORY, READ CAREFULLY
        Output ONLY a Python script (no markdown fence, no prose).

        The FIRST TWO LINES of the script must be these magic comments with
        ACTUAL NUMERIC COORDINATES already substituted. Do NOT copy the
        placeholder names below; replace them with concrete floats you choose.

        EXAMPLE (illustrative numbers — choose your own):
            # HOUSE_CORNERS: [(10.0, 25.0), (50.0, 25.0), (50.0, 70.0), (10.0, 70.0)]
            # DOOR: (30.0, 25.0)
            import ezdxf
            ...

        Rules for those two lines:
        - They must be at the very top of the file, before any imports.
        - The values must be literal numbers (no variables, no expressions, no
          f-strings, no `print(...)` of them — they are STATIC metadata that a
          regex will read without running the script).
        - Corner order: SW, SE, NE, NW (axis-aligned rectangle).
        - DOOR must lie on the SW-SE edge (i.e. door_y == SW_y).

        After those two lines, write the actual ezdxf script: draw the plot
        boundary polygon, the tree circle, the house outline (lwpolyline
        through the four corners), and a small circle at DOOR. Then call
        `doc.saveas(os.environ.get("DXF_OUT", "output/house.dxf"))`. Do not do
        anything else with side effects.
        """).strip()


def _user_prompt(feedback: str | None, iteration: int) -> str:
    if not feedback:
        return ("Generate the first attempt. Aim for maximum footprint while "
                "respecting every constraint above.")
    return dedent(f"""
        Iteration {iteration}. Forget your previous solution.

        Current facts:
        1. Your previous HOUSE_CORNERS and DOOR are STALE — do not reuse them
           as a starting point. Treat the polygon + SBC rules as the only
           ground truth.
        2. The Z3 SMT solver (not the verifier LLM) reports these violations:

        {feedback}

        Before emitting code:
        - Restate which assumption(s) from your previous attempt were wrong.
        - List the moves that will fix EACH violation independently.
        - Pick a single coherent new geometry that satisfies all of them.

        Then output the full script with updated HOUSE_CORNERS and DOOR
        markers at the top. Keep the footprint as large as possible within
        the rules.
        """).strip()


def generate(feedback: str | None = None, iteration: int = 1) -> str:
    """Return Python source code as a string."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Set GEMINI_API_KEY in .env")

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=60_000),  # ms; fail fast
    )
    cfg = types.GenerateContentConfig(
        system_instruction=_system_prompt(PLOT, SBC),
        temperature=0.2,
        # 2.5-* models think by default; disable for code generation
        thinking_config=types.ThinkingConfig(thinking_budget=0),
    )
    last_err: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"  calling Gemini (attempt {attempt}/{MAX_RETRIES})...", flush=True)
            resp = client.models.generate_content(
                model=MODEL,
                contents=_user_prompt(feedback, iteration),
                config=cfg,
            )
            break
        except genai_errors.APIError as e:
            # 503 = UNAVAILABLE, 429 = RESOURCE_EXHAUSTED — both retryable
            status = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status in (429, 503) and attempt < MAX_RETRIES:
                wait = 2 ** attempt  # 2, 4, 8, 16 s
                print(f"  Gemini {status}; retrying in {wait}s...", flush=True)
                time.sleep(wait)
                last_err = e
                continue
            raise
    else:
        raise RuntimeError(f"Gemini exhausted retries: {last_err}")
    code = resp.text or ""
    # Strip accidental markdown fences if the model wraps them anyway
    code = code.strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else code
        if code.endswith("```"):
            code = code.rsplit("```", 1)[0]
    return code.strip()
