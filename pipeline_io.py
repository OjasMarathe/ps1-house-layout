"""Adapter between the team's canonical pipeline envelope and the roof agent.

The pipeline speaks one shape for every agent:
  { session_id, callback_url, stage, jurisdiction, total_lot_area_sqft,
    envelope_polygon, interior_rules, entities:[{id,type,polygon,area_sqft,…}],
    constraints:[{id,type,severity,params}] }

This module maps that envelope -> the roof agent's internal payload, and the roof
output -> the same envelope style (entities + constraints results). It is deliberately
TOLERANT: entity `type` strings differ between agents, so we classify by SHAPE
(has a daylight_score? -> room; otherwise a polygon -> footprint) and fall back to
envelope_polygon when no footprint entity is present. Unknown fields are ignored.
"""


def _num(v, default=None):
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def envelope_to_payload(env: dict) -> dict:
    """Canonical envelope -> roof_plan payload {levels, roof_spec, daylight, constraints}."""
    footprints, room_ents = [], []
    for e in (env.get("entities") or []):
        poly = e.get("polygon")
        t = (e.get("type") or "").lower()
        ds = e.get("daylight_score")
        if ds is None:
            ds = (e.get("params") or {}).get("daylight_score")
        is_room = ("room" in t) or (ds is not None and "footprint" not in t and "floor" not in t)
        if is_room and poly:
            room_ents.append({"name": e.get("id") or e.get("name"),
                              "daylight_score": ds, "polygon": poly})
            continue
        if ds is not None and not poly:            # daylight-only score, no geometry
            room_ents.append({"name": e.get("id") or e.get("name"), "daylight_score": ds})
            continue
        if not poly:
            continue
        lvl = {"level": e.get("level", len(footprints) + 1),
               "name": e.get("id") or e.get("name") or f"level_{len(footprints)+1}",
               "top_height_ft": _num(e.get("top_height_ft"), 0.0),
               "footprint": poly}
        if e.get("rooms"):
            lvl["rooms"] = e["rooms"]
        if e.get("roof_spec"):
            lvl["roof_spec"] = e["roof_spec"]
        footprints.append(lvl)

    if not footprints and env.get("envelope_polygon"):     # fallback: one level from envelope
        footprints = [{"level": 1, "name": "main", "top_height_ft": 0.0,
                       "footprint": env["envelope_polygon"]}]

    # attach room polygons (with scores) to the top level so skylights can be placed
    if room_ents and footprints:
        top = max(footprints, key=lambda l: l.get("top_height_ft", 0) or 0)
        top.setdefault("rooms", [])
        for r in room_ents:
            if r.get("polygon"):
                top["rooms"].append({"name": r["name"], "type": "room",
                                     "daylight_score": r["daylight_score"], "polygon": r["polygon"]})

    # roof_spec + exterior building-code numbers from constraints[] (or a passthrough)
    roof_spec = dict(env.get("roof_spec") or {})
    ext = {}
    for c in (env.get("constraints") or []):
        t = (c.get("type") or c.get("id") or "").lower()
        p = c.get("params") or {}
        val = p.get("value")
        if "pitch" in t:
            roof_spec.setdefault("pitch", p.get("pitch") or val)
        elif "roof_type" in t or t == "type":
            roof_spec.setdefault("type", p.get("roof_type") or val)
        elif "overhang" in t:
            roof_spec.setdefault("overhang_ft", _num(p.get("overhang_ft") or val))
        elif "height" in t:
            ext["max_building_height_ft"] = _num(p.get("max_building_height_ft") or val)
        elif "coverage" in t:
            ext["max_lot_coverage_fraction"] = _num(p.get("fraction") or val)

    return {"session_id": env.get("session_id"), "levels": footprints,
            "roof_spec": roof_spec,
            "daylight": {"rooms": [{"id": r["name"], "daylight_score": r["daylight_score"]}
                                   for r in room_ents]} if room_ents else None,
            "constraints": {"exterior": ext} if ext else None}


def roof_to_envelope(roof: dict, env: dict) -> dict:
    """Roof output -> canonical envelope style: geometry as entities, rule results as
    constraints (only failures are listed; empty list == fully verified)."""
    entities = []
    for s in roof.get("roof_sections", []):
        nm = s.get("name")
        entities.append({"id": f"section_{nm}", "type": "roof_section", "subtype": s.get("type"),
                         "polygon": s.get("outline"), "area_sqft": s.get("roof_area_sqft"),
                         "pitch": s.get("pitch"), "ridge": s.get("ridge"), "hips": s.get("hips"),
                         "eave_height_ft": s.get("eave_height_ft"),
                         "ridge_height_ft": s.get("ridge_height_ft")})
        for p in s.get("planes", []):
            entities.append({"id": f"plane_{nm}_{p.get('id')}", "type": "roof_plane",
                             "polygon": p.get("polygon"), "drains_to": p.get("drains_to"),
                             "azimuth_deg": p.get("azimuth_deg")})
        for sk in (s.get("skylights") or []):
            entities.append({"id": f"skylight_{sk.get('room')}", "type": "skylight",
                             "polygon": sk.get("outline"), "on_plane": sk.get("on_plane"),
                             "room": sk.get("room")})
    constraints = [{"id": v["rule"], "type": v["rule"], "severity": "hard", "status": "fail",
                    "measured": v["measured"], "required": v["required"], "message": v["message"]}
                   for v in roof.get("violations", [])]
    return {"session_id": roof.get("session_id"),
            "stage": env.get("stage") or "roof_plan",
            "jurisdiction": env.get("jurisdiction"),
            "view_type": "roof",
            "status": "verified" if roof.get("verified") else "violations",
            "verified": roof.get("verified"), "n_failed": roof.get("n_failed", 0),
            "entities": entities, "constraints": constraints,
            "schedule": roof.get("schedule"),
            "elevation_profiles": roof.get("elevation_profiles"),
            "artifacts": roof.get("artifacts")}
