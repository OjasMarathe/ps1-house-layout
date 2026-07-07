"""Conversation / planning logic for the design studio UI (no Streamlit dep).

Pure functions that turn a user's choices and free-text into the `params` dict
that interior_milp.solve_layout consumes, plus the progressive option
suggestions that drive the conversation. Keeping this here makes app.py thin
and lets the logic be unit-tested.
"""
from __future__ import annotations
import copy
import re

import interior_milp


# --- vibe presets: a starting brief ---------------------------------------- #
# Each preset is an override on top of default_params(footprint).
VIBES: dict[str, dict] = {
    "Family home":        {"_bed": +3, "_living": -2},                 # roomy bedrooms
    "Entertainer":        {"_living": +4, "_kitchen": +3, "_bed": -1}, # big public space
    "Work from home":     {"_bed": +2, "_public": +2},                 # a study-sized bedroom
    "Balanced":           {},                                          # the defaults
}

# What the user says matters most -> a nudge.
PRIORITIES: dict[str, dict] = {
    "Spacious bedrooms":  {"_bed": +3},
    "Big living room":    {"_living": +4},
    "Large kitchen":      {"_kitchen": +4},
    "Lots of open space": {"_bed": -2, "_living": -2, "_kitchen": -2},
}

# Refinement chips: label -> list of (param, delta).
REFINE: dict[str, list[tuple[str, float]]] = {
    "Bigger bedrooms":  [("bed_depth", +2)],
    "Smaller bedrooms": [("bed_depth", -2)],
    "Bigger living":    [("living_w", +3)],
    "Smaller living":   [("living_w", -3)],
    "Bigger kitchen":   [("kitchen_w", +3)],
    "Smaller kitchen":  [("kitchen_w", -3)],
    "Bigger bathrooms": [("bath_w", +1), ("bath_depth", +1)],
    "More open space":  [("living_w", -2), ("kitchen_w", -2), ("bed_depth", -2)],
    "More compact":     [("living_w", +2), ("kitchen_w", +2), ("bed_depth", +2)],
    "Deeper living/kitchen": [("public_depth", +2)],
}

# Keyword → refine key, split by direction.
_BIG = ("big", "bigger", "large", "larger", "more", "spacious", "roomy", "expand", "grow")
_SMALL = ("small", "smaller", "less", "cozy", "cosy", "tiny", "shrink", "reduce", "compact")
_TOPIC = {
    "bedroom": "bedrooms", "bed": "bedrooms", "bedrooms": "bedrooms",
    "living": "living", "lounge": "living", "hall": "living",
    "kitchen": "kitchen",
    "bath": "bathrooms", "bathroom": "bathrooms", "washroom": "bathrooms",
    "open": "open", "space": "open", "flex": "open",
}


def _apply_deltas(params: dict, deltas: list[tuple[str, float]]) -> dict:
    p = copy.deepcopy(params)
    for key, d in deltas:
        if key.startswith("_"):
            continue
        p[key] = float(p.get(key, 0)) + d
    return p


def apply_meta(params: dict, meta: dict) -> dict:
    """Apply a preset/priority described in the meta shorthand (_bed/_living/…)."""
    p = copy.deepcopy(params)
    mapping = {
        "_bed": [("bed_depth", 2.0)],
        "_living": [("living_w", 2.0)],
        "_kitchen": [("kitchen_w", 2.0)],
        "_public": [("public_depth", 1.0)],
    }
    for k, mult in meta.items():
        for key, unit in mapping.get(k, []):
            p[key] = float(p.get(key, 0)) + unit * mult
    return p


def apply_refine(params: dict, label: str) -> dict:
    return _apply_deltas(params, REFINE.get(label, []))


def parse_message(text: str, params: dict) -> tuple[dict, list[str]]:
    """Map free text to param changes. Returns (new_params, human notes).

    The text is split into clauses on 'and' / punctuation so each clause keeps
    its own direction — e.g. "smaller kitchen and bigger bedrooms" works."""
    notes: list[str] = []
    p = copy.deepcopy(params)
    for clause in re.split(r"\band\b|[,;.]", text.lower()):
        direction = +1 if any(w in clause for w in _BIG) else (-1 if any(w in clause for w in _SMALL) else 0)
        if direction == 0:
            continue
        topics = {v for k, v in _TOPIC.items() if k in clause}
        for topic in topics:
            if topic == "bedrooms":
                p["bed_depth"] = p["bed_depth"] + 2 * direction
                notes.append(f"{'larger' if direction>0 else 'smaller'} bedrooms")
            elif topic == "living":
                p["living_w"] = p["living_w"] + 3 * direction
                notes.append(f"{'larger' if direction>0 else 'smaller'} living room")
            elif topic == "kitchen":
                p["kitchen_w"] = p["kitchen_w"] + 3 * direction
                notes.append(f"{'larger' if direction>0 else 'smaller'} kitchen")
            elif topic == "bathrooms":
                p["bath_w"] = p["bath_w"] + 1 * direction
                p["bath_depth"] = p["bath_depth"] + 1 * direction
                notes.append(f"{'larger' if direction>0 else 'smaller'} bathrooms")
            elif topic == "open":
                s = -direction  # "more open" => shrink rooms
                p["living_w"] = p["living_w"] + 2 * s
                p["kitchen_w"] = p["kitchen_w"] + 2 * s
                p["bed_depth"] = p["bed_depth"] + 2 * s
                notes.append("more open space" if direction > 0 else "less open space")
    return p, notes


def suggest(params: dict, areas: dict | None = None) -> list[str]:
    """Context-aware next options the user can click (sir's progressive flow)."""
    opts = ["Bigger bedrooms", "Bigger living", "Bigger kitchen", "More open space", "More compact"]
    if areas:
        # surface the most useful nudge first
        if areas.get("kitchen", 0) > areas.get("living", 0):
            opts.insert(0, "Smaller kitchen")
        if areas.get("bedroom", 0) < 0.6 * areas.get("living", 1):
            opts.insert(0, "Bigger bedrooms")
    # de-dupe, keep order, cap at 6
    seen, out = set(), []
    for o in opts:
        if o not in seen:
            seen.add(o); out.append(o)
    return out[:6]


def brief_text(params: dict) -> str:
    """A short human description of the current requirements."""
    p = params
    return (f"Living {p['living_w']:.0f} ft wide · Kitchen {p['kitchen_w']:.0f} ft · "
            f"public depth {p['public_depth']:.0f} ft · bedrooms {p['bed_depth']:.0f} ft deep · "
            f"baths {p['bath_w']:.0f}×{p['bath_depth']:.0f} ft")
