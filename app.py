"""Layout Studio — a conversational, human-in-the-loop floor-plan designer.

    streamlit run app.py

You describe the home in plain words; Gemini places the rooms, leftover space
becomes distributed halls, and Z3 proves every core rule. After each message the
studio offers fresh options so your brief gets progressively sharper — sir's
"ChatGPT for architectural sites" idea.
"""
import re
from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from constraints import SBC
from plot import PLOT
from verifier_z3 import HouseGeometry
from interior_verifier_z3 import InteriorLayout, check_interior
import interior_milp
import interior_fill
import interior_render
import dxf_full
import studio_agent
import templates

load_dotenv(Path(__file__).parent / ".env")   # explicit: cwd may not be the repo

FOOTPRINT = (5.0, 20.0, 68.0, 78.0)
DOOR = (40.0, 20.0)
OUT = Path(__file__).parent / "output"
PNG = OUT / "slides" / "studio_layout.png"
DXF = OUT / "studio_layout.dxf"

NAVY, TEAL, ICE, INK, MUTED = "#1E2761", "#0E7490", "#CADCFC", "#0F172A", "#64748B"

# Deterministic, always-valid quick changes (label -> templates.adjust action).
CHIPS = [
    ("Bigger bedrooms", "beds"),
    ("Bigger living", "living"),
    ("Bigger kitchen", "kitchen"),
    ("Bigger bathrooms", "baths"),
    ("Reset to even", "even"),
]

st.set_page_config(page_title="Layout Studio", page_icon="🏠", layout="wide",
                   initial_sidebar_state="collapsed")

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
html, body, [class*="css"] {{ font-family: 'Inter', sans-serif; }}
.stApp {{ background:
   radial-gradient(1200px 500px at 12% -10%, #EEF3FF 0%, rgba(238,243,255,0) 60%),
   radial-gradient(1000px 500px at 100% 0%, #E7F7FA 0%, rgba(231,247,250,0) 55%), #F7F9FC; }}
#MainMenu, footer, header {{ visibility: hidden; }}
.block-container {{ padding-top: 1.4rem; padding-bottom: 2rem; max-width: 1400px; }}
.hero {{ background: linear-gradient(105deg, {NAVY} 0%, #2B3A86 55%, {TEAL} 130%);
   border-radius: 20px; padding: 26px 32px; color: #fff; box-shadow: 0 18px 40px -20px rgba(30,39,97,.55); }}
.hero h1 {{ font-family:'Fraunces',serif; font-size: 2.15rem; margin: 0; font-weight: 700; letter-spacing:-.5px; }}
.hero p {{ margin: 6px 0 0; color: {ICE}; font-size: 1.02rem; }}
.hero .pills span {{ display:inline-block; margin-top:12px; margin-right:8px; padding:4px 12px;
   border:1px solid rgba(202,220,252,.5); border-radius:999px; font-size:.78rem; color:#EAF1FF; }}
.sec {{ font-size:.74rem; font-weight:700; letter-spacing:.12em; color:{TEAL}; text-transform:uppercase; margin-bottom:6px; }}
.badge-ok {{ background:#ECFDF5; color:#047857; border:1px solid #6EE7B7; border-radius:999px;
   padding:7px 14px; font-weight:600; font-size:.92rem; display:inline-block; }}
.badge-bad {{ background:#FEF2F2; color:#B91C1C; border:1px solid #FCA5A5; border-radius:999px;
   padding:7px 14px; font-weight:600; font-size:.92rem; display:inline-block; }}
.stButton > button {{ border-radius:999px; border:1.5px solid {TEAL}; background:#fff; color:{NAVY};
   font-weight:600; padding:.34rem .9rem; transition:all .12s ease; }}
.stButton > button:hover {{ background:{TEAL}; color:#fff; border-color:{TEAL}; }}
.statwrap {{ display:flex; gap:10px; flex-wrap:wrap; }}
.stat {{ background:#fff; border:1px solid #E6ECF5; border-radius:12px; padding:10px 14px; min-width:96px; }}
.stat b {{ font-family:'Fraunces',serif; font-size:1.25rem; color:{NAVY}; display:block; }}
.stat span {{ font-size:.7rem; color:{MUTED}; text-transform:uppercase; letter-spacing:.06em; }}
.vibe button {{ width:100%; height:118px; border-radius:18px !important; border:1.5px solid #DCE6F5 !important;
   background:#fff !important; color:{NAVY} !important; font-size:1.02rem !important; font-weight:600 !important; }}
.vibe button:hover {{ border-color:{TEAL} !important; box-shadow:0 12px 26px -18px rgba(14,116,144,.7); }}
.chatwrap {{ display:flex; flex-direction:column; gap:9px; margin:4px 0 10px; }}
.abub {{ align-self:flex-start; max-width:92%; background:#EEF3FF; border:1px solid #DCE6F8;
   color:{NAVY}; padding:9px 13px; border-radius:14px 14px 14px 4px; font-size:.9rem; line-height:1.45; }}
.ubub {{ align-self:flex-end; max-width:92%; background:{NAVY}; color:#fff;
   padding:9px 13px; border-radius:14px 14px 4px 14px; font-size:.9rem; line-height:1.45; }}
.who {{ display:block; font-size:.6rem; text-transform:uppercase; letter-spacing:.09em; opacity:.6; margin-bottom:2px; }}
.welcome-h {{ font-family:'Fraunces',serif; font-size:1.5rem; color:{NAVY}; font-weight:700; margin:8px 0 2px; }}
</style>""", unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
#  Backend helpers
# --------------------------------------------------------------------------- #
def seed_layout(params) -> InteriorLayout:
    """Fast deterministic starting layout (MILP) + gap-fill to ~100%."""
    p = interior_milp.safe_params(FOOTPRINT, DOOR, params, SBC)
    res = interior_milp.solve_layout(FOOTPRINT, DOOR, SBC, params=p)
    halls = interior_fill.fill_gaps(FOOTPRINT, list(res.layout.rooms))
    return InteriorLayout(FOOTPRINT, DOOR, tuple(list(res.layout.rooms) + halls))


def verify(layout):
    return check_interior(layout, SBC, mode="freeform", require_full_coverage=True)


def fill_frac(layout):
    return sum(r.area for r in layout.rooms) / layout.footprint_area


def run_design(request: str):
    """Ask the AI to redesign per the request; commit ONLY if Z3 fully passes."""
    st.session_state.history.append({"role": "user", "content": request})
    with st.spinner("Designing the layout, then proving it with Z3…"):
        out = studio_agent.design(FOOTPRINT, DOOR, request,
                                  current_layout=st.session_state.layout, max_iters=4)
    if out["ok"] and out["layout"] is not None:
        st.session_state.layout = out["layout"]
        reply = out["reply"]
    else:
        rules = ", ".join(sorted({v.rule for v in out.get("violations", [])})) or "a building rule"
        reply = (f"I couldn't make that change without breaking **{rules}**, so I kept your "
                 "current layout. Try a smaller or differently-worded change.")
    st.session_state.history.append({"role": "assistant", "content": reply})
    st.rerun()


# --------------------------------------------------------------------------- #
#  State
# --------------------------------------------------------------------------- #
if "stage" not in st.session_state:
    st.session_state.stage = "welcome"
    st.session_state.layout = None
    st.session_state.cuts = None
    st.session_state.history = []

# --------------------------------------------------------------------------- #
#  Hero
# --------------------------------------------------------------------------- #
st.markdown(f"""
<div class="hero">
  <h1>🏠 Layout Studio</h1>
  <p>Describe your home in plain words — an AI architect places the rooms and Z3 proves every building rule.</p>
  <div class="pills"><span>AI · conversational design</span><span>Z3 · verified</span>
  <span>Human-in-the-loop</span><span>Plot 63 × 58 ft · Seattle</span></div>
</div>
""", unsafe_allow_html=True)
st.write("")

# --------------------------------------------------------------------------- #
#  Welcome
# --------------------------------------------------------------------------- #
if st.session_state.stage == "welcome":
    st.markdown('<div class="welcome-h">Let\'s plan your home — what\'s the vibe?</div>',
                unsafe_allow_html=True)
    st.caption("Pick a starting point, then describe changes in your own words.")
    cols = st.columns(4)
    icons = {"Family home": "👨‍👩‍👧", "Entertainer": "🥂", "Work from home": "💻", "Balanced": "⚖️"}
    blurb = {"Family home": "Roomy bedrooms", "Entertainer": "Big living + kitchen",
             "Work from home": "A study-sized bedroom", "Balanced": "Even all round"}
    import studio_logic as S
    for col, vibe in zip(cols, S.VIBES):
        with col:
            st.markdown('<div class="vibe">', unsafe_allow_html=True)
            if st.button(f"{icons[vibe]}\n\n{vibe}\n\n{blurb[vibe]}", key=f"vibe_{vibe}", use_container_width=True):
                st.session_state.cuts = dict(templates.VIBE_CUTS[vibe])
                st.session_state.layout = templates.build_cuts(FOOTPRINT, DOOR, st.session_state.cuts)
                st.session_state.stage = "studio"
                st.session_state.history = [{"role": "assistant",
                    "content": f"Here's a starting plan for a **{vibe.lower()}**. Now just tell me "
                               "what to change — e.g. *“put the kitchen between the two top bedrooms.”*"}]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    st.stop()

# --------------------------------------------------------------------------- #
#  Studio
# --------------------------------------------------------------------------- #
layout = st.session_state.layout
viol = verify(layout)
interior_render.render(layout, PNG, title="Your floor plan", fill_frac=fill_frac(layout))
house = HouseGeometry(
    corners=((FOOTPRINT[0], FOOTPRINT[1]), (FOOTPRINT[2], FOOTPRINT[1]),
             (FOOTPRINT[2], FOOTPRINT[3]), (FOOTPRINT[0], FOOTPRINT[3])), door=DOOR)
dxf_full.emit_full_dxf(house, layout, PLOT, DXF)

left, right = st.columns([0.42, 0.58], gap="large")

with left:
    st.markdown('<div class="sec">Design conversation</div>', unsafe_allow_html=True)
    bubbles = ""
    for m in st.session_state.history[-8:]:
        txt = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", m["content"])
        txt = re.sub(r"\*(.+?)\*", r"<i>\1</i>", txt)
        cls = "ubub" if m["role"] == "user" else "abub"
        who = "You" if m["role"] == "user" else "Studio"
        bubbles += f'<div class="{cls}"><span class="who">{who}</span>{txt}</div>'
    st.markdown(f'<div class="chatwrap">{bubbles}</div>', unsafe_allow_html=True)

    st.markdown('<div class="sec" style="margin-top:12px">Quick changes — instant &amp; always valid</div>',
                unsafe_allow_html=True)
    for row in (CHIPS[:3], CHIPS[3:]):
        ccols = st.columns(len(row))
        for c, (label, action) in zip(ccols, row):
            with c:
                if st.button(label, key=f"chip_{label}", use_container_width=True):
                    st.session_state.cuts = templates.adjust(st.session_state.cuts, action)
                    st.session_state.layout = templates.build_cuts(FOOTPRINT, DOOR, st.session_state.cuts)
                    st.session_state.history.append({"role": "user", "content": label})
                    st.session_state.history.append({"role": "assistant", "content": f"Done — {label.lower()}."})
                    st.rerun()

    with st.form("chat", clear_on_submit=True):
        msg = st.text_input("Describe your layout",
                            placeholder="e.g. bedrooms in the three corners, kitchen up top, bathrooms on the sides",
                            label_visibility="collapsed")
        sent = st.form_submit_button("Send  ➤", use_container_width=True)
    if sent and msg.strip():
        run_design(msg.strip())

    if st.button("↺ Start over", key="reset"):
        st.session_state.stage = "welcome"
        st.session_state.layout = None
        st.session_state.cuts = None
        st.session_state.history = []
        st.rerun()

with right:
    st.image(str(PNG), use_container_width=True)
    if viol:
        rules = ", ".join(sorted({v.rule for v in viol}))
        st.markdown(f'<span class="badge-bad">✗ Z3 flags: {rules}</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="badge-ok">✓ Z3-verified · all core rules satisfied</span>',
                    unsafe_allow_html=True)

    rooms = {r.name: r for r in layout.rooms}
    def area_of(name): return rooms[name].area if name in rooms else 0
    stats = [
        ("Living", f"{area_of('Living'):.0f}", "sq ft"),
        ("Kitchen", f"{area_of('Kitchen'):.0f}", "sq ft"),
        ("Bedroom 1", f"{area_of('Bedroom 1'):.0f}", "sq ft"),
        ("Bathroom", f"{area_of('Bath 1'):.0f}", "sq ft"),
        ("Used", f"{fill_frac(layout)*100:.0f}%", "of plot"),
    ]
    html = '<div class="statwrap">' + "".join(
        f'<div class="stat"><b>{v}</b><span>{lab} · {u}</span></div>' for lab, v, u in stats) + "</div>"
    st.markdown(html, unsafe_allow_html=True)
    st.write("")
    with open(DXF, "rb") as f:
        st.download_button("⤓  Download CAD file (.dxf)", f, file_name="floor_plan.dxf",
                           mime="application/dxf", use_container_width=True)
    st.caption("Opens in any CAD viewer (AutoCAD, LibreCAD, the Autodesk web viewer).")
