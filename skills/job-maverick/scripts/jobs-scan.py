#!/usr/bin/env python3
"""Scan first-party job boards (Ashby, Greenhouse, Lever public JSON APIs) for matching openings.

Runs in the directory you call it from. Configuration lives in boards.json there, never in this file.

Usage:
  python3 jobs-scan.py init          # write an example boards.json
  python3 jobs-scan.py scan [--all]  # print a Markdown table; --all ignores the title/topic filters

boards.json:
  {
    "ashby": ["company-slug", ...],        # https://jobs.ashbyhq.com/<slug>
    "greenhouse": ["company-slug", ...],   # https://job-boards.greenhouse.io/<slug>
    "lever": ["company-slug", ...],        # https://jobs.lever.co/<slug>
    "title_pattern": "...",                # regex, case-insensitive, word-bounded; level words
    "topic_pattern": "...",                # regex, case-insensitive, word-bounded; specialty words
    "location_pattern": "..."              # regex, case-insensitive; where you can work
  }

Coverage is limited to employers on those three boards (mostly technology companies and startups).
Hospitals, school districts, public bodies and most property firms post elsewhere; search those directly.
Outbound HTTPS only to api.ashbyhq.com, boards-api.greenhouse.io and api.lever.co.
"""
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

CONFIG = Path.cwd() / "boards.json"

EXAMPLE_CONFIG = {
    "ashby": ["example-company"],
    "greenhouse": ["example-company"],
    "lever": ["example-company"],
    "title_pattern": r"senior|lead|principal|manager|director",
    "topic_pattern": r"nurse|nursing|accountant|finance|facilities|property|teacher|engineer|security|platform",
    "location_pattern": r"canada|remote",
}


@dataclass
class Job:
    board: str
    company: str
    title: str
    location: str
    remote: bool
    comp: str
    url: str
    posted: str


def fetch_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "job-maverick-scan/0.2"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def ashby(slug):
    data = fetch_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    for j in data.get("jobs", []):
        comp = (j.get("compensation") or {}).get("compensationTierSummary") or ""
        yield Job("ashby", slug, j["title"], j.get("location", ""), bool(j.get("isRemote")), comp,
                  j.get("jobUrl", ""), (j.get("publishedAt") or "")[:10])


def greenhouse(slug):
    data = fetch_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    for j in data.get("jobs", []):
        yield Job("greenhouse", slug, j["title"], (j.get("location") or {}).get("name", ""), False, "",
                  j.get("absolute_url", ""), (j.get("updated_at") or "")[:10])


def lever(slug):
    data = fetch_json(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    for j in data:
        loc = (j.get("categories") or {}).get("location", "") or ""
        posted = datetime.fromtimestamp(j.get("createdAt", 0) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")
        yield Job("lever", slug, j["text"], loc, "remote" in loc.lower(), "", j.get("hostedUrl", ""), posted)


FETCHERS = {"ashby": ashby, "greenhouse": greenhouse, "lever": lever}


def word_bounded(pattern):
    # Each alternative gets word boundaries so "ai" does not match "Retail".
    alts = [a.strip() for a in pattern.split("|") if a.strip()]
    return re.compile(r"\b(?:" + "|".join(alts) + r")\b", re.I)


def scan(cfg, show_all):
    title_re = word_bounded(cfg.get("title_pattern", ""))
    topic_re = word_bounded(cfg.get("topic_pattern", ""))
    loc_re = re.compile(cfg.get("location_pattern", "."), re.I)
    rows, errors = [], []
    for board, fetch in FETCHERS.items():
        for slug in cfg.get(board, []):
            try:
                for job in fetch(slug):
                    if not (loc_re.search(job.location) or job.remote):
                        continue
                    if show_all or (title_re.search(job.title) and topic_re.search(job.title)):
                        rows.append(job)
            except urllib.error.HTTPError as e:
                errors.append(f"{board}/{slug}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001 - report and continue
                errors.append(f"{board}/{slug}: {type(e).__name__}")
    rows.sort(key=lambda j: (j.company, j.title))
    print(f"# Board scan {datetime.now():%Y-%m-%d} — {len(rows)} matches\n")
    print("| Board | Company | Title | Location | Comp | Posted | Link |\n|---|---|---|---|---|---|---|")
    for j in rows:
        loc = j.location + (" (remote)" if j.remote else "")
        print(f"| {j.board} | {j.company} | {j.title} | {loc} | {j.comp} | {j.posted} | {j.url} |")
    if errors:
        print("\nBoards not found or failed (slug may be wrong): " + ", ".join(errors))


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "scan"
    if cmd == "init":
        if CONFIG.exists():
            sys.exit(f"{CONFIG.name} already exists; edit it instead")
        CONFIG.write_text(json.dumps(EXAMPLE_CONFIG, indent=2) + "\n")
        print(f"wrote {CONFIG}; edit the slugs and patterns, then run `jobs-scan.py scan`")
    elif cmd == "scan":
        if not CONFIG.exists():
            sys.exit("no boards.json here; run `jobs-scan.py init` first")
        scan(json.loads(CONFIG.read_text()), "--all" in argv)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
