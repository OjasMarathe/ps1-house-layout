#!/usr/bin/env bash
# ------------------------------------------------------------------------------
# Z3 Verifier — live demo.  One command:   bash demo.sh
# Owner: Ojas.  Shows the deterministic judge that gates Site Plan + Floor Plan.
# ------------------------------------------------------------------------------
cd "$(dirname "$0")"
PY=.venv/bin/python
bar(){ printf '\n\033[1m============================================================\n %s\n============================================================\033[0m\n' "$1"; }

bar "1.  Cities the verifier knows  (config-driven JSON, not hardcoded code)"
$PY verifier_tool.py cities

bar "2.  OPTIMIZE mode  -  provable MAX buildable area per city"
echo "    Same Z3 code, different code-book -> different legal max:"
$PY verifier_tool.py optimize --city seattle
$PY verifier_tool.py optimize --city bellevue

bar "3.  VERIFY a LEGAL layout (Seattle)  -  every constraint proven PASS"
$PY verifier_tool.py verify --city seattle

bar "4.  VERIFY an ILLEGAL layout  -  rejected, with measured-vs-required reasons"
echo "    (these reasons are the feedback the Site Plan Generator retries on)"
$PY verifier_tool.py verify --city seattle --layout demo/bad_house.json

bar "5.  FLOAT TOLERANCE  -  no false failures from rounding noise"
$PY - <<'PYEOF'
from verifier_tool import verify_site
ok = lambda r: next(c for c in r["constraints"] if c["rule"]=="front_setback_south")["pass"]
near = {"corners":[[5,20-5e-7],[75,20-5e-7],[75,78],[5,78]], "door":[40,20-5e-7]}
far  = {"corners":[[5,19.99],[75,19.99],[75,78],[5,78]],     "door":[40,19.99]}
print("    off by 5e-7 ft :", "PASS" if ok(verify_site(near,"seattle")) else "FAIL", " (within tolerance -> ignored)")
print("    off by 0.01 ft :", "PASS" if ok(verify_site(far ,"seattle")) else "FAIL", " (real violation -> caught)")
PYEOF

bar "6.  INTERIOR  -  same engine, IRC room rules (Floor Plan gate)"
$PY - <<'PYEOF'
import json, dataclasses
from templates import build
from interior_verifier_z3 import Room
fp=(0,0,65,58); door=(32,0)
lay=build(fp, door, "Balanced")
rooms=[[getattr(r,f.name) for f in dataclasses.fields(Room)] for r in lay.rooms]
json.dump({"footprint":list(fp),"door":list(door),"rooms":rooms}, open("demo/interior_ok.json","w"))
PYEOF
$PY verifier_tool.py interior --city seattle --layout demo/interior_ok.json --json \
  | $PY -c "import sys,json; d=json.load(sys.stdin); print(f\"    interior ok={d['ok']}  failures={d['n_failed']}  solve={d['solve_time_s']}s\")"

bar "Done  -  every check above ran in well under the 5s budget"
