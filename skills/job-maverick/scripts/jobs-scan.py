#!/usr/bin/env python3
"""Scan first-party ATS boards (Ashby, Greenhouse, Lever) for matching openings.

Usage: python3 jobs-scan.py [--all]   # prints a markdown table; --all ignores the title filter
Edit BOARDS to add companies. No scraping of Indeed/LinkedIn: these are public JSON APIs.
"""
import json, os, re, sys, urllib.request, urllib.error
from datetime import datetime

BOARDS = {
    # Example slugs; replace with the boards for your target companies.
    "ashby": ["jane", "1password", "cohere", "klue"],
    "greenhouse": ["affirm", "tailscale", "grafanalabs", "databricks", "gitlab", "tigera"],
    "lever": ["fullscript"],
}

TITLE_RE = re.compile(r"(staff|principal|lead|senior staff|head of)", re.I)
TOPIC_RE = re.compile(r"(security|devops|devsecops|platform|sre|infrastructure|ai|ml|machine learning|llm|agent|backend|compliance)", re.I)
LOC_RE = re.compile(os.environ.get("JOBS_LOC_RE", r"(canada|remote)"), re.I)  # set JOBS_LOC_RE for your market


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "jobs-scan/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def ashby(slug):
    data = get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true")
    for j in data.get("jobs", []):
        comp = (j.get("compensation") or {}).get("compensationTierSummary") or ""
        yield dict(company=slug, title=j["title"], location=j.get("location", ""),
                   remote=j.get("isRemote", False), comp=comp, url=j.get("jobUrl"),
                   posted=(j.get("publishedAt") or "")[:10])


def greenhouse(slug):
    data = get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs")
    for j in data.get("jobs", []):
        yield dict(company=slug, title=j["title"], location=(j.get("location") or {}).get("name", ""),
                   remote=False, comp="", url=j.get("absolute_url"), posted=(j.get("updated_at") or "")[:10])


def lever(slug):
    data = get(f"https://api.lever.co/v0/postings/{slug}?mode=json")
    for j in data:
        cat = j.get("categories") or {}
        yield dict(company=slug, title=j["text"], location=cat.get("location", ""),
                   remote="remote" in (cat.get("location") or "").lower(), comp="", url=j.get("hostedUrl"),
                   posted=datetime.utcfromtimestamp(j.get("createdAt", 0) / 1000).strftime("%Y-%m-%d"))


def main():
    show_all = "--all" in sys.argv
    rows, errors = [], []
    for kind, slugs in BOARDS.items():
        fn = {"ashby": ashby, "greenhouse": greenhouse, "lever": lever}[kind]
        for slug in slugs:
            try:
                for j in fn(slug):
                    loc_ok = LOC_RE.search(j["location"] or "") or j["remote"]
                    if not loc_ok:
                        continue
                    if show_all or (TITLE_RE.search(j["title"]) and TOPIC_RE.search(j["title"])):
                        j["ats"] = kind
                        rows.append(j)
            except urllib.error.HTTPError as e:
                errors.append(f"{kind}/{slug}: HTTP {e.code}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{kind}/{slug}: {type(e).__name__}")
    rows.sort(key=lambda r: (r["company"], r["title"]))
    print(f"# ATS scan {datetime.now():%Y-%m-%d} — {len(rows)} matches\n")
    print("| Company | Title | Location | Comp | Posted | Link |\n|---|---|---|---|---|---|")
    for r in rows:
        print(f"| {r['company']} | {r['title']} | {r['location']}{' (remote)' if r['remote'] else ''} | {r['comp']} | {r['posted']} | {r['url']} |")
    if errors:
        print("\nBoards not found or failed (slug may be wrong): " + ", ".join(errors))


if __name__ == "__main__":
    main()
