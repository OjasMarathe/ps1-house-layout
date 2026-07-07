"""Attic roof VENTILATION calculation — IRC R806.2 (deterministic).

This reproduces the "ROOF VENTILATION" table on a real roof-layout sheet: given a
roof section's area and eave length, it computes the required Net Free Ventilating
Area (NFA), splits it half at the eaves (intake) and half in the upper roof
(exhaust), and sizes the birdblocking (l.f.) and the number of 7"x7" roof jacks.

Rule (IRC R806.2): NFA >= roof area / 300 when the vents are balanced
(>= 40% and <= 50% in the upper third, remainder at the eaves); else / 150.
Areas are worked in square INCHES (x 144 s.i. per s.f.), exactly like the sheet.

Verified against a real sheet: main roof 2306 s.f. -> 1106.9 s.i. req'd,
16 x 7"x7" jacks, 156.7 l.f. birdblocking.
"""
import math

JACK_NFA_SQIN = 36.75          # one 7"x7" attic roof jack, less 25% screen reduction
BIRDBLOCK_NFA_PER_LF = 3.53    # eave birdblocking, s.i. per l.f., less 25% reduction
DEFAULT_RATIO = 300            # 1/300 (balanced eave + ridge); use 150 if unbalanced


def slope_factor(pitch_ratio: float) -> float:
    """Sloped roof area is larger than the flat footprint by sqrt(1 + slope^2)."""
    return math.sqrt(1.0 + pitch_ratio * pitch_ratio)


def ventilation(roof_area_sqft: float, eave_length_ft: float, ratio: int = DEFAULT_RATIO) -> dict:
    req = roof_area_sqft * 144.0 / ratio
    eave_req = req / 2.0
    upper_req = req / 2.0
    jacks = int(math.ceil(upper_req / JACK_NFA_SQIN))
    eave_lf_req = eave_req / BIRDBLOCK_NFA_PER_LF
    eave_lf = max(float(eave_length_ft or 0.0), eave_lf_req)
    provided = jacks * JACK_NFA_SQIN + eave_lf * BIRDBLOCK_NFA_PER_LF
    return {
        "code": "IRC R806.2",
        "rule": f"1/{ratio} (balanced eave + upper)",
        "roof_area_sqft": round(roof_area_sqft, 1),
        "nfa_required_sqin": round(req, 1),
        "eave_required_sqin": round(eave_req, 1),
        "upper_required_sqin": round(upper_req, 1),
        "roof_jacks_7x7": jacks,
        "eave_birdblock_lf": round(eave_lf, 1),
        "nfa_provided_sqin": round(provided, 1),
        "ok": provided >= req - 1e-6,
    }
