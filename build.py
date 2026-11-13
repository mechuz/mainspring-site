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


# Practice areas. Every advisor sits in exactly one; the directory, the booking form and
# the plan tool all group by these. Order = order on the page.
CATEGORIES = [
    ("administration", "Administration & executive leadership", "Administration",
     "Licensed administrators, executive directors and regional operators who have run buildings. Interim seats, turnarounds, temporary management and day-to-day operating discipline.",
     ["Interim leadership", "Turnaround", "Temporary management", "Operations"]),
    ("clinical", "Clinical & nursing leadership", "Clinical",
     "Directors of nursing, infection preventionists, MDS and quality leads. Clinical systems, staffing models, documentation and the care side of a survey.",
     ["Clinical operations", "Infection control", "MDS & reimbursement", "Quality"]),
    ("compliance", "Survey, compliance & regulatory", "Compliance",
     "People who have sat across from surveyors. Plans of correction, immediate jeopardy, informal dispute resolution, mock surveys and the monthly discipline that keeps a building in compliance.",
     ["Survey remediation", "Plan of correction", "Mock survey", "Life safety"]),
    ("finance", "Finance, revenue cycle & restructuring", "Finance",
     "CFOs, controllers, business office leaders and restructuring operators. Budgets that hold, payroll and agency spend, billing and collections, forensic reviews and underwriting.",
     ["Restructuring", "Budgeting & financial analysis", "Forensic & payroll analysis", "Revenue cycle", "Due diligence & underwriting"]),
    ("marketing", "Marketing, census & admissions", "Marketing & census",
     "Admissions directors, sales leaders and marketers who grow census honestly: referral relationships, hospital and physician outreach, digital presence, pricing and move-in process.",
     ["Census growth", "Admissions", "Referral development", "Brand & digital"]),
    ("workforce", "Human resources & workforce", "HR & workforce",
     "Recruiting, retention, scheduling and culture. Agency reduction, staffing plans that meet the hours, onboarding that sticks and leaders who stay.",
     ["Recruiting & retention", "Scheduling & agency reduction", "Training", "Culture"]),
    ("capital", "Capital projects, facilities & life safety", "Capital & facilities",
     "Renovations, repositioning, life-safety corrections and plant operations. Budgets, phasing around residents and getting the work accepted by the state.",
     ["Capital projects", "Life safety", "Plant operations", "Repositioning"]),
    ("technology", "Technology, EHR & systems", "Technology & systems",
     "EHR, billing, scheduling and reporting systems that actually get used. Vendor selection, implementation, data and the operating dashboards leadership runs on.",
     ["EHR & systems", "Reporting & dashboards", "Vendor selection", "Agentic workflow"]),
]
CAT = {k: (label, short, desc, tags) for k, label, short, desc, tags in CATEGORIES}
_ROLE_TO_CAT = {"administrator": "administration", "executive": "administration", "finance": "finance", "restructuring": "finance",
                "nurse": "clinical", "clinical": "clinical", "don": "clinical", "survey": "compliance", "compliance": "compliance",
                "marketing": "marketing", "census": "marketing", "admissions": "marketing", "hr": "workforce", "capital": "capital",
                "facilit": "capital", "technology": "technology", "ehr": "technology"}

def cat_of(c):
    k = c.get("category")
    if k in CAT:
        return k
    low = (c.get("role", "") + " " + c.get("title", "")).lower()
    for w, k in _ROLE_TO_CAT.items():
        if w in low:
            return k
    return "administration"

def by_category():
    out = {k: [] for k in CAT}
    for c in consultants():
        out[cat_of(c)].append(c)
    return out

def prof_url(c):
    return f"/consultants/{c['slug']}/"

def initials(c):
    return "".join(w[0] for w in c["name"].split()[:2])

def category_tiles(current=None, compact=False):
    counts = {k: len(v) for k, v in by_category().items()}
    out = []
    for k, label, short, desc, tags in CATEGORIES:
        n = counts.get(k, 0)
        cur = ' aria-current="page"' if k == current else ""
        meta = f"{n} profile{'s' if n != 1 else ''} published" if n else "Matched from the network"
        out.append(f'<a class="cattile c-{k}" href="/consultants/{k}/"{cur}><span class="cat-ico" aria-hidden="true"></span><b>{escape(short if compact else label)}</b>'
                   + ("" if compact else f'<span class="cat-desc">{escape(desc.split(". ")[0])}.</span>')
                   + f'<span class="cat-meta">{meta}</span></a>')
    return f'<div class="catgrid{" compact" if compact else ""}">' + "".join(out) + "</div>"

def category_options():
    return "".join(f'<option value="{k}">{escape(label)}</option>' for k, label, *_ in CATEGORIES)

def card_for(c):
    """One directory card for a single consultant (same markup as the directory grid)."""
    for part in consultant_cards(only={cat_of(c)}).split("</article>"):
        if f'href="{prof_url(c)}"' in part:
            return part + "</article>"
    return ""


def consultant_cards(only=None):
    out = []
    for c in consultants():
        if only is not None and cat_of(c) not in only:
            continue
        ini = initials(c)
        text = " ".join([c["name"], c.get("title", ""), " ".join(c.get("credentials", [])), " ".join(c.get("specialties", [])), " ".join(c.get("settings", []))])
        modes = {"video": "Video", "phone": "Phone", "in-person": "In person"}
        out.append(
            f'<article class="ccard" data-text="{escape(text, quote=True)}" data-states="{"|".join(c.get("states", []))}" '
            f'data-specs="{"|".join(c.get("specialties", []))}" data-settings="{"|".join(c.get("settings", []))}" data-modes="{"|".join(c.get("modes", []))}" data-cat="{cat_of(c)}">'
            f'<div class="ccard-top"><span class="mono">{escape(ini)}</span><div><h3><a href="{prof_url(c)}">{escape(c["name"])}</a></h3><p class="ccard-t">{escape(c.get("title", ""))}</p><p class="ccard-cat">{escape(CAT[cat_of(c)][1])}</p></div></div>'
            f'<p class="ccard-cred">{escape(" · ".join(c.get("credentials", [])))}{(" · " + str(c["years"]) + " years") if c.get("years") else ""}</p>'
            f'<p class="ccard-bio">{escape(c.get("bio", ""))}</p>'
            f'<div class="ccard-tags">{"".join(f"<span>{escape(t)}</span>" for t in c.get("specialties", [])[:5])}</div>'
            f'<p class="ccard-meta">{escape(", ".join(c.get("states", [])))} · {escape(", ".join(c.get("settings", [])))}</p>'
            f'<div class="ccard-modes">{"".join(f"<span>{modes[m]}</span>" for m in c.get("modes", []) if m in modes)}</div>'
            f'<div class="ccard-actions"><a class="btn btn-primary" href="/book/?consultant={c["slug"]}&amp;mode=video">Book a video call <span class="arrow">&rarr;</span></a>'
            f'<a class="btn btn-ghost" href="/book/?consultant={c["slug"]}&amp;mode=phone">Phone</a><a class="btn btn-ghost" href="/book/?consultant={c["slug"]}&amp;mode=in-person">In person</a></div>'
            f'<a class="ccard-more" href="{prof_url(c)}">Full profile &amp; résumé &rarr;</a>'
            f'</article>')
    return "\n".join(out) or '<p class="cf-empty">Profiles are being published. <a href="/book/">Book a consultation</a> and we match you by hand.</p>'

def _opts(key):
    vals = sorted({v for c in consultants() for v in c.get(key, [])})
    return "".join(f'<option>{escape(v)}</option>' for v in vals)

def consultant_options():
    groups = by_category()
    out = []
    for k, label, *_ in CATEGORIES:
        if groups[k]:
            out.append(f'<optgroup label="{escape(label)}">' + "".join(
                f'<option value="{c["slug"]}">{escape(c["name"])} — {escape(c.get("title", ""))}</option>' for c in groups[k]) + "</optgroup>")
    return "".join(out)

def consultants_json():
    slim = [dict({k: c.get(k) for k in ("slug", "name", "title", "credentials", "states", "specialties", "settings", "modes", "featured")}, category=cat_of(c)) for c in consultants()]
    return '<script type="application/json" id="ms-consultants">' + json.dumps(slim).replace("</", "<\\/") + "</script>"


# ----------------------------------------------------------------- advisor marketplace pages
def _book_panel(c, first):
    return (f'<aside class="prof-book reveal"><p class="eyebrow">Book {escape(first)}</p>'
            f'<a class="btn btn-primary block" href="/book/?consultant={c["slug"]}&amp;mode=video">Book a video call <span class="arrow">&rarr;</span></a>'
            f'<a class="btn btn-ghost block" href="/book/?consultant={c["slug"]}&amp;mode=phone">Book a phone call</a>'
            f'<a class="btn btn-ghost block" href="/book/?consultant={c["slug"]}&amp;mode=in-person">Meet at the building</a>'
            f'<p class="fineprint">The first 30-minute consultation is included, no charge. Scope, dates and fee are in writing before any work.</p>'
            f'<a class="prof-intro-link" href="#intro">Prefer an introduction by email? &darr;</a></aside>')

def _intro_form(c, first):
    return ('<div class="prof-block reveal" id="intro"><h2>Request an introduction</h2>'
            f'<p>Not ready to book a time? Tell us about the building and {escape(first)} replies by email, usually the same day.</p>'
            f'<form class="site-form" action="https://formsubmit.co/{EMAIL}" method="POST">'
            f'<input type="hidden" name="_cc" value="{EMAIL}"><input type="hidden" name="_template" value="table">'
            f'<input type="hidden" name="_subject" value="INTRODUCTION — {escape(c["name"], quote=True)} — mainspringhcp.com">'
            f'<input type="hidden" name="_next" value="{SITE}/thank-you/"><input type="hidden" name="_captcha" value="false">'
            f'<input type="hidden" name="consultant" value="{c["slug"]}"><input type="hidden" name="consultant_name" value="{escape(c["name"], quote=True)}">'
            '<input type="text" name="_honey" style="display:none" tabindex="-1" autocomplete="off">'
            '<div class="row"><div><label for="i-name">Your name *</label><input id="i-name" name="name" required autocomplete="name"></div>'
            '<div><label for="i-email">Email *</label><input id="i-email" name="email" type="email" required autocomplete="email"></div></div>'
            '<div class="row"><div><label for="i-org">Organization</label><input id="i-org" name="organization" autocomplete="organization"></div>'
            '<div><label for="i-state">State</label><input id="i-state" name="state" maxlength="20"></div></div>'
            '<label for="i-msg">What is going on at the building?</label><textarea id="i-msg" name="details" rows="4"></textarea>'
            '<button class="btn btn-primary" type="submit">Send the introduction request <span class="arrow">&rarr;</span></button>'
            '<p class="fineprint">Confidential. Facility and client names are never published without written consent.</p>'
            '</form></div>')

def profile_page(c):
    k = cat_of(c); label, short = CAT[k][0], CAT[k][1]; first = c["name"].split()[0]
    exp = c.get("experience") or []
    edu = c.get("education") or []
    good = c.get("good_for") or []
    related = [r for r in by_category()[k] if r["slug"] != c["slug"]][:3]
    title = f'{c["name"]} — {c.get("title", "Consultant")} | Mainspring Healthcare Partners'
    desc = c.get("headline") or c.get("bio", "")
    person = {"@context": "https://schema.org", "@type": "Person", "name": c["name"], "jobTitle": c.get("title", ""),
              "worksFor": {"@type": "Organization", "name": "Mainspring Healthcare Partners", "url": SITE},
              "url": SITE + prof_url(c), "knowsAbout": c.get("specialties", [])}
    head = '<script type="application/ld+json">' + json.dumps(person).replace("</", "<\\/") + "</script>"
    years = (" · " + str(c["years"]) + " years") if c.get("years") else ""
    modes = ", ".join(m.replace("in-person", "in person") for m in c.get("modes", []))
    b = [f'<div class="container"><p class="crumbs"><a href="/">Home</a> · <a href="/consultants/">Consultants</a> · <a href="/consultants/{k}/">{escape(short)}</a> · {escape(c["name"])}</p></div>',
         '<section class="prof-sec"><div class="container"><div class="prof">',
         f'<header class="prof-head reveal"><span class="prof-avatar">{escape(initials(c))}</span><div>'
         f'<p class="eyebrow"><a href="/consultants/{k}/">{escape(label)}</a></p><h1>{escape(c["name"])}</h1><p class="prof-title">{escape(c.get("title", ""))}</p>'
         f'<p class="prof-cred">{escape(" · ".join(c.get("credentials", [])))}{years}</p>'
         f'<div class="prof-facts"><span><b>Where</b>{escape(", ".join(c.get("states", [])))}</span><span><b>Settings</b>{escape(", ".join(c.get("settings", [])))}</span><span><b>Meets by</b>{escape(modes)}</span></div>'
         '</div></header>',
         _book_panel(c, first),
         '<div class="prof-body">',
         f'<div class="prof-block reveal"><h2>About</h2><p class="lead">{escape(c.get("headline") or c.get("bio", ""))}</p>' + (f'<p>{escape(c["bio"])}</p>' if c.get("headline") and c.get("bio") else "") + "</div>",
         '<div class="prof-block reveal"><h2>Specialties</h2><div class="ccard-tags big">' + "".join(f"<span>{escape(t)}</span>" for t in c.get("specialties", [])) + "</div></div>"]
    if good:
        b.append(f'<div class="prof-block reveal"><h2>Call {escape(first)} when</h2><ul class="prof-list">' + "".join(f"<li>{escape(g)}</li>" for g in good) + "</ul></div>")
    if exp:
        rows = []
        for e in exp:
            rows.append(f'<li><span class="when">{escape(e.get("when", ""))}</span><div><b>{escape(e.get("role", ""))}</b>'
                        + (f'<span>{escape(e["org"])}</span>' if e.get("org") else "") + (f'<p>{escape(e["note"])}</p>' if e.get("note") else "") + "</div></li>")
        b.append('<div class="prof-block reveal"><h2>Experience</h2><ol class="prof-exp">' + "".join(rows) + "</ol></div>")
    creds = list(c.get("credentials", [])) + list(edu)
    if creds:
        b.append('<div class="prof-block reveal"><h2>Licenses, credentials &amp; education</h2><ul class="prof-list plain">' + "".join(f"<li>{escape(x)}</li>" for x in creds) + "</ul></div>")
    b.append(f'<div class="prof-block reveal"><h2>How an engagement with {escape(first)} works</h2><ol class="prof-steps">'
             '<li><b>Book the consultation.</b> Thirty minutes by video, phone or at the building. You describe the situation; we tell you what we would do first.</li>'
             '<li><b>Scope in writing.</b> Deliverables, dates and fee before any work starts. The first 30 days are about taking control; later phases are set by the building, not by a template.</li>'
             '<li><b>Work and monthly reporting.</b> On site or alongside your team, with a written monthly report to ownership, the board or the agency.</li></ol></div>')
    b.append(_intro_form(c, first))
    b.append("</div></div></div></section>")
    if related:
        b.append(f'<section style="padding-top:0"><div class="container"><div class="head reveal"><p class="eyebrow">Also in {escape(short.lower())}</p><h2 class="h2">Other advisors in this practice area</h2></div><div class="cgrid reveal">'
                 + "".join(card_for(r) for r in related) + "</div></div></section>")
    lk = 'style="color:#fff;border-bottom:1px solid rgba(255,255,255,.4)"'
    b.append(f'<section style="padding-top:0"><div class="container"><div class="diag reveal"><div><p class="seclabel">Not sure {escape(first)} is the right fit?</p><h2>Tell us the issue. We match the advisor.</h2>'
             '<p>Three questions on the home page produce the first-30-days plan and the advisor who would run it.</p><a class="btn btn-on-dark" href="/#diagnose">Tell us what is happening <span class="arrow">&rarr;</span></a></div>'
             f'<div class="diag-aside"><ul><li><a href="/consultants/" {lk}>All consultants</a></li><li><a href="/consultants/{k}/" {lk}>{escape(label)}</a></li><li><a href="/book/" {lk}>Book any partner</a></li></ul></div></div></div></section>')
    meta = {"title": title, "description": desc, "path": prof_url(c), "nav": "consultants", "_head": head, "priority": "0.8", "changefreq": "monthly"}
    return meta, "\n".join(b)

def category_page(k):
    label, short, desc, tags = CAT[k]
    people = by_category()[k]
    title = f"{label} consultants | Mainspring Healthcare Partners"
    b = [f'<div class="container"><p class="crumbs"><a href="/">Home</a> · <a href="/consultants/">Consultants</a> · {escape(short)}</p></div>',
         f'<div class="hero-sub"><div class="container"><p class="eyebrow">Practice area</p><h1>{escape(label)}.</h1><p class="lede">{escape(desc)}</p>'
         '<div class="hero-cta"><a class="btn btn-primary btn-lg" href="/book/">Book a consultation <span class="arrow">&rarr;</span></a><a class="btn btn-ghost btn-lg" href="/#diagnose">Tell us the issue, get matched</a></div>'
         '<div class="ccard-tags big" style="margin-top:1.2rem">' + "".join(f"<span>{escape(t)}</span>" for t in tags) + "</div></div></div>",
         '<section style="padding-top:6px"><div class="container">']
    if people:
        n = len(people)
        b.append(f'<p class="cf-count reveal">{n} consultant{"s" if n != 1 else ""} published in {escape(short.lower())}. Hundreds more in the network, matched by hand.</p><div class="cgrid reveal">' + consultant_cards(only={k}) + "</div>")
    else:
        b.append(f'<div class="prof-empty reveal"><h2>Profiles in {escape(short.lower())} are being published.</h2><p>Consultants appear here as each one approves publication. In the meantime, book a consultation and a partner matches you from the full network, usually the same day.</p>'
                 '<div class="hero-cta"><a class="btn btn-primary" href="/book/">Book a consultation <span class="arrow">&rarr;</span></a><a class="btn btn-ghost" href="/#diagnose">Tell us the issue</a></div></div>')
    b.append("</div></section>")
    b.append('<section style="padding-top:0"><div class="container"><div class="head reveal"><p class="eyebrow">Other practice areas</p><h2 class="h2">Advisors by what the building needs.</h2></div>' + category_tiles(current=k, compact=True) + "</div></section>")
    b.append(f'<section style="padding-top:0"><div class="container"><div class="diag reveal"><div><p class="seclabel">Consultants</p><h2>Work in {escape(short.lower())}? Join the network.</h2>'
             '<p>Defined engagements, scope and rate in writing, Mainspring handles the client and the invoicing. Profiles are published only with your consent.</p><a class="btn btn-on-dark" href="/consultant-network/">Apply to the network <span class="arrow">&rarr;</span></a></div>'
             '<div class="diag-aside"><ul><li>Licensed and placed by state</li><li>Video, phone or in person at the building</li><li>You approve your public profile before it goes live</li></ul></div></div></div></section>')
    meta = {"title": title, "description": desc, "path": f"/consultants/{k}/", "nav": "consultants", "_head": "", "priority": "0.8", "changefreq": "weekly"}
    return meta, "\n".join(b)

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
                    ("consultant_options", consultant_options), ("consultant_categories", category_tiles),
                    ("consultant_category_options", category_options), ("advisor_categories", lambda: category_tiles(compact=True))):
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

    # advisor marketplace: /consultants/<category>/ and /consultants/<slug>/
    for k, *_ in CATEGORIES:
        meta, body = category_page(k)
        paths.append((render(meta, body, template, assetv), meta["priority"], meta["changefreq"]))
    for c in consultants():
        meta, body = profile_page(c)
        paths.append((render(meta, body, template, assetv), meta["priority"], meta["changefreq"]))

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
