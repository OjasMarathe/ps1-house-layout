"""Residential WINDOW code as deterministic, city-parameterisable constraints.

This is the HARD, shift-left constraint set for windows — the rules a generator
must satisfy by construction and the verifier proves. It is deliberately separate
from the *soft* daylight quality score (the Livability / Window Agent): compliance
is deterministic and provable here; "how nice is the light" stays a score there.

Every value cites its International Residential Code (IRC) section so the rules are
defensible and auditable. Values tagged (city) vary by jurisdiction and can be
overridden by the Constraint Engine ruleset — this is the coordination point with
the Constraint Engine (Harshit) and Floor Plan (Prasad).

Units: feet (IRC is imperial; the tool converts metres->feet upstream).
"""

# --- Egress — IRC R310 (emergency escape & rescue) ------------------------
EGRESS_ROOM_TYPES = {"bedroom", "master_bedroom"}   # every sleeping room (R310.1)
EGRESS_MIN_CLEAR_SQFT = 5.7        # R310.2.1 net clear opening (5.0 at grade-floor)
EGRESS_MIN_HEIGHT_FT = 24 / 12     # R310.2.1 net clear height >= 24 in
EGRESS_MIN_WIDTH_FT = 20 / 12      # R310.2.1 net clear width  >= 20 in
EGRESS_MAX_SILL_FT = 44 / 12       # R310.2.2 sill <= 44 in above the floor   (city)

# --- Natural light & ventilation — IRC R303.1 -----------------------------
HABITABLE = {"living_room", "kitchen", "bedroom", "master_bedroom", "dining",
             "study", "family_room"}
NAT_LIGHT_MIN_FRAC = 0.08          # glazing area >= 8% of floor area
NAT_VENT_MIN_FRAC = 0.04           # openable area >= 4% of floor area

# --- Safety glazing / tempered — IRC R308.4 -------------------------------
WET_ROOMS = {"bathroom", "master_bathroom"}         # R308.4.5 glazing in wet areas
TEMPERED_BELOW_SILL_FT = 18 / 12   # R308.4.3 bottom edge < 18 in => hazardous   (city)
SAFETY_PANE_SQFT = 9.0             # R308.4.3 pane > 9 sq ft (paired with the sill test)

# windows that actually open (needed to count for ventilation + egress)
OPENABLE_TYPES = {"sliding", "casement", "openable", "single_hung",
                  "double_hung", "awning", "hopper"}
FIXED_TYPES = {"fixed", "picture"}


def params_from_ruleset(constraints: dict | None) -> dict:
    """Pull any window overrides the Constraint Engine ships (else IRC defaults).
    Looks under ruleset['windows'] and a couple of exterior keys."""
    p = {
        "egress_min_clear_sqft": EGRESS_MIN_CLEAR_SQFT,
        "egress_max_sill_ft": EGRESS_MAX_SILL_FT,
        "nat_light_min_frac": NAT_LIGHT_MIN_FRAC,
        "nat_vent_min_frac": NAT_VENT_MIN_FRAC,
        "tempered_below_sill_ft": TEMPERED_BELOW_SILL_FT,
    }
    if not constraints:
        return p
    w = constraints.get("windows", {}) or {}
    for k in list(p):
        if k in w and w[k] is not None:
            p[k] = float(w[k])
    return p
