"""FastAPI serving layer for the house-design pipeline (PS1 exterior + PS2 interior).

This is the process that runs *inside the container / Kubernetes pod*. It wraps the
deterministic pipeline (Z3 optimize -> template generate -> Z3 verify) behind a
small HTTP API, so the cluster can run many replicas of it and load-balance/scale
queries across them.

Endpoints:
  GET  /health              liveness/readiness probe target
  GET  /cities              jurisdictions the verifier knows
  GET  /optimize?city=...   provable max buildable area (PS1)
  POST /verify              check an exterior footprint  {city, corners, door}
  POST /generate            full run: optimize + tile interior + verify (PS1+PS2)
  POST /roof                generate + Z3-verify a roof plan  {levels, roof_spec, daylight}

Run locally:   uvicorn serve_app:app --host 0.0.0.0 --port 8000
In the pod:    same command (see Dockerfile CMD).
"""
import base64
import os
import threading
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import artifacts                         # optional S3 pull of citycodes/*.json
artifacts.sync_city_codes()              # must run BEFORE codeloader reads them

from codeloader import available_cities
from verifier_tool import optimize_area, verify_site, verify_interior
from roof_tool import roof_plan
import templates

app = FastAPI(title="House-Design Pipeline", version="1.0",
              description="Neuro-symbolic CAD: Z3-verified exterior + interior layouts.")

# Canonical footprint that tiles + verifies cleanly; callers may override.
DEFAULT_FOOTPRINT = (5.0, 20.0, 68.0, 78.0)

# Z3 is NOT thread-safe. FastAPI runs sync endpoints in a threadpool, so without
# this lock concurrent requests call the solver from multiple threads at once and
# segfault the whole pod (observed: "ASSERTION VIOLATION ast.cpp", exit 139).
# We serialize all solver work inside one pod; throughput then scales by running
# MORE PODS (Kubernetes HPA), not more threads. That's the whole point of the
# horizontal-scaling design.
Z3_LOCK = threading.Lock()


class VerifyReq(BaseModel):
    city: str = "seattle"
    corners: list           # [[x,y] x4]
    door: list              # [x, y]


class GenerateReq(BaseModel):
    city: str = "seattle"
    vibe: str = "Balanced"          # Balanced | Family home | Entertainer | Work from home
    footprint: Optional[list] = None  # [x0,y0,x1,y1]; default canonical


class RoofReq(BaseModel):
    levels: list                        # [{level, name, top_height_ft, footprint:[[x,y]…], rooms?}]
    roof_spec: Optional[dict] = None    # {type, pitch, overhang_ft}
    daylight: Optional[dict] = None     # {rooms:[{id, daylight_score}]} from the Window Agent
    constraints: Optional[dict] = None  # per-city ruleset (exterior block)
    session_id: Optional[str] = None
    emit_dxf: bool = False              # also write output/roof_plan.dxf
    emit_svg: bool = False              # also write output/roof_plan.svg


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/cities")
def cities():
    return {"cities": available_cities()}


@app.get("/optimize")
def optimize(city: str = "seattle"):
    try:
        with Z3_LOCK:
            return optimize_area(city)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/verify")
def verify(req: VerifyReq):
    try:
        with Z3_LOCK:
            return verify_site({"corners": req.corners, "door": req.door}, req.city)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/generate")
def generate(req: GenerateReq):
    """End-to-end: max buildable area (PS1) + a tiled, Z3-verified interior (PS2)."""
    t0 = time.perf_counter()
    try:
        with Z3_LOCK:                       # serialize all solver work (see note above)
            opt = optimize_area(req.city)
            fp = tuple(req.footprint) if req.footprint else DEFAULT_FOOTPRINT
            door = ((fp[0] + fp[2]) / 2, fp[1])
            lay = templates.build(fp, door, req.vibe)
            rooms = [[r.name, r.kind, r.x_min, r.y_min, r.x_max, r.y_max] for r in lay.rooms]
            inter = verify_interior(
                {"footprint": list(fp), "door": list(door), "rooms": rooms}, req.city)
        return {
            "city": req.city,
            "vibe": req.vibe,
            "exterior": {
                "max_buildable_area_sqft": opt["max_buildable_area_sqft"],
                "optimal_corners": opt["optimal_corners"],
            },
            "interior": {
                "footprint": list(fp),
                "door": list(door),
                "rooms": rooms,
                "verified": inter["ok"],
                "violations": inter.get("violations", []),
            },
            "took_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _inline_artifacts(roof: dict):
    """Embed the written CAD/SVG files into the response as base64, so REMOTE callers
    actually RECEIVE the drawing. A pod-local file path is useless across the network,
    and unreliable behind a multi-pod load balancer (a later GET could hit a different
    pod). Read inside the Z3 lock so a concurrent request can't overwrite the file
    before we read it."""
    inlined = {}
    for kind, path in (roof.get("artifacts") or {}).items():
        try:
            with open(path, "rb") as f:
                data = f.read()
            inlined[kind] = {"filename": os.path.basename(path),
                             "media_type": "image/vnd.dxf" if kind == "dxf" else "image/svg+xml",
                             "encoding": "base64", "bytes": len(data),
                             "content": base64.b64encode(data).decode("ascii")}
        except Exception:
            inlined[kind] = {"path": path}
    if inlined:
        roof["artifacts"] = inlined
    return roof


@app.post("/roof")
def roof(body: dict):
    """Generate + Z3-verify a roof plan AND emit CAD. Accepts EITHER shape:
      • the team canonical envelope (has `entities`/`envelope_polygon`) -> canonical
        output envelope (geometry as entities, rule results as constraints);
      • the native payload (`levels`, `roof_spec`, `daylight`) -> native roof JSON.
    A DXF (CAD) is produced BY DEFAULT and returned inline as base64 under
    `artifacts.dxf` (set `emit_dxf:false` to skip); `emit_svg:true` adds the sheet."""
    try:
        os.makedirs("output", exist_ok=True)
        want_dxf = body.get("emit_dxf", True)          # CAD on by default (per sir)
        emit_dxf = "output/roof_plan.dxf" if want_dxf else None
        emit_svg = "output/roof_plan.svg" if body.get("emit_svg") else None
        canonical = ("entities" in body or "envelope_polygon" in body) and "levels" not in body
        with Z3_LOCK:                                   # serialize solver + artifact read
            if canonical:
                from pipeline_io import envelope_to_payload
                payload = envelope_to_payload(body)
            else:
                payload = {"levels": body.get("levels"), "roof_spec": body.get("roof_spec") or {},
                           "daylight": body.get("daylight"), "constraints": body.get("constraints"),
                           "session_id": body.get("session_id")}
            out = roof_plan(payload, emit_dxf=emit_dxf, emit_svg=emit_svg)
            _inline_artifacts(out)
        if canonical:
            from pipeline_io import roof_to_envelope
            return roof_to_envelope(out, body)
        return out
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
