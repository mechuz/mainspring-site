#!/usr/bin/env python3
"""Assemble public/ from content/ + templates/base.html.

Same shape as the Kirby Gate site: one file per page in content/ (body only,
with a <!--meta --> block), one shared template, and a build step that writes
clean-URL directories into public/. GitHub Actions runs this on every push and
on a schedule; nothing here needs a server.

    python3 build.py

Never edit public/ by hand — it is overwritten.
"""
import json
import re
import shutil
import datetime as dt
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parent
CONTENT = ROOT / "content"
TEMPLATES = ROOT / "templates"
ASSETS = ROOT / "assets"
PUBLIC = ROOT / "public"

SITE = "https://mainspringhcp.com"
DOMAIN = "mainspringhcp.com"
EMAIL = "info@mainspringhcp.com"
PHONE_FMT = "650-418-2280"
PHONE_TEL = "+16504182280"

# Google Calendar appointment schedule (Google Workspace -> Calendar -> Appointment
# schedules -> Share -> "Website embed"). Paste the iframe's src here. Empty =
# /book/ shows the intake form instead, so the page never dead-ends.
BOOKING_URL = ""

# nav label -> path; the meta block's `nav:` key marks the current one
NAV = [  # ordered by how likely the click is to turn into a lead
    ("services", "/services/", "Services"),
    ("consultants", "/consultants/", "Consultants"),
    ("state", "/state-agencies/", "State agencies"),
    ("about", "/about/", "About"),
]

STICKY = f"""<div class="sticky-cta">
  <div class="sticky-inner">
    <div class="txt">Under a survey or short an administrator?
      <small>Same-day response on survey and leadership situations.</small></div>
    <div class="sticky-actions" style="display:flex;gap:10px">
      <a class="btn btn-primary" href="/book/">Book a consultation</a>
    </div>
  </div>
</div>"""

# Old .html URLs that existed before clean URLs, so nothing already indexed 404s.
LEGACY = {
    "checkout/index.html": "/book/",
    "overview.html": "/",
    "overview/index.html": "/",
    "services.html": "/services/",
    "assessment.html": "/how-we-work/",
    "about.html": "/about/",
    "contact.html": "/contact/",
    "insights.html": "/insights/",
    "industry.html": "/industry/",
    "join-our-network.html": "/consultant-network/",
    "interim-executive-leadership.html": "/services/interim-executive-leadership/",
    "survey-remediation.html": "/services/survey-remediation/",
    "operational-financial-restructuring.html": "/services/operational-financial-restructuring/",
    "operating-systems-buildout.html": "/services/operating-systems-buildout/",
    "capital-projects-redesign.html": "/services/capital-projects-redesign/",
    "rebranding-census-recovery.html": "/services/",
    "services/rebranding-census-recovery/index.html": "/services/",
    "services/technology-agentic-advisory/index.html": "/services/",
    "privacy-policy.html": "/privacy-policy/",
    "terms-of-use.html": "/terms-of-use/",
    "disclosures.html": "/disclosures/",
    "insight-plan-of-correction.html": "/insights/plan-of-correction/",
    "insight-ed-vacancy-cost.html": "/insights/ed-vacancy-cost/",
    "insight-al-margin-erosion.html": "/insights/al-margin-erosion/",
    "insight-immediate-jeopardy-first-72-hours.html": "/insights/immediate-jeopardy-first-72-hours/",
    "insight-five-star-staffing-rating.html": "/insights/five-star-staffing-rating/",
    "insight-census-recovery-playbook.html": "/insights/census-recovery-playbook/",
}


# ----------------------------------------------------------------- helpers
def parse_meta(text):
    """Split a content file into its <!--meta --> dict and its body."""
    m = re.match(r"\s*<!--meta\s*\n(.*?)\n-->\s*\n?(.*)", text, re.S)
    if not m:
        raise SystemExit("content file has no <!--meta --> block")
    meta = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if ":" not in line:
            raise SystemExit(f"bad meta line: {line}")
        k, v = line.split(":", 1)
        meta[k.strip()] = v.strip()
    return meta, m.group(2)


def tokens(s, extra=None):
    out = (s.replace("{{phone_fmt}}", PHONE_FMT)
            .replace("{{phone_tel}}", PHONE_TEL)
            .replace("{{email}}", EMAIL)
            .replace("{{site}}", SITE)
            .replace("{{domain}}", DOMAIN))
    for k, v in (extra or {}).items():
        out = out.replace("{{" + k + "}}", v)
    return out


def tabstrip(current):
    home_cur = ' aria-current="page"' if current == "" else ""
    rows = [f'    <a href="/"{home_cur}>Home</a>']
    for i, (key, href, label) in enumerate(NAV):
        cur = ' aria-current="page"' if key == current else ""
        rows.append(f'    <a href="{href}"{cur}>{label}</a>')
        if i == 0:
            rows.append('    <a href="/book/" class="tab-cta">Book a consultation</a>')
            rows.append('    <a href="/contact/">Contact</a>')
    rows.append('    <a href="/industry/">Industry news</a>')
    return "\n".join(rows)


def navlinks(current):
    rows = []
    for key, href, label in NAV:
        cur = ' aria-current="page"' if key == current else ""
        rows.append(f'      <a class="nav-hide" href="{href}"{cur}>{label}</a>')
    return "\n".join(rows)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def render(meta, body, template, assetv):
    page_path = meta["path"]
    html = tokens(template, {
        "title": escape(meta["title"], quote=True),
        "description": escape(meta.get("description", ""), quote=True),
        "path": page_path,
        "og_type": meta.get("og_type", "website"),
        "head": meta.get("_head", ""),
        "body": tokens(body),
        "navlinks": navlinks(meta.get("nav", "")),
        "tabstrip": tabstrip(meta.get("nav", "") if meta["path"] != "/" else ""),
        "nav_dark": " nav-dark" if meta.get("nav_dark") == "yes" else "",
        "sticky": "" if meta.get("sticky") == "no" else STICKY,
        "year": str(dt.date.today().year),
        "assetv": assetv,
    })
    if page_path == "/":
        out = PUBLIC / "index.html"
    elif page_path.endswith(".html"):          # /404.html must be a file, not a directory
        out = PUBLIC / page_path.lstrip("/")
    else:
        out = PUBLIC / page_path.strip("/") / "index.html"
    write(out, html)
    return page_path


# ----------------------------------------------------------------- news feed
def _when(iso):
    try:
        d = dt.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)
    except ValueError:
        return ""
    days = (dt.datetime.now(dt.timezone.utc) - d).days
    if days <= 0:
        return "Today"
    if days == 1:
        return "Yesterday"
    if days <= 6:
        return f"{days} days ago"
    return d.strftime("%b %-d, %Y")


def _cards(items, empty):
    if not items:
        return '<div class="feed-skel">%s</div>' % empty
    return "\n".join(
        '<a class="feed-item" href="%s" target="_blank" rel="noopener nofollow">'
        '<span class="src">%s</span><h3>%s</h3><span class="date">%s</span></a>' % (
            escape(it["link"], quote=True), escape(it["source"]), escape(it["title"]),
            escape(_when(it.get("published", "")))) for it in items[:24])


def news_html():
    """Render the industry AND regulatory headlines at BUILD time from
    content/news_feeds.json, so the page is real HTML and needs no server.
    Returns (industry_cards, regulatory_cards, updated_label)."""
    f = CONTENT / "news_feeds.json"
    waiting = ("Headlines are refreshed automatically several times a day; "
               "the next run will fill this in.")
    if not f.exists():
        return '<div class="feed-skel">%s</div>' % waiting, '<div class="feed-skel">%s</div>' % waiting, ""
    data = json.loads(f.read_text(encoding="utf-8"))
    stamp = data.get("fetched_at", "")
    try:
        label = dt.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").strftime("%b %-d, %H:%M UTC")
    except ValueError:
        label = ""
    return (_cards(data.get("items", []), "No industry headlines came back on the last run."),
            _cards(data.get("regulatory", []), "No regulatory items came back on the last run."),
            label)


# ----------------------------------------------------------------- booking
def booking_block():
    if BOOKING_URL:
        return ('<div class="panel reveal" style="padding:0;overflow:hidden;background:#fff">'
                f'<iframe src="{BOOKING_URL}" title="Book a call with Mainspring" style="border:0;width:100%;height:760px;display:block" loading="lazy"></iframe></div>'
                '<p class="fineprint" style="margin-top:1rem">Times are shown in your time zone. You will receive a calendar invitation with a video link.</p>')
    # not wired yet: fall back to the full intake form so the page still converts
    contact = (CONTENT / "contact.html").read_text(encoding="utf-8")
    form = re.search(r'<form class="site-form"[\s\S]*?</form>', contact)
    return ('<p class="lead reveal" style="margin:0 0 1.6rem">Online booking is being connected to our calendar. '
            'In the meantime tell us what is going on and we will send times the same day.</p>' + (form.group(0) if form else ""))


def booking_block_inline():
    if BOOKING_URL:
        return ('<p class="fineprint" style="margin:0 0 .6rem">Pick a slot. Times are shown in your time zone.</p>'
                f'<div style="border-radius:16px;overflow:hidden;background:#fff;border:1px solid var(--line)"><iframe src="{BOOKING_URL}" title="Pick a time with Mainspring" style="border:0;width:100%;height:640px;display:block" loading="lazy"></iframe></div>'
                '<input type="hidden" name="time_picked_in_calendar" value="yes">')
    return ('<p class="fineprint" style="margin:0 0 .4rem">Give us two or three times that work and we confirm one the same day, in your time zone.</p>'
            '<div class="row"><div><label for="b-t1">First choice *</label><input id="b-t1" name="preferred_time_1" type="datetime-local" required></div>'
            '<div><label for="b-t2">Second choice</label><input id="b-t2" name="preferred_time_2" type="datetime-local"></div></div>'
            '<label for="b-tz">Your time zone</label><select id="b-tz" name="time_zone"><option>Eastern</option><option>Central</option><option>Mountain</option><option>Pacific</option><option>Other</option></select>')


# ----------------------------------------------------------------- consultants + diagnosis tool
def consultants():
    f = CONTENT / "consultants.json"
    if not f.exists():
        return []
    return [c for c in json.loads(f.read_text(encoding="utf-8")) if c.get("published")]

def consultant_cards():
    out = []
    for c in consultants():
        ini = "".join(w[0] for w in c["name"].split()[:2])
        text = " ".join([c["name"], c.get("title", ""), " ".join(c.get("credentials", [])), " ".join(c.get("specialties", [])), " ".join(c.get("settings", []))])
        modes = {"video": "Video", "phone": "Phone", "in-person": "In person"}
        out.append(
            f'<article class="ccard" data-text="{escape(text, quote=True)}" data-states="{"|".join(c.get("states", []))}" '
            f'data-specs="{"|".join(c.get("specialties", []))}" data-settings="{"|".join(c.get("settings", []))}" data-modes="{"|".join(c.get("modes", []))}">'
            f'<div class="ccard-top"><span class="mono">{escape(ini)}</span><div><h3>{escape(c["name"])}</h3><p class="ccard-t">{escape(c.get("title", ""))}</p></div></div>'
            f'<p class="ccard-cred">{escape(" · ".join(c.get("credentials", [])))}{(" · " + str(c["years"]) + " years") if c.get("years") else ""}</p>'
            f'<p class="ccard-bio">{escape(c.get("bio", ""))}</p>'
            f'<div class="ccard-tags">{"".join(f"<span>{escape(t)}</span>" for t in c.get("specialties", [])[:5])}</div>'
            f'<p class="ccard-meta">{escape(", ".join(c.get("states", [])))} · {escape(", ".join(c.get("settings", [])))}</p>'
            f'<div class="ccard-modes">{"".join(f"<span>{modes[m]}</span>" for m in c.get("modes", []) if m in modes)}</div>'
            f'<div class="ccard-actions"><a class="btn btn-primary" href="/book/?consultant={c["slug"]}&amp;mode=video">Book a video call <span class="arrow">&rarr;</span></a>'
            f'<a class="btn btn-ghost" href="/book/?consultant={c["slug"]}&amp;mode=phone">Phone</a><a class="btn btn-ghost" href="/book/?consultant={c["slug"]}&amp;mode=in-person">In person</a></div>'
            f'</article>')
    return "\n".join(out) or '<p class="cf-empty">Profiles are being published. <a href="/book/">Book a consultation</a> and we match you by hand.</p>'

def _opts(key):
    vals = sorted({v for c in consultants() for v in c.get(key, [])})
    return "".join(f'<option>{escape(v)}</option>' for v in vals)

def consultant_options():
    return "".join(f'<option value="{c["slug"]}">{escape(c["name"])} — {escape(c.get("title", ""))}</option>' for c in consultants())

def consultants_json():
    slim = [{k: c.get(k) for k in ("slug", "name", "title", "credentials", "states", "specialties", "settings", "modes", "featured")} for c in consultants()]
    return '<script type="application/json" id="ms-consultants">' + json.dumps(slim).replace("</", "<\\/") + "</script>"

def diagnose_tool():
    f = CONTENT / "_diagnose.html"
    return f.read_text(encoding="utf-8") if f.exists() else ""

def dynamic(body):
    if "{{booking_block}}" in body:
        body = body.replace("{{booking_block}}", booking_block())
    if "{{booking_block_inline}}" in body:
        body = body.replace("{{booking_block_inline}}", booking_block_inline())
    if "{{diagnose_tool}}" in body:
        body = body.replace("{{diagnose_tool}}", diagnose_tool())
    for tok, fn in (("consultant_cards", consultant_cards), ("consultant_states", lambda: _opts("states")),
                    ("consultant_specialties", lambda: _opts("specialties")), ("consultant_settings", lambda: _opts("settings")),
                    ("consultant_options", consultant_options)):
        if "{{" + tok + "}}" in body:
            body = body.replace("{{" + tok + "}}", fn())
    if "ms-consultants" not in body and ("dx-sec" in body or 'class="ck"' in body):
        body = consultants_json() + body
    return body


# ----------------------------------------------------------------- build
def main():
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    template = (TEMPLATES / "base.html").read_text(encoding="utf-8")
    assetv = dt.datetime.now().strftime("%Y%m%d%H%M")
    paths = []

    # assets
    shutil.copytree(ASSETS, PUBLIC / "assets")

    # pages
    for f in sorted(CONTENT.glob("*.html")):
        if f.name.endswith(".head.html") or f.name == "case-studies.html" or f.name.startswith("_"):
            continue
        meta, body = parse_meta(f.read_text(encoding="utf-8"))
        if meta.get("status", "published") != "published":
            continue
        head = CONTENT / f.name.replace(".html", ".head.html")
        meta["_head"] = tokens(head.read_text(encoding="utf-8")) if head.exists() else ""
        body = dynamic(body)
        if meta.get("feed") == "yes":
            cards, reg, label = news_html()
            body = (body.replace("{{feed_items}}", cards).replace("{{reg_items}}", reg)
                        .replace("{{feed_updated}}", label))
        p = render(meta, body, template, assetv)
        if meta.get("sitemap") != "no" and not p.endswith(".html"):
            paths.append((p, meta.get("priority", "0.7"), meta.get("changefreq", "monthly")))

    # blog posts
    posts = []
    for f in sorted(CONTENT.glob("blog/*.html")):
        if f.name.endswith(".head.html"):
            continue
        meta, body = parse_meta(f.read_text(encoding="utf-8"))
        if meta.get("status", "published") != "published":
            continue
        head = f.parent / f.name.replace(".html", ".head.html")
        meta["_head"] = tokens(head.read_text(encoding="utf-8")) if head.exists() else ""
        meta.setdefault("nav", "insights")
        paths.append((render(meta, body, template, assetv), "0.7", "monthly"))
        posts.append(meta)

    # case studies: content/case-studies/<slug>.html -> /case-studies/<slug>/, index gets cards
    studies = []
    for f in sorted(CONTENT.glob("case-studies/*.html")):
        if f.name.endswith(".head.html"):
            continue
        meta, body = parse_meta(f.read_text(encoding="utf-8"))
        if meta.get("status", "published") != "published":
            continue
        head = f.parent / f.name.replace(".html", ".head.html")
        meta["_head"] = tokens(head.read_text(encoding="utf-8")) if head.exists() else ""
        meta.setdefault("nav", "cases")
        paths.append((render(meta, body, template, assetv), "0.8", "monthly"))
        studies.append(meta)
    idx = CONTENT / "case-studies.html"
    if idx.exists():
        meta, body = parse_meta(idx.read_text(encoding="utf-8"))
        head = CONTENT / "case-studies.head.html"
        meta["_head"] = tokens(head.read_text(encoding="utf-8")) if head.exists() else ""
        cards = "".join(
            '<a class="post-card reveal" href="%s"><p class="meta">%s</p><h3>%s</h3><p>%s</p>'
            '<span class="more">Read the case study &rarr;</span></a>' % (
                m["path"], escape(m.get("sector", "Case study")), escape(m.get("headline", m["title"])),
                escape(m.get("summary", m.get("description", "")))) for m in studies)
        body = body.replace("{{case_study_cards}}", cards or
            '<p class="lead">Case studies are being added. Ask us for references in the meantime.</p>')
        paths.append((render(meta, body, template, assetv), "0.9", "monthly"))

    # legacy .html -> clean URL, so older links keep working
    for old, new in LEGACY.items():
        write(PUBLIC / old,
              f'<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
              f'<title>Moved</title><link rel="canonical" href="{SITE}{new}">'
              f'<meta http-equiv="refresh" content="0; url={new}">'
              f'<meta name="robots" content="noindex">'
              f'</head><body><p>This page moved to <a href="{new}">{SITE}{new}</a>.</p></body></html>')

    # sitemap / robots / CNAME
    today = dt.date.today().isoformat()
    urls = "\n".join(
        f"  <url><loc>{SITE}{p}</loc><lastmod>{today}</lastmod>"
        f"<changefreq>{cf}</changefreq><priority>{pr}</priority></url>"
        for p, pr, cf in sorted(set(paths)))
    write(PUBLIC / "sitemap.xml",
          '<?xml version="1.0" encoding="UTF-8"?>\n'
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + urls + "\n</urlset>\n")
    write(PUBLIC / "robots.txt", f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    write(PUBLIC / "CNAME", DOMAIN + "\n")
    write(PUBLIC / "version.txt", assetv + "\n")

    print(f"built {len(paths)} pages ({len(posts)} posts) + {len(LEGACY)} redirects -> public/")


if __name__ == "__main__":
    main()
