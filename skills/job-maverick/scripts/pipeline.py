#!/usr/bin/env python3
"""Job pipeline: pipeline.json is canonical; this renders PIPELINE.md and gaps.md.

Runs in the directory you call it from (the person's project), never inside the plugin.

Usage:
  python3 pipeline.py init                       # create pipeline.json (empty) and an example gaps.json
  python3 pipeline.py render                     # rewrite PIPELINE.md and gaps.md
  python3 pipeline.py add company="X" role="Y" url=... lane=A tier=1 eligible=yes comp="..." gaps=a,b
  python3 pipeline.py set <id> status=applied applied=2026-01-31 next="follow up 2026-02-07"
  python3 pipeline.py list [status]

Statuses: found, triaged, tailoring, drafted, applied, replied, interview, offer, rejected, closed, parked
Tiers: 1 (apply first), 2 (next), 3 (keep warm)
gaps.json maps each gap name to one prep action; unknown gaps render as TODO.
"""
import json
import sys
from dataclasses import dataclass, field, asdict
from datetime import date
from pathlib import Path
from typing import List

PROJECT = Path.cwd()
DB = PROJECT / "pipeline.json"
GAPS_DB = PROJECT / "gaps.json"
TRACKER = PROJECT / "PIPELINE.md"
MATRIX = PROJECT / "gaps.md"

STATUSES = ["offer", "interview", "replied", "applied", "drafted", "tailoring", "triaged", "found",
            "parked", "rejected", "closed"]
ACTIVE = {"found", "triaged", "tailoring", "drafted", "applied", "replied", "interview", "offer"}
TIER_WEIGHT = {1: 3, 2: 2, 3: 1}

EXAMPLE_GAPS = {
    "example-gap": "Replace with the person's gaps: one concrete prep action per gap, e.g. 'Weekend lab on X; write it up.'",
}


@dataclass
class Role:
    id: str
    company: str
    role: str
    url: str = ""
    lane: str = ""
    tier: int = 3
    eligible: str = ""      # local eligibility note (immigration program, licence, on-site), free text
    comp: str = ""          # posted range, with currency
    status: str = "found"
    applied: str = ""
    next: str = ""
    gaps: List[str] = field(default_factory=list)
    notes: str = ""
    resume: str = ""        # path to the tailored resume folder

    @classmethod
    def from_dict(cls, d):
        known = {k: d[k] for k in cls.__dataclass_fields__ if k in d}
        known["tier"] = int(known.get("tier", 3))
        known["gaps"] = list(known.get("gaps") or [])
        return cls(**known)


def load_roles():
    if not DB.exists():
        sys.exit("no pipeline.json here; run `pipeline.py init` in your project directory first")
    return [Role.from_dict(d) for d in json.loads(DB.read_text())]


def save_roles(roles):
    DB.write_text(json.dumps([asdict(r) for r in roles], indent=2, ensure_ascii=False) + "\n")


def load_gap_actions():
    return json.loads(GAPS_DB.read_text()) if GAPS_DB.exists() else {}


def render(roles):
    actions = load_gap_actions()
    order = {s: i for i, s in enumerate(STATUSES)}
    rows = sorted(roles, key=lambda r: (order.get(r.status, 99), r.tier, r.company))
    out = [f"# Job pipeline — rendered {date.today()} from pipeline.json (canonical; edit with pipeline.py)\n",
           "| ID | Company | Role | Lane | Tier | Eligible | Comp | Status | Applied | Next action | Gaps |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        link = f"[{r.role}]({r.url})" if r.url else r.role
        out.append(f"| {r.id} | {r.company} | {link} | {r.lane} | {r.tier} | {r.eligible} | {r.comp} | "
                   f"**{r.status}** | {r.applied} | {r.next} | {', '.join(r.gaps)} |")
    counts = {}
    for r in roles:
        counts[r.status] = counts.get(r.status, 0) + 1
    out.append("\nStatus counts: " + (", ".join(f"{k} {v}" for k, v in sorted(counts.items())) or "none"))
    TRACKER.write_text("\n".join(out) + "\n")

    gaps = {}
    for r in roles:
        if r.status not in ACTIVE:
            continue
        for g in r.gaps:
            entry = gaps.setdefault(g, {"roles": [], "score": 0})
            entry["roles"].append(f"{r.company} (T{r.tier})")
            entry["score"] += TIER_WEIGHT.get(r.tier, 1)
    ranked = sorted(gaps.items(), key=lambda kv: -kv[1]["score"])
    out = [f"# Gap matrix — rendered {date.today()}\n",
           "Which must-haves you miss, how often they block the roles you want (weighted by tier), "
           "and the one prep action per gap (from gaps.json).\n",
           "| Gap | Score | Roles blocked | Prep action |", "|---|---|---|---|"]
    for g, v in ranked:
        out.append(f"| {g} | {v['score']} | {', '.join(v['roles'])} | {actions.get(g, 'TODO: add to gaps.json')} |")
    out.append("\n## This week's prep, by score\n")
    for i, (g, _) in enumerate(ranked[:3], 1):
        out.append(f"{i}. **{g}** — {actions.get(g, 'TODO: add to gaps.json')}")
    MATRIX.write_text("\n".join(out) + "\n")


def parse_kv(args):
    kv = {}
    for a in args:
        k, _, v = a.partition("=")
        if k == "gaps":
            kv[k] = [x for x in v.split(",") if x]
        elif k == "tier":
            kv[k] = int(v)
        else:
            kv[k] = v
    return kv


def main(argv):
    cmd = argv[1] if len(argv) > 1 else "render"
    if cmd == "init":
        if not DB.exists():
            DB.write_text("[]\n")
        if not GAPS_DB.exists():
            GAPS_DB.write_text(json.dumps(EXAMPLE_GAPS, indent=2) + "\n")
        render(load_roles())
        print(f"initialized {DB.name}, {GAPS_DB.name}, {TRACKER.name}, {MATRIX.name} in {PROJECT}")
        return
    roles = load_roles()
    if cmd == "render":
        render(roles)
    elif cmd == "list":
        want = argv[2] if len(argv) > 2 else None
        for r in roles:
            if not want or r.status == want:
                print(f"{r.id:<4} {r.status:<9} T{r.tier} {r.company} — {r.role}")
    elif cmd == "set":
        rid = argv[2]
        kv = parse_kv(argv[3:])
        for r in roles:
            if r.id == rid:
                for k, v in kv.items():
                    if k not in Role.__dataclass_fields__:
                        sys.exit(f"unknown field {k}")
                    setattr(r, k, v)
                break
        else:
            sys.exit(f"no row with id {rid}")
        if kv.get("status") not in (None, *STATUSES):
            sys.exit(f"unknown status; use one of {', '.join(STATUSES)}")
        save_roles(roles)
        render(roles)
    elif cmd == "add":
        kv = parse_kv(argv[2:])
        kv["id"] = f"{len(roles) + 1:02d}"
        roles.append(Role.from_dict(kv))
        save_roles(roles)
        render(roles)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
