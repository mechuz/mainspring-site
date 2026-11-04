#!/usr/bin/env python3
"""Collect skilled nursing / senior living headlines AND regulatory news into content/news_feeds.json.

Runs in GitHub Actions (deploy.yml before each build, and refresh-news-feeds.yml
on a schedule). build.py turns the file into the /industry/ page, so the
headlines are real HTML — no server, no client-side fetch, and search engines
see them. Standard library only.

Only the headline, publisher, date and link are kept: the stories belong to
their publishers and every headline links straight to the original. A feed that
fails is recorded in "sources" and skipped, so one broken feed never empties the
page.

    python3 scripts/fetch_news_feeds.py [--out content/news_feeds.json]
"""
import datetime as dt
import email.utils
import html
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "news_feeds.json"
UA = "Mozilla/5.0 (compatible; MainspringNewsBot/1.0; +https://mainspringhcp.com/industry/)"
MAX_AGE_DAYS = 21
MAX_ITEMS = 24
PER_SOURCE = 8

# Verified Oct 30 + Nov 4 2026. McKnight's and HHS news are absent (403 to
# datacenter IPs); LeadingAge's feed stopped updating in 2022; OIG publishes no
# RSS. DOJ is filtered by topic and is legitimately empty on quiet days.
SOURCES = [
    # name, feed urls, home, group, topic filter (None = keep everything)
    ("Skilled Nursing News", ["https://skillednursingnews.com/feed/"], "https://skillednursingnews.com", "industry", None),
    ("Senior Housing News", ["https://seniorhousingnews.com/feed/"], "https://seniorhousingnews.com", "industry", None),
    ("Home Health Care News", ["https://homehealthcarenews.com/feed/"], "https://homehealthcarenews.com", "industry", None),
    ("CMS Newsroom", ["https://www.cms.gov/newsroom/rss-feeds"], "https://www.cms.gov", "regulatory", None),
    ("Federal Register \u00b7 CMS", ["https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bagencies%5D%5B%5D=centers-for-medicare-medicaid-services&order=newest"], "https://www.federalregister.gov", "regulatory", None),
    ("Federal Register \u00b7 Nursing homes", ["https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bterm%5D=nursing+home&order=newest"], "https://www.federalregister.gov", "regulatory",
     r"nursing|long-term care|skilled nursing|assisted living|hospice|home health|medicare|medicaid|civil money|survey|certification|staffing|minimum staff|resident"),
    ("Federal Register \u00b7 Long-term care", ["https://www.federalregister.gov/api/v1/documents.rss?conditions%5Bterm%5D=long-term+care+facilities&conditions%5Bagencies%5D%5B%5D=centers-for-medicare-medicaid-services&order=newest"], "https://www.federalregister.gov", "regulatory",
     r"nursing|long-term care|skilled nursing|assisted living|hospice|home health|medicare|medicaid|civil money|survey|certification|staffing|minimum staff|resident"),
    ("U.S. Department of Justice", ["https://www.justice.gov/news/rss?type=press_release"], "https://www.justice.gov", "regulatory",
     r"nursing home|nursing facilit|skilled nursing|long-term care|assisted living|hospice|home health|medicare|medicaid|elder|senior living"),
]


def clean(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]*>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def parse_date(s, block=""):
    s = (s or "").strip()
    for attempt in (s,):
        if not attempt:
            break
        try:
            d = email.utils.parsedate_to_datetime(attempt)
        except (TypeError, ValueError):
            try:
                d = dt.datetime.fromisoformat(attempt.replace("Z", "+00:00"))
            except ValueError:
                d = None
        if d:
            return d.replace(tzinfo=d.tzinfo or dt.timezone.utc).astimezone(dt.timezone.utc)
    # CMS emits "Fri, 10/30/2026 - 08:31" and carries an ISO <time datetime=...>
    iso = re.search(r'datetime="(\d{4}-\d{2}-\d{2}T[^"]+)"', block)
    if iso:
        try:
            return dt.datetime.fromisoformat(iso.group(1)).astimezone(dt.timezone.utc)
        except ValueError:
            pass
    m = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})(?:\s*-\s*(\d{1,2}):(\d{2}))?", s)
    if m:
        return dt.datetime(int(m.group(3)), int(m.group(1)), int(m.group(2)),
                           int(m.group(4) or 12), int(m.group(5) or 0), tzinfo=dt.timezone.utc)
    return None


def item_blocks(data):
    text = data.decode("utf-8", "replace")
    return re.findall(r"<(item|entry)[\s>][\s\S]*?</\1>", text, re.I)


def parse_feed(data, home):
    """[(title, link, datetime|None)] from RSS or Atom bytes."""
    out = []
    try:
        root = ET.fromstring(data)
    except ET.ParseError:
        root = None
    blocks = [b[0] if isinstance(b, tuple) else b for b in
              re.findall(r"(<(?:item|entry)[\s>][\s\S]*?</(?:item|entry)>)",
                         data.decode("utf-8", "replace"), re.I)]
    for block in blocks:
        t = re.search(r"<title[^>]*>([\s\S]*?)</title>", block, re.I)
        title = clean(t.group(1)) if t else ""
        link = ""
        l = re.search(r"<link[^>]*>([\s\S]*?)</link>", block, re.I)
        if l:
            link = clean(l.group(1))
        if not link or "%3Ca" in link or "<a " in link.lower():
            href = re.search(r'href="([^"]+)"', html.unescape(t.group(1)) if t else "")
            if not href:
                href = re.search(r'<link[^>]*href="([^"]+)"', block, re.I)
            if href:
                h = href.group(1)
                link = h if h.startswith("http") else home.rstrip("/") + "/" + h.lstrip("/")
        d = re.search(r"<(pubDate|published|updated|dc:date)[^>]*>([\s\S]*?)</\1>", block, re.I)
        when = parse_date(clean(d.group(2)) if d else "", block)
        if title and link.startswith(("http://", "https://")):
            out.append((title, link, when))
    return out


def fetch(url):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.5"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def collect(now):
    cutoff = now - dt.timedelta(days=MAX_AGE_DAYS)
    sources, per_source, seen = [], [], set()
    for name, urls, home, group, topic in SOURCES:
        entries, used, error = None, None, ""
        for url in urls:
            try:
                entries, used = parse_feed(fetch(url), home), url
                break
            except Exception as e:  # noqa: BLE001 — any failure just skips the feed
                error = f"{type(e).__name__}: {e}"[:200]
        if entries is None:
            sources.append({"name": name, "url": urls[0], "ok": False, "count": 0, "error": error})
            per_source.append([])
            continue
        kept = []
        topic_re = re.compile(topic, re.I) if topic else None
        for title, link, when in entries:
            if len(kept) >= PER_SOURCE:
                break
            if when is None or when < cutoff or when > now + dt.timedelta(days=1):
                continue
            if topic_re and not topic_re.search(title):
                continue
            key = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
            if key in seen or len(title) < 15:
                continue
            seen.add(key)
            kept.append({"title": title[:200], "link": link, "source": name, "group": group,
                         "published": when.strftime("%Y-%m-%dT%H:%M:%SZ")})
        kept.sort(key=lambda i: i["published"], reverse=True)
        per_source.append(kept)
        sources.append({"name": name, "url": used, "ok": True, "count": len(kept), "error": "", "group": group})

    # round-robin inside each group, so no single publisher fills a section
    def interleave(group):
        lists = [l for l in per_source if l and l[0]["group"] == group]
        out = []
        for i in range(PER_SOURCE):
            for lst in lists:
                if i < len(lst):
                    out.append(lst[i])
        return out[:MAX_ITEMS]
    return {"fetched_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "sources": sources,
            "items": interleave("industry"), "regulatory": interleave("regulatory")}


def main(argv):
    out, args = OUT, argv[1:]
    while args:
        a = args.pop(0)
        if a == "--out":
            out = Path(args.pop(0))
        else:
            print(__doc__)
            return 2
    result = collect(dt.datetime.now(dt.timezone.utc))
    for s in result["sources"]:
        print(f"{'ok ' if s['ok'] else 'ERR'} {s['name']}: {s['count'] if s['ok'] else s['error']}")
    if not result["items"] and not result["regulatory"] and out.exists():
        print("no headlines collected; keeping the previous file")
        return 0
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    ok = sum(1 for s in result["sources"] if s["ok"])
    print(f"{len(result['items'])} industry + {len(result['regulatory'])} regulatory headlines from {ok} of {len(result['sources'])} feeds -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
