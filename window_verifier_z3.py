"""Deterministic Z3 verifier for WINDOW code compliance (the shift-left layer).

Given a set of windows + the rooms they serve, it PROVES the hard IRC rules:
egress, natural light, natural ventilation, and safety (tempered) glazing. Every
numeric comparison goes through verifier_z3._violated, so verdicts are
deterministic proofs — the same input always gives the same result, and the same
rules can be handed to the generator as constraints (correct-by-construction)
instead of being discovered by a slow generate->verify->fail loop.

Window record (feet):
  {"room": <room id>, "type": <window type>, "width_ft":, "height_ft":,
   "sill_height_ft":, "operable_type": "sliding"|"casement"|"fixed"|...,
   "tempered": bool, "adjacent_to_door": bool,
   "egress_clear_sqft": <optional net clear opening, else width*height>}
Room record (feet):
  {"id"/"name":, "type":, "floor_area_sqft":}
"""
from dataclasses import dataclass

from verifier_z3 import _violated
import window_rules as R


@dataclass(frozen=True)
class WindowViolation:
    rule: str
    measured: float
    required: float
    message: str


def _area(w) -> float:
    return float(w.get("area_sqft", float(w.get("width_ft", 0)) * float(w.get("height_ft", 0))))


def _openable(w) -> bool:
    return bool(w.get("openable")) or w.get("operable_type") in R.OPENABLE_TYPES


def _egress_ok(w, min_clear, max_sill) -> bool:
    clear = float(w.get("egress_clear_sqft", _area(w)))
    return (clear >= min_clear
            and float(w.get("height_ft", 0)) >= R.EGRESS_MIN_HEIGHT_FT
            and float(w.get("width_ft", 0)) >= R.EGRESS_MIN_WIDTH_FT
            and float(w.get("sill_height_ft", 99)) <= max_sill
            and _openable(w))


def check_windows(windows, rooms, params=None) -> list:
    """Return a list of WindowViolation; empty == code-compliant windows."""
    p = params or R.params_from_ruleset(None)
    egr_area = p["egress_min_clear_sqft"]; egr_sill = p["egress_max_sill_ft"]
    light_f = p["nat_light_min_frac"];     vent_f = p["nat_vent_min_frac"]
    temp_sill = p["tempered_below_sill_ft"]

    by_room = {}
    for w in windows:
        by_room.setdefault(w.get("room"), []).append(w)

    v = []
    for room in rooms:
        rid = room.get("id", room.get("name"))
        rtype = room.get("type")
        area = float(room.get("floor_area_sqft", room.get("area_sqft", 0)))
        wins = by_room.get(rid, [])

        # 1) egress — every sleeping room needs one operable escape window (R310)
        if rtype in R.EGRESS_ROOM_TYPES:
            if not any(_egress_ok(w, egr_area, egr_sill) for w in wins):
                v.append(WindowViolation("egress_window", 0.0, 1.0,
                    f"{rid} ({rtype}) has no compliant egress window "
                    f"(need >= {egr_area} sq ft clear, >= 24 in H, >= 20 in W, sill <= "
                    f"{egr_sill*12:.0f} in, operable) — IRC R310."))

        # 2) natural light + ventilation — habitable rooms (R303.1)
        if rtype in R.HABITABLE and area > 0:
            glaze = sum(_area(w) for w in wins)
            if _violated(glaze, light_f * area):
                v.append(WindowViolation("natural_light", round(glaze, 2), round(light_f * area, 2),
                    f"{rid} ({rtype}) glazing {glaze:.1f} sq ft < {light_f*100:.0f}% of floor "
                    f"({light_f*area:.1f} sq ft) — IRC R303.1."))
            openable = sum(_area(w) for w in wins if _openable(w))
            if _violated(openable, vent_f * area):
                v.append(WindowViolation("natural_ventilation", round(openable, 2), round(vent_f * area, 2),
                    f"{rid} ({rtype}) openable {openable:.1f} sq ft < {vent_f*100:.0f}% of floor "
                    f"({vent_f*area:.1f} sq ft) — IRC R303.1."))

        # 3) safety glazing — hazardous locations must be tempered (R308.4)
        for w in wins:
            sill = float(w.get("sill_height_ft", 3.0))
            hazardous = (sill < temp_sill) or (rtype in R.WET_ROOMS) or bool(w.get("adjacent_to_door"))
            if hazardous and not bool(w.get("tempered", False)):
                why = ("sill %.0f in < %.0f in" % (sill * 12, temp_sill * 12) if sill < temp_sill
                       else "wet room" if rtype in R.WET_ROOMS else "adjacent to a door")
                v.append(WindowViolation("safety_glazing", 0.0, 1.0,
                    f"{rid}: window ({why}) is a hazardous location and must be tempered / "
                    f"safety glazing — IRC R308.4."))
    return v
