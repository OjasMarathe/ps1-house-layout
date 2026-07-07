"""Conversational layout designer — Gemini places rooms from a description.

This is Agent 1 driven by the user's words instead of a fixed objective. The
user describes where rooms should go ("bedrooms bottom-left / top-left /
top-right, kitchen between the top bedrooms, …"); Gemini emits room rectangles;
`interior_fill` turns the leftover into distributed halls; Z3 verifies the core
rules (freeform mode); on failure the violations are fed back and Gemini
retries. Returns the layout plus a plain-English reply for the chat UI.
"""
import os
import time
from textwrap import dedent

from constraints import SBC
from interior_verifier_z3 import InteriorLayout, check_interior
import interior_parser
import interior_fill

# Which LLM places the rooms. Default Groq (Llama) — generous free tier.
# Set STUDIO_LLM=gemini to use Gemini instead (20 req/day free-tier cap).
PROVIDER = os.environ.get("STUDIO_LLM", "groq").lower()
MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
MAX_RETRIES = int(os.environ.get("GEMINI_MAX_RETRIES", "3"))


def _system(footprint, door) -> str:
    X0, Y0, X1, Y1 = footprint
    dx, dy = door
    mx, my = (X0 + X1) / 2, (Y0 + Y1) / 2
    return dedent(f"""
        You are an expert residential architect. You lay out the INTERIOR of a
        house as axis-aligned rectangles, following the client's description.

        # Coordinate system (feet)
        x runs WEST→EAST: x={X0:.0f} is the LEFT/WEST wall, x={X1:.0f} is the RIGHT/EAST wall.
        y runs SOUTH→NORTH: y={Y0:.0f} is the SOUTH/FRONT wall (where the door is, the
        "bottom"), y={Y1:.0f} is the NORTH/BACK wall (the "top").
        Centre of the house is about ({mx:.0f}, {my:.0f}).
        Position words map like this:
          bottom = south (low y) · top = north (high y) · left = west (low x) · right = east (high x)
          bottom-left ≈ ({X0:.0f},{Y0:.0f}) · top-right ≈ ({X1:.0f},{Y1:.0f}) · middle ≈ ({mx:.0f},{my:.0f})

        # The rooms to place (exactly these, unless the client says otherwise)
        3 bedrooms, 2 bathrooms, 1 kitchen, 1 living room.

        # HARD rules (a Z3 solver checks them; satisfy ALL)
        - Every room is a rectangle fully inside the footprint x∈[{X0:.0f},{X1:.0f}], y∈[{Y0:.0f},{Y1:.0f}].
        - No two rooms overlap.
        - Minimum sizes: living/kitchen/bedrooms ≥ 70 sq ft and every side ≥ 7 ft;
          bathrooms ≥ 25 sq ft, each side between 5 and 15 ft.
        - The FRONT DOOR is at ({dx:.0f},{dy:.0f}) on the south wall. The LIVING ROOM
          must sit on the south wall (its y_min = {Y0:.0f}) and span across x={dx:.0f},
          so the door opens into the living room.
        - Use most of the footprint with GENEROUS rooms: living & bedrooms roughly
          250–550 sq ft, kitchen 200–400 sq ft, baths 60–140 sq ft. Cover ~90% so
          only THIN gaps remain for circulation — do NOT leave big empty blocks.
          (Any leftover is auto-converted to hallways.)
        - CONNECTED: every room must share a wall of at least 3 ft with a hallway
          or another room. No room may be cut off. Leave gaps no wider than ~3 ft
          (so the auto-hallways can link everything) or make rooms flush.
        - Keep ALL the rules above satisfied even when the client only asks to
          change one thing — a change must not break the rest of the plan.

        # Honour the client's described positions and adjacencies as closely as
        # the hard rules allow.

        # OUTPUT FORMAT — output ONLY this one line, nothing else:
        # ROOMS: [("Living","living",x0,y0,x1,y1), ("Kitchen","kitchen",x0,y0,x1,y1), ("Bedroom 1","bedroom",...), ("Bedroom 2","bedroom",...), ("Bedroom 3","bedroom",...), ("Bath 1","bathroom",...), ("Bath 2","bathroom",...)]
        Use literal numbers (x_min,y_min,x_max,y_max). kinds ∈ living/kitchen/bedroom/bathroom.
        You MAY also add "corridor" rooms for halls if you want, but it is optional.
        """).strip()


def _user(request, current_rooms, feedback) -> str:
    parts = []
    if current_rooms:
        cur = ", ".join(f'("{r.name}","{r.kind}",{r.x_min:.0f},{r.y_min:.0f},{r.x_max:.0f},{r.y_max:.0f})'
                        for r in current_rooms if r.kind != "corridor")
        parts.append(f"Current layout (modify it to satisfy the new request, keep the rest):\n# ROOMS: [{cur}]")
    parts.append(f"Client request:\n{request}")
    if feedback:
        parts.append(f"Your previous attempt FAILED these checks — fix them:\n{feedback}")
    parts.append("Output only the corrected `# ROOMS:` line.")
    return "\n\n".join(parts)


def _strip(code: str) -> str:
    code = (code or "").strip()
    if code.startswith("```"):
        code = code.split("\n", 1)[1] if "\n" in code else code
        code = code.rsplit("```", 1)[0]
    return code.strip()


def _generate_groq(footprint, door, request, current_rooms, feedback) -> str:
    from groq import Groq
    key = os.environ.get("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY not set — add it to .env to use the chat designer.")
    client = Groq(api_key=key)
    resp = client.chat.completions.create(
        model=GROQ_MODEL, temperature=0.3,
        messages=[{"role": "system", "content": _system(footprint, door)},
                  {"role": "user", "content": _user(request, current_rooms, feedback)}])
    return _strip(resp.choices[0].message.content)


def _generate_gemini(footprint, door, request, current_rooms, feedback) -> str:
    from google import genai
    from google.genai import types
    from google.genai import errors as genai_errors
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    client = genai.Client(api_key=key, http_options=types.HttpOptions(timeout=60_000))
    cfg = types.GenerateContentConfig(
        system_instruction=_system(footprint, door), temperature=0.3,
        thinking_config=types.ThinkingConfig(thinking_budget=0))
    last = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = client.models.generate_content(
                model=MODEL, contents=_user(request, current_rooms, feedback), config=cfg)
            return _strip(resp.text)
        except genai_errors.APIError as e:
            status = getattr(e, "code", None) or getattr(e, "status_code", None)
            if status in (429, 503) and attempt < MAX_RETRIES:
                time.sleep(2 ** attempt); last = e; continue
            raise
    raise RuntimeError(f"Gemini unavailable: {last}")


def _generate(footprint, door, request, current_rooms, feedback) -> str:
    if PROVIDER == "gemini":
        return _generate_gemini(footprint, door, request, current_rooms, feedback)
    return _generate_groq(footprint, door, request, current_rooms, feedback)


def _fallback_layout(footprint, door) -> InteriorLayout:
    """Deterministic, no-API balanced layout (used when the LLM is unavailable)."""
    import templates
    return templates.build(footprint, door, "Balanced")


def _fb(viol) -> str:
    return "\n".join(f"- {v.message}" for v in viol[:8])


def design(footprint, door, request, current_layout=None, max_iters: int = 3) -> dict:
    """Return {layout, ok, violations, reply, attempts}."""
    current_rooms = list(current_layout.rooms) if current_layout else None
    feedback = None
    best = None  # (n_violations, layout, violations)
    for it in range(1, max_iters + 1):
        try:
            code = _generate(footprint, door, request, current_rooms, feedback)
        except Exception as e:                       # quota / network / any LLM error
            if best is not None:                     # we already have a decent attempt
                break
            msg = str(e)
            quota = "429" in msg or "RESOURCE_EXHAUSTED" in msg or "rate" in msg.lower()
            note = ("⚠️ The AI designer is rate-limited right now, so here's a balanced, "
                    "fully Z3-verified default layout. Try your wording again in a moment."
                    if quota else
                    f"⚠️ The AI designer is unavailable ({msg[:80]}). Showing a verified default.")
            return {"layout": _fallback_layout(footprint, door), "ok": True,
                    "violations": [], "reply": note, "attempts": it - 1}
        try:
            rooms = list(interior_parser.parse(code))
        except interior_parser.InteriorParseError as e:
            feedback = f"PARSE ERROR: {e}. Re-emit the single `# ROOMS:` line with 7 rooms."
            continue
        halls = interior_fill.fill_gaps(footprint, rooms)
        layout = InteriorLayout(footprint=footprint, door=door, rooms=tuple(rooms + halls))
        viol = check_interior(layout, SBC, mode="freeform", require_full_coverage=True)
        if best is None or len(viol) < best[0]:
            best = (len(viol), layout, viol)
        if not viol:
            return {"layout": layout, "ok": True, "violations": [],
                    "reply": _summary(layout, ok=True), "attempts": it}
        feedback = _fb(viol)
        current_rooms = rooms  # iterate on the latest attempt

    if best is None:
        return {"layout": current_layout, "ok": False, "violations": [],
                "reply": "I couldn't turn that into a valid plan — could you rephrase "
                         "or be a bit more specific about where each room goes?",
                "attempts": max_iters}
    _, layout, viol = best
    return {"layout": layout, "ok": False, "violations": viol,
            "reply": _summary(layout, ok=False, viol=viol), "attempts": max_iters}


def _summary(layout, ok: bool, viol=None) -> str:
    rooms = [r for r in layout.rooms if r.kind != "corridor"]
    halls = [r for r in layout.rooms if r.kind == "corridor"]
    fill = sum(r.area for r in layout.rooms) / layout.footprint_area
    line = ", ".join(f"{r.name} {r.area:.0f} sq ft" for r in rooms)
    head = ("Here's your layout — " if ok else
            "I placed it as close to your description as the building rules allow — ")
    tail = (f" Filled the rest with {len(halls)} hall(s) ({fill*100:.0f}% used). "
            "Z3: all core rules pass. ✅" if ok else
            f" But Z3 still flags: {', '.join(sorted({v.rule for v in (viol or [])}))}. "
            "Tell me how to adjust.")
    return head + line + "." + tail


if __name__ == "__main__":
    fp = (5.0, 20.0, 68.0, 78.0)
    door = (40.0, 20.0)
    req = ("Bedrooms in the bottom-left, top-left and top-right. Kitchen between the "
           "top-left and top-right bedrooms. Living room in the bottom middle across "
           "the door. Bathrooms on the left-middle and right-middle.")
    out = design(fp, door, req)
    print("attempts:", out["attempts"], "| ok:", out["ok"])
    print(out["reply"])
    for r in out["layout"].rooms:
        print(f"  {r.name:10s} {r.kind:9s} ({r.x_min:.0f},{r.y_min:.0f})-({r.x_max:.0f},{r.y_max:.0f})  {r.area:.0f} sq ft")
