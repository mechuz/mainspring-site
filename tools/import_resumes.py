#!/usr/bin/env python3
"""Draft consultant profiles from a private folder of résumés.

Usage:
    python3 tools/import_resumes.py ~/path/to/resumes  [--out content/consultants.drafts.json]

Reads every .pdf, .docx and .txt in the folder, extracts the text, and writes one
DRAFT profile per file with "published": false. Drafts are reviewed by hand (name,
title, states, specialties, bio, consent) and then moved into content/consultants.json.
Nothing from the résumés themselves is published: the public site only ever shows the
reviewed fields in consultants.json. Keep the résumé folder OUTSIDE this public repo.
"""
import json, re, subprocess, sys, zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

SPECIALTY_WORDS = {
    "Survey remediation": ["survey", "plan of correction", "deficienc", "immediate jeopardy", "compliance"],
    "Interim leadership": ["interim", "administrator", "executive director", "nursing home administrator", "nha"],
    "Clinical operations": ["director of nursing", "don ", "rn ", "nurse", "clinical"],
    "Restructuring": ["turnaround", "restructur", "labor", "ppd", "agency"],
    "Budgeting & financial analysis": ["budget", "p&l", "financial", "cfo", "controller"],
    "Census growth": ["census", "admissions", "referral", "marketing", "business development"],
    "Capital projects": ["renovation", "construction", "capital", "life safety", "maintenance"],
    "Temporary management": ["receiver", "temporary manag", "monitor", "court"],
}
SETTING_WORDS = {
    "Skilled nursing": ["skilled nursing", "snf", "nursing home", "rehab"],
    "Assisted living": ["assisted living", "alf"],
    "Memory care": ["memory care", "dementia"],
    "CCRC": ["ccrc", "life plan", "continuing care"],
    "Independent living": ["independent living"],
}
STATE_RE = re.compile(r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b")


def text_of(path: Path) -> str:
    suf = path.suffix.lower()
    if suf == ".txt":
        return path.read_text(errors="ignore")
    if suf == ".docx":
        with zipfile.ZipFile(path) as z:
            root = ET.fromstring(z.read("word/document.xml"))
        ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        return "\n".join("".join(t.text or "" for t in p.iter(ns + "t")) for p in root.iter(ns + "p"))
    if suf == ".pdf":
        swift = ('import Foundation; import PDFKit; let u = URL(fileURLWithPath: CommandLine.arguments[1]); '
                 'if let d = PDFDocument(url: u) { print(d.string ?? "") }')
        try:
            return subprocess.run(["swift", "-e", swift, str(path)], capture_output=True, text=True, timeout=120).stdout
        except Exception:
            return ""
    return ""


def slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def draft(path: Path) -> dict:
    txt = text_of(path)
    low = txt.lower()
    first = next((ln.strip() for ln in txt.splitlines() if ln.strip()), path.stem)
    name = first if len(first) < 60 else path.stem.replace("_", " ").replace("-", " ")
    years = re.findall(r"(\d{2})\+?\s+years", low)
    return {
        "slug": slugify(name),
        "name": name,
        "title": "",
        "role": "",
        "credentials": ["Licensed Nursing Home Administrator"] if ("nursing home administrator" in low or re.search(r"\bnha\b", low)) else [],
        "states": sorted(set(STATE_RE.findall(txt)))[:8],
        "specialties": [k for k, ws in SPECIALTY_WORDS.items() if any(w in low for w in ws)],
        "settings": [k for k, ws in SETTING_WORDS.items() if any(w in low for w in ws)],
        "years": int(years[0]) if years else None,
        "modes": ["video", "phone", "in-person"],
        "bio": "",
        "source_file": path.name,
        "excerpt_for_review": re.sub(r"\s+", " ", txt)[:1200],
        "consent_to_publish": False,
        "published": False,
    }


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    folder = Path(sys.argv[1]).expanduser()
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else Path("content/consultants.drafts.json")
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() in (".pdf", ".docx", ".txt"))
    drafts = [draft(p) for p in files]
    out.write_text(json.dumps(drafts, indent=2, ensure_ascii=False))
    print(f"{len(drafts)} draft profiles -> {out}  (review, then move approved ones into content/consultants.json)")


if __name__ == "__main__":
    main()
