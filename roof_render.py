"""Roof plan -> a professional ROOF LAYOUT sheet (SVG), styled like a real
construction document: title block, north arrow, scale, legend, eave overhang,
ridge/hip labels, pitch callouts, roof-jack vents, skylight tags, and the IRC
ventilation table drawn on the sheet. Pure-python SVG (no matplotlib).
"""
import os
import math

from roof_agent import _bbox

_DIR = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}
INK = "#1A1D29"; AMBER = "#E0922F"; RED = "#C0392B"; TEAL = "#1C7293"; BLUE = "#1F6FEB"; MUT = "#6A7186"


def _centroid(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _arrow(x1, y1, x2, y2, color, w=1.8):
    """A line with an explicitly-drawn arrowhead (LibreOffice ignores SVG markers)."""
    ang = math.atan2(y2 - y1, x2 - x1); a = 9
    h1x, h1y = x2 - a * math.cos(ang - 0.45), y2 - a * math.sin(ang - 0.45)
    h2x, h2y = x2 - a * math.cos(ang + 0.45), y2 - a * math.sin(ang + 0.45)
    return (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{color}" stroke-width="{w}"/>'
            f'<line x1="{x2:.1f}" y1="{y2:.1f}" x2="{h1x:.1f}" y2="{h1y:.1f}" stroke="{color}" stroke-width="{w}"/>'
            f'<line x1="{x2:.1f}" y1="{y2:.1f}" x2="{h2x:.1f}" y2="{h2y:.1f}" stroke="{color}" stroke-width="{w}"/>')


def render_roof(roof, path="output/roof_plan.svg", title="ROOF LAYOUT",
                project="GENERATED RESIDENCE", sheet="R-1", scale='1/4" = 1\'-0"'):
    secs = roof["roof_sections"]
    pts = [p for s in secs for p in s.get("eave_outline", s["outline"])]
    minx = min(p[0] for p in pts); maxx = max(p[0] for p in pts)
    miny = min(p[1] for p in pts); maxy = max(p[1] for p in pts)

    SW, SH = 1500, 1000
    dax0, day0, dax1, day1 = 410, 130, 1180, 910          # main drawing area
    sc = min((dax1 - dax0) / max(maxx - minx, 1e-6), (day1 - day0) / max(maxy - miny, 1e-6))
    ox = dax0 + ((dax1 - dax0) - (maxx - minx) * sc) / 2
    oy = day0 + ((day1 - day0) - (maxy - miny) * sc) / 2

    def tx(x): return ox + (x - minx) * sc
    def ty(y): return oy + (maxy - y) * sc                # flip (north up)

    def poly_pts(pl): return " ".join(f"{tx(p[0]):.1f},{ty(p[1]):.1f}" for p in pl)

    e = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SW}" height="{SH}" '
         f'viewBox="0 0 {SW} {SH}" font-family="Helvetica,Arial,sans-serif">',
         f'<rect width="{SW}" height="{SH}" fill="#FFFFFF"/>',
         f'<rect x="12" y="12" width="{SW-24}" height="{SH-24}" fill="none" stroke="{INK}" stroke-width="2.5"/>',
         f'<rect x="20" y="20" width="{SW-40}" height="{SH-40}" fill="none" stroke="{INK}" stroke-width="0.7"/>',
         '<defs><marker id="ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" '
         f'orient="auto-start-reverse"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{BLUE}" stroke-width="1.6"/>'
         '</marker></defs>']

    # --- title (top-left of drawing area) ---
    e.append(f'<text x="{dax0}" y="70" font-size="26" font-weight="bold" fill="{INK}">{title}</text>')
    e.append(f'<text x="{dax0}" y="94" font-size="13" fill="{MUT}">SCALE: {scale}</text>')

    # --- the roof plan ---
    for s in secs:
        # eave overhang line (dashed) + O.H. dims
        if s.get("eave_outline"):
            e.append(f'<polygon points="{poly_pts(s["eave_outline"])}" fill="none" stroke="{INK}" '
                     f'stroke-width="1.3" stroke-dasharray="8,5"/>')
            ex0, ey0, ex1, ey1 = _bbox(s["eave_outline"])
            e.append(f'<text x="{tx((ex0+ex1)/2):.0f}" y="{ty(ey1)-4:.0f}" font-size="9" fill="{MUT}" '
                     f'text-anchor="middle">{s.get("eave_overhang_ft",1.5):.1f} ft O.H.</text>')
        out = s["outline"]
        e.append(f'<polygon points="{poly_pts(out)}" fill="#EAF1F6" stroke="{INK}" stroke-width="2"/>')
        # ridge + label
        if s.get("ridge"):
            (a, b) = s["ridge"][0], s["ridge"][1]
            e.append(f'<line x1="{tx(a[0]):.1f}" y1="{ty(a[1]):.1f}" x2="{tx(b[0]):.1f}" y2="{ty(b[1]):.1f}" '
                     f'stroke="{RED}" stroke-width="3"/>')
            mx, my = (a[0]+b[0])/2, (a[1]+b[1])/2
            e.append(f'<text x="{tx(mx):.0f}" y="{ty(my)-4:.0f}" font-size="9" fill="{RED}" '
                     f'text-anchor="middle" font-weight="bold">RIDGE</text>')
        # hips
        for h in s.get("hips", []):
            e.append(f'<line x1="{tx(h[0][0]):.1f}" y1="{ty(h[0][1]):.1f}" x2="{tx(h[1][0]):.1f}" '
                     f'y2="{ty(h[1][1]):.1f}" stroke="{TEAL}" stroke-width="1.3" stroke-dasharray="5,4"/>')
        if s.get("hips"):
            hm = s["hips"][0]
            e.append(f'<text x="{tx((hm[0][0]+hm[1][0])/2):.0f}" y="{ty((hm[0][1]+hm[1][1])/2):.0f}" '
                     f'font-size="8" fill="{TEAL}">HIP</text>')
        # pitch arrows + callouts per plane
        x0, y0, x1, y1 = _bbox(out)
        L = 0.16 * min(x1 - x0, y1 - y0)
        for pl in s.get("planes", []):
            cx, cy = _centroid(pl["polygon"]); dx, dy = _DIR[pl["drains_to"]]
            e.append(_arrow(tx(cx), ty(cy), tx(cx + dx * L), ty(cy + dy * L), BLUE, 2.0))
            e.append(f'<text x="{tx(cx):.0f}" y="{ty(cy)+13:.0f}" font-size="9" fill="{BLUE}" '
                     f'text-anchor="middle">{s["pitch"].replace(":", chr(34)+"/")}"</text>')
        # roof-jack vents (small squares) — a row near the ridge
        n = s.get("ventilation", {}).get("roof_jacks_7x7", 0)
        if n:
            ncol = min(n, 12)
            gy = y0 + (y1 - y0) * 0.62
            for i in range(ncol):
                gx = x0 + (x1 - x0) * (0.22 + 0.56 * (i / max(ncol - 1, 1)))
                e.append(f'<rect x="{tx(gx)-4:.1f}" y="{ty(gy)-4:.1f}" width="8" height="8" '
                         f'fill="#FFFFFF" stroke="{INK}" stroke-width="1.3"/>')
            e.append(f'<text x="{tx((x0+x1)/2):.0f}" y="{ty(gy)+16:.0f}" font-size="8.5" fill="{INK}" '
                     f'text-anchor="middle">{n} x 7"x7" roof jacks</text>')
        # skylights
        for sk in s.get("skylights", []):
            so = sk["outline"]
            e.append(f'<polygon points="{poly_pts(so)}" fill="#FCE9A6" stroke="{AMBER}" stroke-width="1.6"/>')
            scx, scy = sk["center"]
            e.append(f'<text x="{tx(scx):.0f}" y="{ty(scy)-6:.0f}" font-size="8.5" fill="#B26A00" '
                     f'text-anchor="middle">SKYLIGHT {sk["width_ft"]:.0f}\'x{sk["length_ft"]:.0f}\'</text>')
        # section name
        e.append(f'<text x="{tx(x0)+4:.0f}" y="{ty(y1)+15:.0f}" font-size="10" fill="{INK}" '
                 f'font-weight="bold">{s["name"].upper()} - {s["type"].upper()}</text>')

    # --- left panel: ventilation table(s) ---
    py = 130
    for s in secs[:2]:
        v = s["ventilation"]
        e.append(f'<rect x="30" y="{py}" width="360" height="150" fill="none" stroke="{INK}" stroke-width="1"/>')
        e.append(f'<rect x="30" y="{py}" width="360" height="22" fill="{INK}"/>')
        e.append(f'<text x="40" y="{py+16}" font-size="12" fill="#FFFFFF" font-weight="bold">'
                 f'ROOF VENTILATION - {s["name"].upper()}</text>')
        lines = [f'Roof area: {v["roof_area_sqft"]} s.f.   ({v["code"]})',
                 f'Required NFA = area x 144 / 300 = {v["nfa_required_sqin"]} s.i.',
                 f'  eave (intake):  {v["eave_required_sqin"]} s.i.',
                 f'  upper (exhaust): {v["upper_required_sqin"]} s.i.',
                 f'Provide: {v["eave_birdblock_lf"]} l.f. birdblocking (eave)',
                 f'Provide: {v["roof_jacks_7x7"]} x 7"x7" roof jacks (upper)',
                 f'Provided = {v["nfa_provided_sqin"]} s.i.   >= required  {"OK" if v["ok"] else "SHORT"}']
        for i, t in enumerate(lines):
            col = "1AA06D" if ("OK" in t) else INK
            e.append(f'<text x="40" y="{py+40+i*15}" font-size="10" fill="{col}" '
                     f'font-family="Consolas,monospace">{t}</text>')
        py += 168

    # --- legend ---
    ly = py + 6
    e.append(f'<rect x="30" y="{ly}" width="360" height="120" fill="none" stroke="{INK}" stroke-width="1"/>')
    e.append(f'<text x="40" y="{ly+18}" font-size="11" font-weight="bold" fill="{INK}">LEGEND</text>')
    leg = [(RED, "solid", "RIDGE"), (TEAL, "dash", "HIP"), (MUT, "dash", "EAVE / O.H. line"),
           (BLUE, "arrow", "slope + pitch (rise/12)")]
    for i, (c, kind, lab) in enumerate(leg):
        yy = ly + 36 + i * 18
        if kind == "arrow":
            e.append(_arrow(46, yy, 76, yy, c, 1.8))
        else:
            da = 'stroke-dasharray="5,4"' if kind == "dash" else ""
            e.append(f'<line x1="46" y1="{yy}" x2="76" y2="{yy}" stroke="{c}" stroke-width="2.5" {da}/>')
        e.append(f'<text x="84" y="{yy+4}" font-size="10" fill="{INK}">{lab}</text>')
    e.append(f'<rect x="46" y="{ly+100}" width="8" height="8" fill="#FCE9A6" stroke="{AMBER}"/>')
    e.append(f'<text x="60" y="{ly+108}" font-size="10" fill="{INK}">SKYLIGHT   </text>')
    e.append(f'<rect x="160" y="{ly+100}" width="8" height="8" fill="none" stroke="{INK}"/>')
    e.append(f'<text x="174" y="{ly+108}" font-size="10" fill="{INK}">7"x7" roof jack</text>')

    # --- north arrow (bottom-left) ---
    nx, ny = 70, SH - 70
    e.append(_arrow(nx, ny + 22, nx, ny - 22, INK, 2.2))
    e.append(f'<text x="{nx}" y="{ny-28}" font-size="12" fill="{INK}" text-anchor="middle" font-weight="bold">N</text>')

    # --- title block (right strip) ---
    tbx = SW - 250
    e.append(f'<rect x="{tbx}" y="20" width="230" height="{SH-40}" fill="none" stroke="{INK}" stroke-width="1"/>')
    sched = roof.get("schedule", {})
    rows = [("PROJECT", project), ("SHEET TITLE", "ROOF LAYOUT"), ("SHEET NO.", sheet),
            ("SCALE", scale), ("GENERATED BY", "Roof Plan Agent"),
            ("ROOF TYPES", ", ".join(sched.get("roof_types", []))),
            ("TOTAL AREA", f'{sched.get("total_roof_area_sqft","-")} s.f.'),
            ("ROOF JACKS", str(sched.get("ventilation", {}).get("total_roof_jacks_7x7", "-"))),
            ("EAVE VENT", f'{sched.get("ventilation", {}).get("total_eave_birdblock_lf","-")} l.f.'),
            ("SKYLIGHTS", str(len(sched.get("skylights", [])))),
            ("ATTIC ACCESS", "22\"x30\" min"),
            ("VERIFIED", "YES" if roof.get("verified") else "NO")]
    yy = 60
    for k, val in rows:
        e.append(f'<text x="{tbx+14}" y="{yy}" font-size="9" fill="{MUT}">{k}</text>')
        e.append(f'<text x="{tbx+14}" y="{yy+16}" font-size="11" fill="{INK}" font-weight="bold">{val}</text>')
        e.append(f'<line x1="{tbx}" y1="{yy+26}" x2="{tbx+230}" y2="{yy+26}" stroke="#DDE1EB" stroke-width="0.6"/>')
        yy += 40

    e.append("</svg>")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(e))
    return path
