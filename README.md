# Job Maverick

A Claude Code skill for accomplished professionals who have never had to sell themselves: a dozen gold medals, no idea how to thrive in today's market. Engineers, nurses, accountants, building managers, teachers, analysts.

It coaches rather than fills forms. It starts from your current resume, quizzes you for the numbers behind your work, verifies them, positions you, and cuts a 2-page resume per posting. You click Submit.

## What it produces
- `profile.md` - profession, level, market, licensing, constraints (drafted from your resume)
- `brag-document.md` - every achievement with a number and a source
- `master-resume.md` - the comprehensive superset, ATS-clean
- `targets.md`, `pipeline.json`, `PIPELINE.md` - lanes, triaged roles, status
- `compensation.md` - posted bands, a walk-away floor, an anchor
- `applications/<slug>/` - strategy + tailored resume per posting
- `gaps.md` - the must-haves you miss, weighted, each with one prep action
- `linkedin-profile.md` - every field drafted offline, applied in your own browser

## Install

Claude Code plugin (one step on Claude Code 2.1.275 or later):

```
/plugin install job-maverick --marketplace ernestomancebo/job-maverick
```

Agent Skills CLI (any compatible agent):

```
npx skills add ernestomancebo/job-maverick
```

Or copy `skills/job-maverick/` into `~/.claude/skills/` (or your project's `.claude/skills/`), or upload that folder as a Skill in claude.ai. Then start with "here is my resume, help me with my job search".

## Requirements
- Python 3.9+ for the scripts (standard library only).
- Optional, for PDF builds: pandoc, LibreOffice, poppler (`pdftotext`). Without them the skill produces Markdown resumes. Set `RESUME_TEMPLATE` to a reference `.docx` for styling.

## Safety notes
- `scripts/jobs-scan.py` makes outbound HTTPS requests to three public job-board APIs (Ashby, Greenhouse, Lever) and nothing else.
- All scripts read and write files in the directory you run them from. Nothing is sent anywhere.
- The skill never submits applications, bypasses bot checks, or logs into sites for you.

## Principles
1. Facts over phrasing: nothing goes on a resume without a source.
2. One master, many cuts: tailored resumes are cuts, never rewrites.
3. The person clicks Submit.
4. Never quote a floor below the posted bands.
5. State lives in files; the skill survives a model switch.
6. The profession is an input: see `references/evidence-by-profession.md` and the three worked examples under `examples/`.

## Markets
`references/markets/canada.md` and `usa.md` ship. Add a file for yours (format rules, pay transparency, work authorization, regulated-profession steps) and name it in `profile.md`.

## Status
Extracted from a real search (Vancouver, 2026), then generalized. Issues and market files welcome.

## License
MIT
