---
name: refresh-resume
description: Regenerate index.html and data/resume.pdf from content/resume.yaml after editing the staging data.
---

# Refresh resume

This repo's real content lives in `content/resume.yaml` — a single structured
data file for the resume. `index.html` and `data/resume.pdf` are **generated**
from it via `scripts/build.py` and must never be hand-edited directly; edits
made there get silently overwritten the next time this skill runs.

## When to use

Invoke this skill (`/refresh-resume`) any time `content/resume.yaml` has
changed and the generated `index.html` / `data/resume.pdf` need to catch up —
including just to pick up the automatic date-driven updates. The experience
timeline chart (bar positions/widths), each role's duration text, the current
role's "in progress" label, the axis year ticks, and the nav's career-uptime
badge all recompute from real `start`/`end` dates and today's date on every
run — never from hand-set percentages — so re-running periodically keeps them
current even with zero content edits.

## What it does

1. Ensures Python dependencies are available: `pip install -r requirements.txt`
   (first run only), then `playwright install chromium` (first run only, to
   fetch the headless browser used to print the PDF).
2. Runs `python3 scripts/build.py`, which:
   - Loads `content/resume.yaml`.
   - Computes the experience timeline geometry and durations from each role's
     `start`/`end` dates and today's date.
   - Renders `templates/site.html.j2` → `index.html`.
   - Renders `templates/resume.html.j2` and prints it to `data/resume.pdf` via
     headless Chromium (Playwright).
3. Reports what changed with `git diff --stat` so the result can be reviewed
   before committing.

## Steps

```bash
pip install -r requirements.txt   # first run only
playwright install chromium       # first run only
python3 scripts/build.py
git diff --stat
```

Review the diff (and open `data/resume.pdf` if content changed materially),
then commit as usual. Never edit `index.html` or `data/resume.pdf` by hand —
edit `content/resume.yaml` and rerun this skill instead.
