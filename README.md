# Job Maverick

A Claude Code skill for accomplished professionals who have never had to sell themselves: a dozen gold medals, no idea how to thrive in today's market.

It coaches rather than fills forms. It quizzes, verifies, positions; the person clicks Submit.

## What it produces
- `brag-document.md` - every achievement with a number and a source
- `master-resume.md` - the comprehensive superset, ATS-clean
- `targets.md`, `pipeline.json`, `PIPELINE.md` - lanes, triaged roles, status
- `compensation.md` - posted bands, a walk-away floor, an anchor
- `applications/<slug>/` - strategy + 2-page tailored resume per posting
- `gaps.md` - the must-haves you miss, weighted, each with one prep action
- `linkedin-profile.md` - every field drafted offline, applied in your own browser

## Install

As a Claude Code plugin (one step on Claude Code 2.1.275 or later):

```
/plugin install job-maverick --marketplace ernestomancebo/job-maverick
```

Or as a plain skill: copy `skills/job-maverick/` into `~/.claude/skills/` (or your project's `.claude/skills/`), or upload the same folder as a Skill in claude.ai. Then start a session with "help me with my job search".

Scripts need Python 3.9+; `build-resume.sh` needs pandoc, LibreOffice and poppler (`pdftotext`). Set `RESUME_TEMPLATE` to a reference `.docx` for styling.

## Principles
1. Facts over phrasing: nothing goes on a resume without a source.
2. One master, many cuts: tailored resumes are 2-page cuts, never rewrites.
3. The person clicks Submit. No scraping, no bot bypass, no form submission.
4. Never quote a floor below the posted bands.
5. State lives in files; the skill survives a model switch.

## Status
Extracted from a real search (Vancouver, 2026). Market rules currently cover Canada; add a file under `references/` for another market.

## License
MIT
