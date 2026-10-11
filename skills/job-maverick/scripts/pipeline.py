#!/usr/bin/env python3
"""Job pipeline: pipeline.json is canonical; this renders PIPELINE.md and gaps.md.

Usage:
  python3 pipeline.py render                       # rewrite PIPELINE.md and gaps.md
  python3 pipeline.py set <id> status=applied applied=2026-10-12 next="follow up 2026-10-19"
  python3 pipeline.py add company="X" role="Y" url=... lane=A tier=1 bc=yes comp="..." gaps=go,gcp
  python3 pipeline.py list [status]
Statuses: found, triaged, tailoring, drafted, applied, replied, interview, offer, rejected, closed, parked
"""
import json, sys, re
from datetime import date
from pathlib import Path

HERE = Path.cwd()  # pipeline.json, PIPELINE.md and gaps.md live in the project you run this from
DB = HERE / "pipeline.json"

# Each recurring gap maps to one concrete prep action (the coaching plan).
# EXAMPLE entries below; replace with the person's gaps. Unknown gaps render as TODO.
GAP_ACTIONS = {
    "k8s-cluster-ops": "Weekend EKS lab: cluster + node-pool upgrade, requests/limits right-sizing, Kyverno policy. Write it up (Medium post).",
    "go": "Finish whatomate PR #51 (self-hosted models) and ship one small Go CLI; link both on the resume.",
    "gcp": "GCP fundamentals lab: GKE, IAM, Cloud Build; map every AWS skill to its GCP name on the resume.",
    "pulumi": "Port one Terraform module to Pulumi (Python) in a public repo.",
    "rails": "Read Jane's public engineering posts; do a 2-hour Rails security review exercise (strong params, CSRF, Brakeman).",
    "ruby": "Same as rails: enough Ruby to review a PR.",
    "scala-java": "Refresh Java (you have 2013–2018): one Spring Boot service with tests; mention in interviews, not on the resume.",
    "ebpf": "Read Tigera/Calico eBPF docs; run one bpftrace example. Interview talking point only.",
    "k8s-networking": "NetworkPolicy + Gateway API lab on the same EKS cluster as k8s-cluster-ops.",
    "argocd": "Deploy the EKS lab app with ArgoCD (GitOps); 2 hours.",
    "detection-response": "Not your core; only pursue if the role is otherwise ideal. Prep: GuardDuty/SIEM story as detection engineering.",
    "incident-response": "Prep the GuardDuty incident as an IR narrative (timeline, containment, lessons).",
    "offensive-security": "Skip unless the role is reframed; your profile is defensive/AppSec.",
    "amazon-loop-prep": "Write 8 Leadership Principle stories from the STAR set; practice bar-raiser style questions.",
    "enterprise-hr-domain": "Map FinTech data-governance work to HR/finance data constraints; no prep beyond talking points.",
    "salary-below-floor": "Decide before applying: exception only with equity and a path to the floor within 12 months.",
    "location-eligibility": "Confirm Canada/BC eligibility with the recruiter before tailoring.",
    "strategy-role": "Not a builder role; keep warm as a fallback, don't tailor.",
    "program-level": "Same as strategy-role.",
    "gtm-domain": "GTM automation agents; weak fit, keep warm.",
    "us-hq-remote": "Remote for a US HQ: pays well, does not qualify for BC PNP. Fine as a backup.",
}

ACTIVE = {"found", "triaged", "tailoring", "drafted", "applied", "replied", "interview", "offer"}


def load():
    return json.loads(DB.read_text()) if DB.exists() else []


def save(rows):
    DB.write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n")


def render(rows):
    order = {"interview": 0, "replied": 1, "applied": 2, "drafted": 3, "tailoring": 4, "triaged": 5, "found": 6,
             "offer": -1, "parked": 7, "rejected": 8, "closed": 9}
    rows_sorted = sorted(rows, key=lambda r: (order.get(r["status"], 9), r.get("tier", 9), r["company"]))
    out = [f"# Job pipeline — rendered {date.today()} from pipeline.json (canonical; edit with pipeline.py)\n",
           "| ID | Company | Role | Lane | Tier | BC | Comp (CAD) | Status | Applied | Next action | Gaps |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows_sorted:
        out.append(f"| {r['id']} | {r['company']} | [{r['role']}]({r['url']}) | {r['lane']} | {r.get('tier','')} | {r.get('bc','')} | {r.get('comp','')} | **{r['status']}** | {r.get('applied','')} | {r.get('next','')} | {', '.join(r.get('gaps', []))} |")
    counts = {}
    for r in rows:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    out.append("\nStatus counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    (HERE / "PIPELINE.md").write_text("\n".join(out) + "\n")

    # Gap matrix over active roles, weighted by tier (tier 1 counts 3, tier 2 counts 2, tier 3 counts 1)
    weight = {1: 3, 2: 2, 3: 1}
    gaps = {}
    for r in rows:
        if r["status"] not in ACTIVE:
            continue
        for g in r.get("gaps", []):
            gaps.setdefault(g, {"roles": [], "score": 0})
            gaps[g]["roles"].append(f"{r['company']} (T{r.get('tier','?')})")
            gaps[g]["score"] += weight.get(r.get("tier"), 1)
    out = [f"# Gap matrix — rendered {date.today()}\n",
           "Which must-haves you miss, how often they block the roles you want (weighted by tier), and the one prep action per gap.\n",
           "| Gap | Score | Roles blocked | Prep action |", "|---|---|---|---|"]
    for g, v in sorted(gaps.items(), key=lambda kv: -kv[1]["score"]):
        out.append(f"| {g} | {v['score']} | {', '.join(v['roles'])} | {GAP_ACTIONS.get(g, 'TODO')} |")
    top = [g for g, _ in sorted(gaps.items(), key=lambda kv: -kv[1]["score"])[:3]]
    out.append("\n## This week's prep, by score\n")
    for i, g in enumerate(top, 1):
        out.append(f"{i}. **{g}** — {GAP_ACTIONS.get(g, 'TODO')}")
    (HERE / "gaps.md").write_text("\n".join(out) + "\n")


def parse_kv(args):
    kv = {}
    for a in args:
        k, _, v = a.partition("=")
        kv[k] = v.split(",") if k == "gaps" else v
    return kv


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "render"
    rows = load()
    if cmd == "render":
        render(rows)
    elif cmd == "list":
        want = sys.argv[2] if len(sys.argv) > 2 else None
        for r in rows:
            if not want or r["status"] == want:
                print(f"{r['id']:<4} {r['status']:<9} T{r.get('tier','?')} {r['company']} — {r['role']}")
    elif cmd == "set":
        rid = sys.argv[2]
        kv = parse_kv(sys.argv[3:])
        for r in rows:
            if r["id"] == rid:
                r.update(kv)
                break
        else:
            sys.exit(f"no row with id {rid}")
        save(rows); render(rows)
    elif cmd == "add":
        kv = parse_kv(sys.argv[2:])
        kv.setdefault("status", "found"); kv.setdefault("gaps", [])
        kv["tier"] = int(kv.get("tier", 3))
        kv["id"] = f"{len(rows)+1:02d}"
        rows.append(kv); save(rows); render(rows)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
