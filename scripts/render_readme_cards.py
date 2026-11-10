#!/usr/bin/env python3
"""
Render the profile README's cards as animated SVGs into cards/.

Design: paper (#f3f3f1), ink (#111111), and electric-blue / red / yellow accent cards
with Instrument Serif, Geist, and Geist Mono.

Every card is a standalone SVG shown through <img>, so it can only use what GitHub
allows there: inline CSS animations, SMIL and fonts embedded as data URIs (no JS,
no external requests). Fonts are subset WOFFs in fonts/ (SIL OFL).

Live numbers come from data/contributions.json (fetch_contributions.py),
data/stats.json or langs.svg (generate_stats.py), and GitHub's public API.

Run daily by .github/workflows/stats.yml after fetch_contributions.py.
"""
import base64
import datetime
import json
import os
import re
from html import escape

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data", "contributions.json")
STATS_JSON = os.path.join(ROOT, "data", "stats.json")
LANGS_SVG = os.path.join(ROOT, "langs.svg")
OUT = os.path.join(ROOT, "cards")
FONTS = os.path.join(ROOT, "fonts")
ASSETS = os.path.join(ROOT, "assets")
PORTRAIT = os.path.join(ROOT, "manas-ascii.svg")

GH_USER = os.environ.get("GH_PROFILE_USER", os.environ.get("GH_LOGIN", "Manas-5461X"))

# ---- brand tokens -----------------------------------------------------------
PAPER = "#f3f3f1"
PAPER_DEEP = "#e2e2de"
INK = "#111111"
INK_SOFT = "#3a3a3c"
MUTED = "#6e6e73"
RULE = "#dcdcd7"
TECH = "#2f55ff"
STUDIO = "#ef3b2d"
LEARN = "#ffc81a"
W = 880  # full card width, GitHub's README column at 100%

SERIF = "'Instrument Serif', Georgia, serif"
SANS = "Geist, system-ui, -apple-system, sans-serif"
MONO = "'Geist Mono', ui-monospace, SFMono-Regular, Menlo, monospace"

FONT_FILES = {
    "serif": ("Instrument Serif", "normal", 400, "serif-400.woff"),
    "serif-i": ("Instrument Serif", "italic", 400, "serif-italic.woff"),
    "sans": ("Geist", "normal", 400, "geist-400.woff"),
    "sans-b": ("Geist", "normal", 600, "geist-600.woff"),
    "mono": ("Geist Mono", "normal", 400, "geistmono-400.woff"),
}

BASE_CSS = """
@keyframes rise{from{opacity:0;transform:translateY(16px)}to{opacity:1;transform:none}}
@keyframes fade{from{opacity:0}to{opacity:1}}
@keyframes grow{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes growx{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.15)}100%{opacity:1;transform:none}}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}
@keyframes spark{0%,100%{opacity:.78}45%{opacity:.38}50%{opacity:.95}75%{opacity:.5}}
@keyframes nudge{0%,100%{transform:none}50%{transform:translateX(4px)}}
@keyframes nudgeup{0%,100%{transform:none}50%{transform:translate(3px,-3px)}}
.r{opacity:0;animation:rise .8s cubic-bezier(.2,.7,.2,1) both;transform-box:fill-box}
.f{opacity:0;animation:fade .9s ease-out both}
.g{transform-box:fill-box;transform-origin:bottom;transform:scaleY(0);animation:grow .8s cubic-bezier(.2,.7,.2,1) both}
.gx{transform-box:fill-box;transform-origin:left;transform:scaleX(0);animation:growx .8s cubic-bezier(.2,.7,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .4s ease-out both}
.live{animation:pulse 1.6s ease-in-out infinite}
.sp{animation:spark 2.4s ease-in-out infinite}
.n{transform-box:fill-box;animation:nudge 1.8s ease-in-out infinite}
.nu{transform-box:fill-box;animation:nudgeup 1.8s ease-in-out infinite}
@keyframes tilein{0%{opacity:0;transform:translateY(90px) scale(.6) rotate(-9deg)}55%{opacity:1;transform:translateY(-10px) scale(1.05) rotate(2deg)}75%{transform:translateY(3px) scale(.98) rotate(-.8deg)}90%{transform:translateY(-1px) scale(1.01) rotate(.2deg)}100%{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-26px)}to{opacity:1;transform:none}}
@keyframes arrowin{0%{opacity:0;transform:translateX(-30px)}60%{opacity:1;transform:translateX(6px)}100%{opacity:1;transform:none}}
@keyframes roll{from{transform:translateY(60px)}to{transform:none}}
@keyframes sheen{0%{transform:translateX(-260px) skewX(-20deg)}22%,100%{transform:translateX(420px) skewX(-20deg)}}
@keyframes ring{0%{opacity:.7;transform:scale(.2)}100%{opacity:0;transform:scale(2.4)}}
.ti{opacity:0;transform-box:fill-box;transform-origin:50% 60%;animation:tilein 1.1s cubic-bezier(.2,.8,.2,1) both}
.sl{opacity:0;transform-box:fill-box;animation:slidein .6s cubic-bezier(.2,.7,.2,1) both}
.ai{opacity:0;transform-box:fill-box;animation:arrowin .7s cubic-bezier(.2,.7,.2,1) both}
.ro{transform-box:fill-box;animation:roll .8s cubic-bezier(.15,.8,.2,1) both}
.sh{animation:sheen 5s ease-in-out infinite}
.rg{opacity:0;transform-box:fill-box;transform-origin:center;animation:ring 1s ease-out both}
@media (prefers-reduced-motion: reduce){.r,.f,.g,.gx,.p,.live,.sp,.n,.nu,.ti,.sl,.ai,.ro,.rg{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}}
"""


def font_face(keys):
    out = []
    for k in keys:
        fam, style, weight, fn = FONT_FILES[k]
        with open(os.path.join(FONTS, fn), "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        out.append(
            f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
            f"src:url(data:font/woff;base64,{b64}) format('woff')}}"
        )
    return "".join(out)


def img_uri(filename, mime):
    with open(os.path.join(ASSETS, filename), "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


GAP = 12
BOTTOM = 12
COL = W / 3


def svg(w, h, body, fonts, label, extra_css="", left=0, right=0, bottom=BOTTOM):
    """Card of w x h drawn at x=left inside a transparent canvas, padded so rows tile exactly."""
    if left:
        body = f'<g transform="translate({left:.3f} 0)">{body}</g>'
    w, h = w + left + right, h + bottom
    css = font_face(fonts) + BASE_CSS + extra_css
    if os.environ.get("STATIC"):
        css += ".r,.f,.g,.gx,.p,.live,.sp,.n,.nu,.ti,.sl,.ai,.ro{animation:none!important;opacity:1!important;transform:none!important}.sh,.rg{display:none}"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.3f}" height="{h}" viewBox="0 0 {w:.3f} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{css}</style>{body}</svg>"
    )


def write(name, content):
    os.makedirs(OUT, exist_ok=True)
    path = os.path.join(OUT, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"wrote cards/{name} ({len(content) // 1024} KB)")


def d(s):
    return f'style="animation-delay:{s:.2f}s"'


def wrap(text, n):
    lines, line = [], ""
    for word in text.split():
        if line and len(line) + 1 + len(word) > n:
            lines.append(line)
            line = word
        else:
            line = f"{line} {word}".strip()
    return lines + [line] if line else lines


def text_lines(x, y, lines, lh, attrs):
    return "".join(
        f'<text x="{x}" y="{y + i * lh}" {attrs}>{escape(l)}</text>' for i, l in enumerate(lines)
    )


def pretty_date(iso):
    dt = datetime.date.fromisoformat(iso)
    return f"{dt.strftime('%b')} {dt.day}"


# ---- 1 · hero -----------------------------------------------------------------
def hero():
    h = 420
    with open(PORTRAIT, encoding="utf-8") as f:
        src = f.read()
    rows = re.findall(r'<text xml:space="preserve"[^>]*\by="([\d.]+)"[^>]*>(.*?)</text>', src, re.S)
    portrait = []
    for i, (y, txt) in enumerate(rows):
        portrait.append(
            f'<text class="f" style="animation-delay:{0.25 + i * 0.018:.3f}s;animation-duration:.35s" '
            f'xml:space="preserve" x="20" y="{y}" fill="{INK}" font-size="7.2" '
            f'textLength="800" lengthAdjust="spacing">{txt}</text>'
        )
    s = 0.41
    body = f"""
<defs>
  <linearGradient id="shine" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="600" y2="0">
    <stop offset="0" stop-color="{INK}"/><stop offset=".42" stop-color="{INK}"/>
    <stop offset=".5" stop-color="{TECH}"/><stop offset=".58" stop-color="{INK}"/>
    <stop offset="1" stop-color="{INK}"/>
    <animateTransform attributeName="gradientTransform" type="translate" values="-600 0;600 0;600 0"
      keyTimes="0;.45;1" dur="7s" begin="1.6s" repeatCount="indefinite"/>
  </linearGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0)}>
  <rect class="live" x="48" y="49" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="66" y="57" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">FULL-STACK · APPLIED AI &amp; CYBERSEC</text>
</g>
<text class="r" {d(0.15)} x="44" y="190" font-family="{SERIF}" font-size="116" letter-spacing="-2.5" fill="{INK}">Manas</text>
<text class="r" {d(0.3)} x="44" y="290" font-family="{SERIF}" font-style="italic" font-size="116" letter-spacing="-2.5" fill="url(#shine)">Gandhi</text>
<g class="r" {d(0.55)}>
  {text_lines(48, 338, ["I build full-stack MERN apps, applied AI & RAG", "pipelines, and packet-level security tools."], 27, f'font-family="{SANS}" font-size="18" fill="{INK_SOFT}"')}
</g>
<g class="f" {d(0.8)}>
  <text x="48" y="396" font-family="{MONO}" font-size="13" fill="{INK}">github.com/Manas-5461X</text>
  <text class="nu" x="224" y="396" font-family="{MONO}" font-size="13" fill="{TECH}">&#8599;</text>
</g>
<g transform="translate(520 46) scale({s}) translate(-20 -37)" font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">
  {''.join(portrait)}
</g>
"""
    write(
        "hero.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            "Manas Gandhi. Full-Stack Developer, AI Practitioner & CyberSec Enthusiast.",
        ),
    )


# ---- 1b · about me (white box + custom side illustration) ---------------------
def about():
    h = 398
    about_uri = img_uri("about-dev.png", "image/png")
    p1 = wrap(
        "Hey, I'm Manas Gandhi — a software developer building full-stack MERN "
        "apps, scalable backend services, and applied AI/ML systems from API "
        "and database layers up to responsive UIs.",
        56,
    )
    p2 = wrap(
        "Lately I've been focused on machine learning, RAG pipelines, and "
        "backend engineering with Spring Boot, Node.js, Redis, and PostgreSQL "
        "— alongside core systems and security tools.",
        56,
    )
    bullets = [
        (TECH, "AI & ML:", "Machine learning models, RAG pipelines & intelligent tools."),
        (STUDIO, "MERN & Backend:", "React, Node.js, Spring Boot, Redis & PostgreSQL/Neon."),
        (INK, "DSA & Systems:", "Algorithms in Java & Python, OS & Linux internals."),
        ("#d99b00", "Cyber Security:", "Packet inspection & lightweight security tooling."),
    ]
    y_p1 = 116
    y_p2 = y_p1 + len(p1) * 19 + 12
    y_bul = y_p2 + len(p2) * 19 + 18
    bullet_svg = []
    for i, (col, title, desc) in enumerate(bullets):
        by = y_bul + i * 26
        bullet_svg.append(
            f'<g class="r" {d(0.45 + i * 0.08)}>'
            f'<rect x="44" y="{by - 8}" width="7" height="7" rx="2" fill="{col}"/>'
            f'<text x="60" y="{by}" font-family="{SANS}" font-size="13" fill="{INK_SOFT}">'
            f'<tspan font-weight="600" fill="{INK}">{escape(title)}</tspan> {escape(desc)}</text></g>'
        )

    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0.05)}>
  <rect x="44" y="34" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="62" y="42" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">ABOUT ME</text>
  <text x="836" y="42" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">BENGALURU · SCALER SST</text>
</g>
<text class="r" {d(0.15)} x="42" y="82" font-family="{SERIF}" font-size="36" fill="{INK}">Software builder, <tspan font-style="italic" fill="{TECH}">AI-ML &amp; Backend</tspan> explorer</text>
<g class="r" {d(0.25)}>
  {text_lines(44, y_p1, p1, 19, f'font-family="{SANS}" font-size="13.2" fill="{INK_SOFT}"')}
</g>
<g class="r" {d(0.35)}>
  {text_lines(44, y_p2, p2, 19, f'font-family="{SANS}" font-size="13.2" fill="{INK_SOFT}"')}
</g>
{''.join(bullet_svg)}
<g class="f" {d(0.3)}>
  <image href="{about_uri}" x="554" y="106" width="292" height="214" preserveAspectRatio="xMidYMid meet"/>
  <text x="700" y="352" text-anchor="middle" font-family="{MONO}" font-size="10.5" letter-spacing="0.8" fill="{MUTED}">BITS PILANI CS · SCALER SST (2025–29)</text>
</g>
"""
    write(
        "about.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "sans-b", "mono"],
            "About Manas Gandhi: AI & ML, MERN & Backend, DSA & Systems, Cyber Security.",
        ),
    )


# ---- 1c · tech stack (classified white box + lightning + anime coder) --------
def tech_glyph(key, color):
    """Crisp 16x16 vector icon centered in (0..16, 0..16) for each tech pill."""
    glyphs = {
        "Python": f'<rect x="2" y="2" width="12" height="5" rx="2.5" fill="{color}"/><rect x="2" y="9" width="12" height="5" rx="2.5" fill="#ffc81a"/><circle cx="5" cy="4.5" r="1" fill="#fff"/><circle cx="11" cy="11.5" r="1" fill="#111"/>',
        "TypeScript": f'<rect x="1.5" y="1.5" width="13" height="13" rx="2.5" fill="{color}"/><text x="8" y="11.5" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="8" fill="#fff">TS</text>',
        "JavaScript": f'<rect x="1.5" y="1.5" width="13" height="13" rx="2.5" fill="#f7df1e"/><text x="8" y="11.5" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="8" fill="#111">JS</text>',
        "Java": f'<path d="M5 10h6v2.5a3 3 0 0 1-6 0V10z" fill="{color}"/><path d="M6 3c1.5 1.5-1.5 2.8 0 4.5M10 3c1.5 1.5-1.5 2.8 0 4.5" stroke="#2f55ff" stroke-width="1.3" fill="none" stroke-linecap="round"/>',
        "LangChain": f'<circle cx="5.2" cy="8" r="2.6" fill="none" stroke="{color}" stroke-width="1.6"/><circle cx="10.8" cy="8" r="2.6" fill="none" stroke="{TECH}" stroke-width="1.6"/>',
        "Scikit-learn": f'<circle cx="6.2" cy="8.5" r="4.2" fill="none" stroke="#F7931E" stroke-width="1.8"/><circle cx="10.8" cy="7.2" r="3.2" fill="none" stroke="#3499CD" stroke-width="1.6"/>',
        "Pandas": f'<rect x="3.5" y="2.5" width="2" height="11" rx="1" fill="{color}"/><rect x="7" y="4.5" width="2" height="4.5" rx="1" fill="#E70488"/><rect x="7" y="10.5" width="2" height="3" rx="1" fill="#FFCA00"/><rect x="10.5" y="2.5" width="2" height="11" rx="1" fill="{color}"/>',
        "NumPy": f'<polygon points="8,1.5 13.8,4.8 13.8,11.2 8,14.5 2.2,11.2 2.2,4.8" fill="{color}" fill-opacity="0.16" stroke="{color}" stroke-width="1.4"/><text x="8" y="10.5" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="7.5" fill="{color}">N</text>',
        "React": f'<circle cx="8" cy="8" r="1.7" fill="{color}"/><ellipse cx="8" cy="8" rx="6.5" ry="2.6" fill="none" stroke="{color}" stroke-width="1.1"/><ellipse cx="8" cy="8" rx="6.5" ry="2.6" transform="rotate(60 8 8)" fill="none" stroke="{color}" stroke-width="1.1"/><ellipse cx="8" cy="8" rx="6.5" ry="2.6" transform="rotate(120 8 8)" fill="none" stroke="{color}" stroke-width="1.1"/>',
        "Node.js": f'<polygon points="8,1.5 13.8,4.8 13.8,11.2 8,14.5 2.2,11.2 2.2,4.8" fill="none" stroke="{color}" stroke-width="1.6"/><text x="8" y="10.2" text-anchor="middle" font-family="{MONO}" font-size="6.8" fill="{color}">JS</text>',
        "Express": f'<rect x="1.5" y="1.5" width="13" height="13" rx="3" fill="{color}"/><text x="8" y="11" text-anchor="middle" font-family="{MONO}" font-size="7.2" fill="#fff">EX</text>',
        "Spring Boot": f'<path d="M8 1.8c3.6 0 6.2 2.6 6.2 6.2S11.6 14.2 8 14.2 1.8 11.6 1.8 8 4.4 1.8 8 1.8z" fill="none" stroke="{color}" stroke-width="1.6"/><path d="M5 10.5c2.2 0 4.5-1.8 5.2-5-.9.3-3.5.7-4.8 2.8" fill="none" stroke="{color}" stroke-width="1.4" stroke-linecap="round"/>',
        "MongoDB": f'<path d="M8 1.5C11 5 11.8 8.5 8 13.5C4.2 8.5 5 5 8 1.5Z" fill="{color}"/><line x1="8" y1="7" x2="8" y2="14.8" stroke="{color}" stroke-width="1.2"/>',
        "Tailwind CSS": f'<path d="M2 6.5c1-2 2.4-2.8 4-2.5 2 .4 2.5 2.3 4.2 2.5 1.4.2 2.4-.5 3.4-1.8-1 2-2.4 2.8-4 2.5-2-.4-2.5-2.3-4.2-2.5-1.4-.2-2.4.5-3.4 1.8zm0 4.8c1-2 2.4-2.8 4-2.5 2 .4 2.5 2.3 4.2 2.5 1.4.2 2.4-.5 3.4-1.8-1 2-2.4 2.8-4 2.5-2-.4-2.5-2.3-4.2-2.5-1.4-.2-2.4.5-3.4 1.8z" fill="{color}"/>',
        "HTML5": f'<polygon points="3,2 13,2 12,12.5 8,14 4,12.5" fill="{color}"/><text x="8" y="10.5" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="7.5" fill="#fff">5</text>',
        "CSS3": f'<polygon points="3,2 13,2 12,12.5 8,14 4,12.5" fill="{color}"/><text x="8" y="10.5" text-anchor="middle" font-family="{SANS}" font-weight="600" font-size="7.5" fill="#fff">3</text>',
        "PostgreSQL": f'<circle cx="8" cy="7.5" r="5" fill="none" stroke="{color}" stroke-width="1.6"/><path d="M5 10.5c1.5 2.5 4.5 2.5 6 0" fill="none" stroke="{color}" stroke-width="1.4"/><circle cx="6.3" cy="6.6" r=".8" fill="{color}"/><circle cx="9.7" cy="6.6" r=".8" fill="{color}"/>',
        "Redis": f'<polygon points="8,2 14,5.2 8,8.4 2,5.2" fill="{color}"/><polyline points="2,8.2 8,11.4 14,8.2" fill="none" stroke="{color}" stroke-width="1.4"/><polyline points="2,11 8,14.2 14,11" fill="none" stroke="{color}" stroke-width="1.4"/>',
        "Neon": f'<rect x="2.2" y="2.2" width="11.6" height="11.6" rx="2.5" fill="none" stroke="{color}" stroke-width="1.6"/><polyline points="5,11 5,5 11,11 11,5" fill="none" stroke="{color}" stroke-width="1.5" stroke-linejoin="round" stroke-linecap="round"/>',
        "Supabase": f'<polygon points="9,1.5 3.2,9 8.2,9 7,14.5 12.8,7 7.8,7" fill="{color}"/>',
        "Firebase": f'<polygon points="4,13 5.5,2.5 8.5,7.2 10.8,4.2 12.5,13 8,14.8" fill="{color}"/>',
        "Clerk": f'<circle cx="8" cy="8" r="5.3" fill="none" stroke="{color}" stroke-width="2"/><circle cx="8" cy="8" r="1.8" fill="{color}"/>',
        "Vercel": f'<polygon points="8,2.5 14,13 2,13" fill="{color}"/>',
        "Netlify": f'<polygon points="8,1.5 14.5,8 8,14.5 1.5,8" fill="{color}" fill-opacity="0.18" stroke="{color}" stroke-width="1.4"/><circle cx="8" cy="8" r="2.2" fill="{color}"/>',
        "Docker": f'<rect x="3" y="7" width="10" height="5" rx="1.8" fill="{color}"/><rect x="4" y="4" width="2.4" height="2.2" fill="{color}"/><rect x="7" y="4" width="2.4" height="2.2" fill="{color}"/><rect x="10" y="4" width="2.4" height="2.2" fill="{color}"/>',
        "Linux": f'<rect x="2" y="2.5" width="12" height="11" rx="2" fill="#111"/><text x="8" y="10.5" text-anchor="middle" font-family="{MONO}" font-size="6.8" fill="#ffc81a">&gt;_</text>',
        "Git": f'<circle cx="5" cy="4.2" r="1.6" fill="{color}"/><circle cx="5" cy="11.8" r="1.6" fill="{color}"/><circle cx="11.2" cy="8" r="1.6" fill="{color}"/><path d="M5 5.8v4.4M5 5.8c0 2.2 6.2 0 6.2 2.2" fill="none" stroke="{color}" stroke-width="1.5"/>',
        "GitHub": f'<circle cx="8" cy="8" r="6" fill="{color}"/><circle cx="6.2" cy="7.5" r="1" fill="#fff"/><circle cx="9.8" cy="7.5" r="1" fill="#fff"/><path d="M5.5 10.5c1.5 1.2 3.5 1.2 5 0" stroke="#fff" stroke-width="1.2" fill="none" stroke-linecap="round"/>',
        "Postman": f'<circle cx="8" cy="8" r="5.6" fill="{color}"/><polygon points="5.5,8.2 11,5.2 8.2,10.8 7.5,8.5" fill="#fff"/>',
    }
    return glyphs.get(key, f'<circle cx="8" cy="8" r="5" fill="{color}"/>')


def techstack():
    h = 472
    shinobi_uri = img_uri("tech-shinobi.png", "image/png")
    sections = [
        ("LANGUAGES", 4, [
            ("Python", "#3776AB"),
            ("JavaScript", "#D9A300"),
            ("TypeScript", "#3178C6"),
            ("Java", "#EA8C00"),
        ]),
        ("AI & ML / RAG", 4, [
            ("LangChain", "#1C3C3C"),
            ("Scikit-learn", "#E67E22"),
            ("Pandas", "#150458"),
            ("NumPy", "#013243"),
        ]),
        ("FULL-STACK & BACKEND", 4, [
            ("React", "#0891B2"),
            ("Node.js", "#16A34A"),
            ("Express", "#111111"),
            ("Spring Boot", "#6DB33F"),
            ("MongoDB", "#15803D"),
            ("Tailwind CSS", "#0EA5E9"),
            ("HTML5", "#E34F26"),
            ("CSS3", "#1572B6"),
        ]),
        ("CLOUD, DATABASES & INFRA", 4, [
            ("PostgreSQL", "#336791"),
            ("Redis", "#DC382D"),
            ("Neon", "#00A86B"),
            ("Supabase", "#16A34A"),
            ("Firebase", "#D97706"),
            ("Clerk", "#6C47FF"),
            ("Vercel", "#111111"),
            ("Netlify", "#00A89C"),
        ]),
        ("DEVOPS & TOOLS", 5, [
            ("Docker", "#2496ED"),
            ("Linux", "#B45309"),
            ("Git", "#EF3B2D"),
            ("GitHub", "#181717"),
            ("Postman", "#EA580C"),
        ]),
    ]

    x0, right_x = 286, 844
    grid_w = right_x - x0  # 558px
    cur_y = 98
    cat_svgs = []
    total_tools = sum(len(items) for _, _, items in sections)
    pill_idx = 0

    for sec_title, cols, items in sections:
        cat_svgs.append(
            f'<text class="f" {d(0.2 + pill_idx * 0.015)} x="{x0}" y="{cur_y}" '
            f'font-family="{MONO}" font-size="10" letter-spacing="1.2" fill="{MUTED}">{escape(sec_title)}</text>'
        )
        cur_y += 10
        gx = 9.5
        pw = (grid_w - gx * (cols - 1)) / cols
        ph, gy = 31, 7
        font_sz = "11.2" if cols == 5 else "11.8"
        for i, (name, col) in enumerate(items):
            c, r = i % cols, i // cols
            px = x0 + c * (pw + gx)
            py = cur_y + r * (ph + gy)
            delay = 0.24 + pill_idx * 0.02
            pill_idx += 1
            cat_svgs.append(
                f'<g class="r" {d(delay)}>'
                f'<rect x="{px:.1f}" y="{py}" width="{pw:.1f}" height="{ph}" rx="7.5" '
                f'fill="#ffffff" fill-opacity="0.92" stroke="{col}" stroke-opacity="0.28" stroke-width="1"/>'
                f'<g transform="translate({px + 8:.1f} {py + 7.5})">{tech_glyph(name, col)}</g>'
                f'<text x="{px + 29:.1f}" y="{py + 19.5}" font-family="{SANS}" font-weight="600" '
                f'font-size="{font_sz}" fill="{INK}">{escape(name)}</text>'
                f"</g>"
            )
        rows = (len(items) + cols - 1) // cols
        cur_y += rows * ph + (rows - 1) * gy + 18

    body = f"""
<defs>
  <clipPath id="ts-card"><rect width="{W}" height="{h}" rx="14"/></clipPath>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{TECH}" stop-opacity=".22"/>
    <stop offset=".35" stop-color="{LEARN}" stop-opacity=".14"/>
    <stop offset="1" stop-color="{TECH}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="orb" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="#ffffff" stop-opacity=".95"/>
    <stop offset=".35" stop-color="{TECH}" stop-opacity=".35"/>
    <stop offset=".7" stop-color="{LEARN}" stop-opacity=".18"/>
    <stop offset="1" stop-color="{TECH}" stop-opacity="0"/>
  </radialGradient>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g clip-path="url(#ts-card)">
  <circle cx="195" cy="245" r="155" fill="url(#orb)"/>
  <polygon class="f" {d(0.2)} points="195,245 880,68 880,432" fill="url(#beam)"/>
  <g class="sp" fill="none" stroke-linecap="round" stroke-linejoin="round">
    <polyline points="200,240 266,188 308,200 384,152 454,164 554,116" stroke="{TECH}" stroke-width="1.8" stroke-opacity=".48"/>
    <polyline points="198,246 258,256 318,240 398,262 478,244 584,270" stroke="{LEARN}" stroke-width="1.8" stroke-opacity=".62"/>
    <polyline points="202,252 270,322 336,312 412,356 496,342 608,388" stroke="{TECH}" stroke-width="1.4" stroke-opacity=".36"/>
  </g>
  <image class="sl" {d(0.05)} href="{shinobi_uri}" x="6" y="64" width="262" height="350" preserveAspectRatio="xMidYMid meet"/>
</g>
<g class="f" {d(0.1)}>
  <text x="286" y="37" font-family="{MONO}" font-size="11.5" letter-spacing="1.2" fill="{TECH}">// TECH ARSENAL</text>
  <text x="844" y="37" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">{total_tools} TOOLS MASTERED</text>
</g>
<text class="r" {d(0.18)} x="284" y="75" font-family="{SERIF}" font-size="35" fill="{INK}">Tools I <tspan font-style="italic" fill="{TECH}">build with</tspan></text>
{''.join(cat_svgs)}
"""
    write(
        "techstack.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "sans-b", "mono"],
            f"Manas Gandhi's Classified Tech Stack ({total_tools} tools across Languages, AI & ML/RAG, Full-Stack & Backend, Cloud/DB & DevOps).",
        ),
    )


# ---- 2 · world tiles (achievements) -------------------------------------------
TILE_W, TILE_H = 880 / 3 - 8, 210


def count_up(num, word, x, y, attrs, begin, dur=1.1, frames=18):
    m = re.match(r"([\d.]+)(.*)", num)
    val, suf = float(m.group(1)), m.group(2)
    dec = len(m.group(1).split(".")[1]) if "." in m.group(1) else 0
    tail = f' <tspan font-style="italic">{escape(word)}</tspan>'
    if os.environ.get("STATIC"):
        return f'<text x="{x}" y="{y}" {attrs}>{escape(num)}{tail}</text>'
    out = []
    for i in range(frames + 1):
        e = 1 - (1 - i / frames) ** 3
        txt = num if i == frames else f"{val * e:.{dec}f}{suf}"
        on = begin + dur * i / frames
        off = "" if i == frames else f'<set attributeName="opacity" to="0" begin="{begin + dur * (i + 1) / frames:.3f}s"/>'
        out.append(
            f'<text x="{x}" y="{y}" {attrs} opacity="0">{escape(txt)}{tail}'
            f'<set attributeName="opacity" to="1" begin="{on:.3f}s"/>{off}</text>'
        )
    return "".join(out)


def tile(name, label, color, on, num, word, blurb, delay, pos):
    lines = wrap(blurb, 34)
    blurb_svg = "".join(
        f'<text class="r" {d(delay + 0.75 + i * 0.1)} x="24" y="{150 + i * 20}" font-family="{SANS}" '
        f'font-size="14" fill="{on}" opacity=".92">{escape(l)}</text>'
        for i, l in enumerate(lines)
    )
    body = f"""
<defs>
  <clipPath id="card"><rect width="{TILE_W}" height="{TILE_H}" rx="14"/></clipPath>
  <clipPath id="slot"><rect x="0" y="62" width="{TILE_W}" height="62"/></clipPath>
  <linearGradient id="gl" x1="0" x2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>
    <stop offset=".5" stop-color="#fff" stop-opacity=".35"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
</defs>
<g class="ti" {d(delay)}>
  <g clip-path="url(#card)">
    <rect width="{TILE_W}" height="{TILE_H}" fill="{color}"/>
    <circle class="rg" {d(delay + 0.5)} cx="{TILE_W - 40}" cy="{TILE_H - 40}" r="60" fill="none" stroke="{on}" stroke-opacity=".5" stroke-width="2"/>
    <rect class="sh" style="animation-delay:{delay + 1.4:.2f}s" x="0" y="-20" width="90" height="{TILE_H + 40}" fill="url(#gl)" transform="translate(-260 0)"/>
  </g>
  <text class="sl" {d(delay + 0.35)} x="24" y="38" font-family="{MONO}" font-size="12" letter-spacing="1.2" fill="{on}">{label}</text>
  <g class="ai" {d(delay + 0.5)}><text class="n" style="animation-delay:{delay + 1.3:.2f}s" x="250" y="38" font-family="{MONO}" font-size="14" fill="{on}">&#8594;</text></g>
  <g clip-path="url(#slot)"><g class="ro" {d(delay + 0.45)}>
    {count_up(num, word, 22, 112, f'font-family="{SERIF}" font-size="44" fill="{on}"', delay + 0.45)}
  </g></g>
  {blurb_svg}
</g>
"""
    write(
        f"{name}.svg",
        svg(
            TILE_W,
            TILE_H,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"{label}: {num} {word}. {blurb}",
            left=4 * pos,
            right=8 - 4 * pos,
        ),
    )


# ---- 3 · activity (monthly bars) ------------------------------------------------
def activity(data):
    h = 340
    monthly = data["monthly"][-12:]
    best = max(monthly[:-1] or monthly, key=lambda m: m["total"])
    top = max(best["total"], 1)
    x0, x1, base, maxh, gap = 40, 600, 292, 140, 10
    bw = (x1 - x0 - gap * (len(monthly) - 1)) / len(monthly)
    bars = []
    for i, m in enumerate(monthly):
        partial = i == len(monthly) - 1
        is_best = m is best
        bh = max(4, round(m["total"] / top * maxh))
        x = x0 + i * (bw + gap)
        fill = TECH if is_best else ("#c9c9c4" if partial else INK)
        label = datetime.date.fromisoformat(m["month"] + "-01").strftime("%b")
        bars.append(
            f'<rect class="g" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x:.1f}" y="{base - bh}" '
            f'width="{bw:.1f}" height="{bh}" rx="4" fill="{fill}"><title>{label}: {m["total"]:,}</title></rect>'
            f'<text class="f" style="animation-delay:{2.2 + i * 0.07:.2f}s" x="{x + bw / 2:.1f}" y="{base + 22}" '
            f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{MUTED}">{label}</text>'
        )
        if is_best:
            bars.append(
                f'<text class="p" style="animation-delay:3.2s" x="{x + bw / 2:.1f}" y="{base - bh - 10}" '
                f'text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TECH}">{m["total"]:,}</text>'
            )
    cs = data["current_streak"]["length"]
    ls = data["longest_streak"]["length"]
    streak_note = "current streak, and the longest" if cs >= ls else f"current streak, longest {ls}"
    total_days = len(data["days"])
    stats = [
        (f'{cs} <tspan font-style="italic">days</tspan>', streak_note),
        (f'{data["active_days"]}<tspan fill="#8e8e93"> / {total_days}</tspan>', "days with a commit"),
        (f'{data["best_day"]["count"]}', "on the busiest day"),
    ]
    side = []
    for i, (big, small) in enumerate(stats):
        y = 104 + i * 92
        side.append(
            f'<g class="r" {d(2.6 + i * 0.15)}>'
            f'<text x="650" y="{y}" font-family="{SERIF}" font-size="40" fill="{INK}">{big}</text>'
            f'<text x="650" y="{y + 24}" font-family="{SANS}" font-size="13" fill="{MUTED}">{small}</text></g>'
        )
        if i < 2:
            side.append(f'<rect class="f" {d(2.6)} x="650" y="{y + 44}" width="190" height="1" fill="{RULE}"/>')
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="f" {d(1.9)} x="40" y="58" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">THE LAST 12 MONTHS ON GITHUB</text>
<text class="r" {d(2.0)} x="38" y="114" font-family="{SERIF}" font-size="52" fill="{INK}">{data["total_contributions"]:,} <tspan font-style="italic">contributions</tspan></text>
{''.join(bars)}
{''.join(side)}
"""
    write(
        "activity.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f'{data["total_contributions"]:,} contributions in the last year, {cs}-day streak',
        ),
    )


# ---- 3b · tech journey analytics (white box: streaks + languages + year map) ---
def load_lang_stats():
    """Return (by_size, by_repo) from data/stats.json or fallback to langs.svg."""
    if os.path.exists(STATS_JSON):
        try:
            with open(STATS_JSON, encoding="utf-8") as f:
                st = json.load(f)
            if st.get("by_size") and st.get("by_repo"):
                return st["by_size"], st["by_repo"], True
        except Exception:
            pass
    if os.path.exists(LANGS_SVG):
        try:
            txt = open(LANGS_SVG, encoding="utf-8").read()
            tokens = re.findall(r"<text[^>]*>(.*?)</text>", txt)
            by_size, by_repo = [], []
            mode = None
            i = 0
            while i < len(tokens):
                t = tokens[i]
                if t == "BY BYTES":
                    mode = "bytes"
                    i += 1
                    continue
                if t == "BY REPOS":
                    mode = "repos"
                    i += 1
                    continue
                if mode == "bytes" and i + 1 < len(tokens):
                    pct = int(tokens[i + 1].rstrip("%"))
                    by_size.append([t, pct])
                    i += 2
                elif mode == "repos" and i + 1 < len(tokens):
                    by_repo.append([t, int(tokens[i + 1])])
                    i += 2
                else:
                    i += 1
            if by_size and by_repo:
                return by_size[:5], by_repo[:5], False
        except Exception:
            pass
    return (
        [["typescript", 38], ["css", 21], ["html", 20], ["javascript", 17], ["python", 3]],
        [["python", 6], ["javascript", 5], ["css", 3], ["html", 2], ["typescript", 2]],
        False,
    )


def analytics(data):
    """White-card wrapper for streaks, BY BYTES / BY REPOS, and THE YEAR character map."""
    h = 548
    by_size, by_repo, size_is_raw = load_lang_stats()

    cur = data["current_streak"]
    lng = data["longest_streak"]
    cur_span = f"{pretty_date(cur['start'])} – {pretty_date(cur['end'])}" if cur.get("length") else "—"
    lng_span = f"{pretty_date(lng['start'])} – {pretty_date(lng['end'])}" if lng.get("length") else "—"

    # Language rows
    def lang_block(gx, title, rows, as_pct, base_delay):
        out = [
            f'<text class="f" {d(base_delay)} x="{gx}" y="220" font-family="{MONO}" font-size="10.5" letter-spacing="1.2" fill="{MUTED}">{title}</text>'
        ]
        top_val = max((v for _, v in rows), default=1) or 1
        total_val = sum(v for _, v in rows) or 1
        bar_x, bar_max, val_x = gx + 96, 224, gx + 372
        for ri, (name, val) in enumerate(rows[:5]):
            y = 242 + ri * 24
            bw = max(6.0, bar_max * (val / top_val))
            shown = (
                f"{val / total_val * 100:.0f}%" if (as_pct and size_is_raw)
                else (f"{val}%" if as_pct else f"{val}")
            )
            fill = TECH if ri == 0 else INK
            out.append(
                f'<g class="r" {d(base_delay + 0.08 + ri * 0.05)}>'
                f'<text x="{gx}" y="{y + 7}" font-family="{MONO}" font-size="12" fill="{INK}">{escape(name.lower()[:11])}</text>'
                f'<rect class="gx" style="animation-delay:{base_delay + 0.14 + ri * 0.05:.2f}s" x="{bar_x}" y="{y - 1}" width="{bw:.1f}" height="8" rx="4" fill="{fill}"/>'
                f'<text x="{val_x}" y="{y + 7}" text-anchor="end" font-family="{MONO}" font-size="11.5" fill="{MUTED}">{shown}</text>'
                f"</g>"
            )
        return "".join(out)

    # THE YEAR character map from data["days"]
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    weeks = []
    col = [None] * lead
    for day in days:
        col.append(day)
        if len(col) == 7:
            weeks.append(col)
            col = []
    if col:
        while len(col) < 7:
            col.append(None)
        weeks.append(col)

    ramp = [" ", ":", "+", "#", "@"]

    def lvl(v):
        for i, cut in enumerate((0, 2, 5, 9)):
            if v <= cut:
                return i
        return 4

    gx, gy = 84, 424
    art_w = 752
    row_h = 13.5
    year_rows = []
    for r in range(7):
        chars = []
        for w in weeks:
            d_obj = w[r]
            v = d_obj["count"] if d_obj else 0
            chars.append(ramp[lvl(v)] * 2)
        line = "".join(chars).rstrip()
        if not line:
            continue
        ry = gy + r * row_h + 10
        safe = escape(line)
        year_rows.append(
            f'<text class="f" {d(0.45 + r * 0.05)} xml:space="preserve" x="{gx}" y="{ry:.1f}" '
            f'font-family="{MONO}" font-size="10" fill="{INK_SOFT}" textLength="{len(line) * 6.8:.1f}" lengthAdjust="spacing">{safe}</text>'
        )

    day_labs = "".join(
        f'<text x="{gx - 10}" y="{gy + r * row_h + 10:.1f}" text-anchor="end" font-family="{MONO}" font-size="9.5" fill="{MUTED}">{lab}</text>'
        for r, lab in ((1, "mon"), (3, "wed"), (5, "fri"))
    )

    month_labs, last_m, last_x = [], None, -999.0
    col_px = 2 * 6.8
    for wi, w in enumerate(weeks):
        first_day = next((x for x in w if x is not None), None)
        if not first_day:
            continue
        dt = datetime.date.fromisoformat(first_day["date"])
        x = gx + wi * col_px
        if dt.month != last_m and wi < len(weeks) - 2 and x - last_x >= 44:
            month_labs.append(
                f'<text x="{x:.1f}" y="{gy + 7 * row_h + 15:.1f}" font-family="{MONO}" font-size="9.5" fill="{MUTED}">{dt.strftime("%b").lower()}</text>'
            )
            last_x = x
        last_m = dt.month

    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0.05)}>
  <text x="44" y="44" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{MUTED}">TECH JOURNEY ANALYTICS</text>
  <text x="836" y="44" text-anchor="end" font-family="{MONO}" font-size="11.5" letter-spacing="1" fill="{TECH}">STREAKS · LANGUAGES · YEAR MAP</text>
</g>
<text class="r" {d(0.12)} x="42" y="82" font-family="{SERIF}" font-size="36" fill="{INK}">Streaks, stack &amp; <tspan font-style="italic" fill="{TECH}">the year</tspan></text>

<!-- Row 1: Streaks -->
<g class="r" {d(0.2)}>
  <text x="44" y="142" font-family="{SERIF}" font-size="42" fill="{INK}">{cur['length']} <tspan font-style="italic" fill="{TECH}">days</tspan></text>
  <text x="44" y="164" font-family="{MONO}" font-size="11" letter-spacing="0.8" fill="{MUTED}">CURRENT STREAK  ·  {escape(cur_span)}</text>
</g>
<rect x="440" y="110" width="1" height="62" fill="{RULE}"/>
<g class="r" {d(0.28)}>
  <text x="472" y="142" font-family="{SERIF}" font-size="42" fill="{INK}">{lng['length']} <tspan font-style="italic">days</tspan></text>
  <text x="472" y="164" font-family="{MONO}" font-size="11" letter-spacing="0.8" fill="{MUTED}">LONGEST STREAK  ·  {escape(lng_span)}</text>
</g>

<rect x="44" y="190" width="792" height="1" fill="{RULE}"/>

<!-- Row 2: Languages -->
{lang_block(44, "BY BYTES", by_size, True, 0.3)}
{lang_block(464, "BY REPOS", by_repo, False, 0.36)}

<rect x="44" y="362" width="792" height="1" fill="{RULE}"/>

<!-- Row 3: THE YEAR -->
<g class="f" {d(0.42)}>
  <text x="44" y="388" font-family="{MONO}" font-size="10.5" letter-spacing="1.2" fill="{MUTED}">THE YEAR</text>
  <text x="44" y="407" font-family="{SANS}" font-size="12.5" fill="{INK_SOFT}">{data['active_days']} of {len(days)} days had a contribution</text>
  <text x="752" y="407" text-anchor="end" font-family="{MONO}" font-size="10" fill="{MUTED}">less</text>
  <text xml:space="preserve" x="760" y="407" font-family="{MONO}" font-size="10.5" fill="{INK}">: + # @</text>
  <text x="836" y="407" text-anchor="end" font-family="{MONO}" font-size="10" fill="{MUTED}">more</text>
</g>
{day_labs}
{''.join(year_rows)}
{''.join(month_labs)}
"""
    write(
        "analytics.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "mono"],
            f"Tech Journey Analytics: {cur['length']}-day current streak, {lng['length']}-day longest streak, top languages, and {data['active_days']} active days.",
        ),
    )


# ---- 4 · repo cards -----------------------------------------------------------
REPO_W, REPO_H = 880 / 3 - 8, 176
REPOS = [
    ("DPI_Engine", "Deep Packet Inspection engine inspecting packet payloads & SNI beyond firewall headers.", "Python", TECH),
    ("CodeForensics", "Evidence-backed repo intelligence & AST code archaeology for tracing regressions.", "TypeScript", STUDIO),
    ("SecScan.io", "GitHub security scanner analyzing public repos for vulnerabilities, secrets & misconfigs.", "TypeScript", LEARN),
]


def repo_card(i, name, desc, lang, color, stars):
    delay = 4.6 + i * 0.12
    meta = f"{lang}  ·  ★ {stars}" if stars else f"{lang}  ·  live"
    body = f"""
<rect width="{REPO_W}" height="{REPO_H}" rx="14" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="24" y="30" width="8" height="8" rx="2" fill="{color}"/>
  <text x="40" y="39" font-family="{SANS}" font-weight="600" font-size="18" fill="{INK}">{escape(name)}</text>
  {text_lines(24, 72, wrap(desc, 34), 21, f'font-family="{SANS}" font-size="14" fill="{INK_SOFT}"')}
  <text x="24" y="{REPO_H - 24}" font-family="{MONO}" font-size="12" fill="{MUTED}">{escape(meta)}</text>
</g>
"""
    write(
        f"repo-{name}.svg",
        svg(
            REPO_W,
            REPO_H,
            body,
            ["sans", "sans-b", "mono"],
            f"{name}: {desc}",
            left=4 * i,
            right=8 - 4 * i,
        ),
    )


def section_title(slug, text, italic, theme, delay=0.35):
    fg = "#e6edf3" if theme == "dark" else INK
    accent = "#6b8bff" if theme == "dark" else TECH
    body = (
        f'<text class="r" {d(delay)} x="2" y="46" font-family="{SERIF}" font-size="34" fill="{fg}">{escape(text)} '
        f'<tspan font-style="italic" fill="{accent}">{escape(italic)}</tspan></text>'
    )
    write(f"title-{slug}-{theme}.svg", svg(W, 64, body, ["serif", "serif-i"], f"{text} {italic}", bottom=0))


# ---- 5 · blue contribution graph -----------------------------------------------
BLUE = [PAPER_DEEP, "#c8d3ff", "#94a8ff", "#6280ff", TECH, "#1a3be0"]


def level_for(c):
    return 0 if c == 0 else 1 if c <= 5 else 2 if c <= 15 else 3 if c <= 30 else 4 if c <= 50 else 5


def heatmap(data):
    days = data["days"]
    first = datetime.date.fromisoformat(days[0]["date"])
    lead = (first.weekday() + 1) % 7
    cell, step, gx, gy = 12, 15, 44, 96
    cells, months, seen = [], [], set()
    for i, day in enumerate(days):
        k = i + lead
        col, row = divmod(k, 7)
        date = datetime.date.fromisoformat(day["date"])
        if date.day <= 7 and (date.year, date.month) not in seen and row == 0:
            seen.add((date.year, date.month))
            months.append((col, date.strftime("%b")))
        c = day["count"]
        delay = 1.0 + col * 0.03 + row * 0.02
        cells.append(
            f'<rect class="p" style="animation-delay:{delay:.2f}s" x="{gx + col * step}" y="{gy + row * step}" '
            f'width="{cell}" height="{cell}" rx="3" fill="{BLUE[level_for(c)]}">'
            f'<title>{day["date"]}: {c} contribution{"s" if c != 1 else ""}</title></rect>'
        )
    ncols = (len(days) + lead + 6) // 7
    right = gx + ncols * step - 3
    labels = "".join(
        f'<text x="{gx + col * step}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">{m}</text>'
        for col, m in months if col < ncols - 12
    )
    legend_x = right - len(BLUE) * 14
    legend = "".join(
        f'<rect x="{legend_x + i * 14}" y="{gy + 7 * step + 6}" width="11" height="11" rx="2.5" fill="{c}"/>'
        for i, c in enumerate(BLUE)
    )
    h = gy + 7 * step + 44
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<text class="r" {d(0.8)} x="42" y="62" font-family="{SERIF}" font-size="34" fill="{INK}">Every day, <tspan font-style="italic" fill="{TECH}">in blue</tspan></text>
<text class="f" {d(0.8)} x="{right}" y="60" text-anchor="end" font-family="{MONO}" font-size="12" letter-spacing="1" fill="{MUTED}">REFRESHED DAILY</text>
{''.join(cells)}
<g class="f" {d(2.4)}>{labels}
<text x="{legend_x - 8}" y="{gy + 7 * step + 16}" text-anchor="end" font-family="{MONO}" font-size="11" fill="{MUTED}">less</text>
{legend}
<text x="{legend_x + len(BLUE) * 14 + 2}" y="{gy + 7 * step + 16}" font-family="{MONO}" font-size="11" fill="{MUTED}">more</text></g>
"""
    write(
        "heatmap.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "mono"],
            f'Contribution graph: {data["total_contributions"]:,} contributions in the last year',
        ),
    )


# ---- 6 · get in touch card (white box like Image 5) ---------------------------
def contact():
    h = 330
    art_uri = img_uri("contact-art.jpg", "image/jpeg")
    boxes = [
        ("GitHub", "@Manas-5461X", "#111111", "GH"),
        ("LinkedIn", "manas-gandhi", "#0A66C2", "in"),
        ("Email", "manasgandhi684@gmail.com", "#EA4335", "M"),
        ("Portfolio", "manas-5461x.github.io", TECH, "↗"),
    ]
    tile_svgs = []
    for i, (label, sub, accent, badge_txt) in enumerate(boxes):
        col, row = i % 2, i // 2
        tx = 424 + col * 218
        ty = 114 + row * 82
        sub_size = "8.7" if len(sub) > 20 else "9.5"
        tile_svgs.append(
            f'<g class="r" {d(0.3 + i * 0.08)}>'
            f'<rect x="{tx}" y="{ty}" width="210" height="70" rx="10" fill="#ffffff" stroke="{RULE}" stroke-width="1"/>'
            f'<rect x="{tx + 12}" y="{ty + 17}" width="36" height="36" rx="8" fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-opacity="0.28"/>'
            f'<text x="{tx + 30}" y="{ty + 40}" text-anchor="middle" font-family="{MONO}" font-size="14" font-weight="600" fill="{accent}">{escape(badge_txt)}</text>'
            f'<text x="{tx + 57}" y="{ty + 33}" font-family="{SANS}" font-weight="600" font-size="14" fill="{INK}">{escape(label)}</text>'
            f'<text x="{tx + 57}" y="{ty + 50}" font-family="{MONO}" font-size="{sub_size}" fill="{MUTED}">{escape(sub)}</text>'
            f"</g>"
        )

    body = f"""
<defs>
  <clipPath id="c-art"><rect x="24" y="24" width="376" height="282" rx="12"/></clipPath>
</defs>
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0.1)}>
  <image clip-path="url(#c-art)" href="{art_uri}" x="24" y="24" width="376" height="282" preserveAspectRatio="xMidYMid slice"/>
  <rect x="24" y="24" width="376" height="282" rx="12" fill="none" stroke="{RULE}" stroke-width="1"/>
</g>
<text class="f" {d(0.12)} x="424" y="50" font-family="{MONO}" font-size="11.5" letter-spacing="1.2" fill="{STUDIO}">// GET IN TOUCH</text>
<text class="r" {d(0.2)} x="422" y="90" font-family="{SERIF}" font-size="35" fill="{INK}">Let's build <tspan font-style="italic" fill="{TECH}">something legendary</tspan></text>
{''.join(tile_svgs)}
<g class="f" {d(0.65)}>
  <rect class="live" x="426" y="289" width="7" height="7" rx="2" fill="{TECH}"/>
  <text x="441" y="296" font-family="{MONO}" font-size="10.8" fill="{INK_SOFT}">Pick a channel below to chat on AI, backend &amp; hackathons</text>
</g>
"""
    write(
        "contact.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "sans", "sans-b", "mono"],
            "Get in Touch with Manas Gandhi: GitHub, LinkedIn, Email, Portfolio.",
        ),
    )


def contact_buttons():
    """Four 25%-width clickable action button cards that tile cleanly under contact.svg."""
    btn_w, btn_h = (W - 3 * GAP) / 4, 58  # 211px drawn + 9px baked spacing = 220px (25%)
    buttons = [
        ("github", "GitHub", "View repos", "#111111", "GH"),
        ("linkedin", "LinkedIn", "Chat & connect", "#0A66C2", "in"),
        ("email", "Email", "Mail me", "#EA4335", "M"),
        ("portfolio", "Portfolio", "Visit site", TECH, "↗"),
    ]
    for pos, (slug, title, sub, accent, badge_txt) in enumerate(buttons):
        delay = 0.25 + pos * 0.08
        body = f"""
<rect width="{btn_w:.3f}" height="{btn_h}" rx="12" fill="{PAPER}"/>
<g class="r" {d(delay)}>
  <rect x="12" y="13" width="32" height="32" rx="8" fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-opacity="0.30"/>
  <text x="28" y="33.5" text-anchor="middle" font-family="{MONO}" font-size="12.5" font-weight="600" fill="{accent}">{escape(badge_txt)}</text>
  <text x="54" y="27" font-family="{SANS}" font-weight="600" font-size="13.5" fill="{INK}">{escape(title)}</text>
  <text x="54" y="42.5" font-family="{MONO}" font-size="10" fill="{MUTED}">{escape(sub)}</text>
  <text class="nu" x="{btn_w - 18:.1f}" y="33.5" text-anchor="end" font-family="{MONO}" font-size="13" fill="{accent}">&#8599;</text>
</g>
"""
        write(
            f"btn-{slug}.svg",
            svg(
                btn_w,
                btn_h,
                body,
                ["sans", "sans-b", "mono"],
                f"{title}: {sub}",
                left=3 * pos,
                right=9 - 3 * pos,
            ),
        )


# ---- 7 · profile views card ---------------------------------------------------
def fetch_profile_views():
    """Fetch current profile view count from komarev without overwriting on failure."""
    views = "424"
    try:
        import requests

        r = requests.get(
            f"https://komarev.com/ghpvc/?username={GH_USER}&style=for-the-badge",
            timeout=10,
        )
        if r.ok:
            m = re.search(r"PROFILE VIEWS:\s*([\d,]+)", r.text, re.I)
            if m:
                views = m.group(1).replace(",", "")
    except Exception as e:
        print(f"profile views unavailable, using default: {e}")
    return views


def views_card(views_str):
    h = 96
    body = f"""
<rect width="{W}" height="{h}" rx="14" fill="{PAPER}"/>
<g class="f" {d(0.1)}>
  <rect class="live" x="44" y="29" width="8" height="8" rx="2" fill="{TECH}"/>
  <text x="62" y="37" font-family="{MONO}" font-size="11" letter-spacing="1.2" fill="{MUTED}">PROFILE REACH</text>
</g>
<text class="r" {d(0.18)} x="42" y="72" font-family="{SERIF}" font-size="32" fill="{INK}">Thanks for <tspan font-style="italic" fill="{TECH}">stopping by</tspan></text>
<rect x="570" y="20" width="1" height="56" fill="{RULE}"/>
<g class="r" {d(0.25)}>
  {count_up(f"{views_str}+", "views", 602, 58, f'font-family="{SERIF}" font-size="38" fill="{TECH}"', 0.35)}
  <text x="602" y="77" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{MUTED}">ALL-TIME PROFILE VIEWS</text>
</g>
"""
    write(
        "views.svg",
        svg(
            W,
            h,
            body,
            ["serif", "serif-i", "mono"],
            f"Profile Reach: {views_str}+ all-time profile views.",
        ),
    )


def github_repo_metrics():
    """Fetch live star counts, original repo count, and total stars from GitHub API."""
    stars = {"DPI_Engine": 24, "CodeForensics": 1, "SecScan.io": 1}
    own_count = 22
    total_stars = 28
    try:
        import requests

        headers = {"User-Agent": f"{GH_USER}-profile-cards"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"

        r = requests.get(
            f"https://api.github.com/users/{GH_USER}/repos?per_page=100",
            headers=headers,
            timeout=10,
        )
        if r.ok:
            repos = r.json()
            own_repos = [x for x in repos if isinstance(x, dict) and not x.get("fork")]
            if own_repos:
                own_count = len(own_repos)
                total_stars = sum(int(x.get("stargazers_count", 0)) for x in repos if isinstance(x, dict))
                by_name = {x["name"]: int(x.get("stargazers_count", 0)) for x in repos if isinstance(x, dict)}
                for name, *_ in REPOS:
                    if name in by_name:
                        stars[name] = by_name[name]
    except Exception as e:
        print(f"repo metrics unavailable, using defaults: {e}")
    return stars, own_count, total_stars


if __name__ == "__main__":
    with open(DATA, encoding="utf-8") as f:
        data = json.load(f)
    stars, own_count, total_stars = github_repo_metrics()
    dpi_stars = stars.get("DPI_Engine", 24)

    hero()
    about()
    techstack()
    heatmap(data)
    activity(data)
    analytics(data)
    tile(
        "build",
        "BUILD",
        TECH,
        "#ffffff",
        f"{own_count}+",
        "projects",
        f"DPI Engine ({dpi_stars}★), CodeForensics, SecScan.io, DevGuard Pro & ShopKart.",
        3.1,
        0,
    )
    tile(
        "achieve",
        "ACHIEVE",
        STUDIO,
        "#ffffff",
        f"{total_stars}+",
        "stars",
        f"{dpi_stars}★ on DPI Engine, 8 merged OSS PRs & A-rank Ultra Committer trophy.",
        3.35,
        1,
    )
    tile(
        "learn",
        "LEARN",
        LEARN,
        INK,
        "4",
        "tracks",
        "BITS Pilani CS · Scaler SST — Applied AI & RAG, MERN, CyberSec & DSA.",
        3.6,
        2,
    )
    for i, (name, desc, lang, color) in enumerate(REPOS):
        repo_card(i, name, desc, lang, color, stars.get(name, 0))
    for slug, text, italic, delay in (
        ("about", "About", "me", 0.25),
        ("stack", "My tech", "stack", 0.35),
        ("cycle", "My contribution", "cycle", 0.45),
        ("achieved", "What I've", "achieved", 0.55),
        ("coding", "What I'm", "coding", 0.65),
        ("contact", "Get in", "touch", 0.75),
    ):
        section_title(slug, text, italic, "dark", delay)
        section_title(slug, text, italic, "light", delay)
    contact()
    contact_buttons()
    views_card(fetch_profile_views())
