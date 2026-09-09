# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

`rhp4515.github.io` is a personal résumé/landing page served directly by GitHub Pages (user-site repos are published from the root of the default branch with no build step at deploy time). The site itself is one self-contained HTML file with all CSS inline and no external JS — but that file, and the matching `data/resume.pdf`, are **generated** from a single structured data file rather than hand-written.

## Repository layout

- `content/resume.yaml` — **the single source of truth.** All résumé content (profile text, experience roles with real `start`/`end` dates, leadership highlights, work highlights, toolkit, education, contact links) lives here. Edit this file for any content change.
- `templates/site.html.j2` — Jinja2 template for the public dark "developer console"-themed page. Renders to `index.html`.
- `templates/resume.html.j2` — Jinja2 template for a separate, traditional black-on-white ATS-friendly resume layout (serif font, Education → Technical Skills → Work Experience → Research Experience, roles grouped by company). Renders to `data/resume.pdf` via headless Chromium.
- `scripts/build.py` — loads `content/resume.yaml`, computes the experience-timeline geometry (bar positions/widths, "Xy"/"Xmo" durations, axis year ticks, the nav's career-uptime badge) from real dates and today's date, then renders both templates.
- `index.html` and `data/resume.pdf` — **generated output.** Do not hand-edit either; edits are silently overwritten on the next build. Both are still committed to git (GitHub Pages serves `index.html` as-is; `data/resume.pdf` needs to exist as a real file to be downloadable).
- `requirements.txt` — `pyyaml`, `jinja2`, `playwright` (needed by `scripts/build.py`).
- `.claude/skills/refresh-resume/SKILL.md` — the `/refresh-resume` skill; wraps the build command below.
- `LICENSE` — MIT.

There is no `CNAME` file, so the site serves at `rhp4515.github.io` (not a custom domain).

## Making a content change

1. Edit `content/resume.yaml`.
2. Regenerate: `python3 scripts/build.py` (or invoke the `refresh-resume` skill). First-time setup: `pip install -r requirements.txt && playwright install chromium`.
3. Review `git diff` on `index.html` and open `data/resume.pdf` if the change was substantial.
4. Commit `content/resume.yaml` together with the regenerated `index.html` / `data/resume.pdf` — they should never drift apart.

Because the experience timeline and the nav's "uptime" badge are computed from real dates vs. today, re-running the build periodically (even with zero content edits) keeps those numbers current — that's the point of the pipeline being date-driven rather than hand-tuned percentages.

## Design notes

- The website (`templates/site.html.j2`) and the PDF (`templates/resume.html.j2`) intentionally look nothing alike: the website is a stylized dark "API/developer console" concept (CSS custom properties for the "Nocturne" dark palette, monospace route-style section headers, an ingestion-pipeline diagram, a Gantt-style experience trace chart), while the PDF mirrors a conventional serif resume format for ATS/recruiter readability. Keep that split — don't try to make one a snapshot of the other.
- In `templates/site.html.j2`, the trace-panel header date (`{{ trace_meta }}`) intentionally uses abbreviated-month formatting (e.g. "2013-Jul"), while each role card's own date range (`{{ role.dates_text }}`) intentionally stays numeric ("2013-07") — this was a deliberate, explicit choice, not an inconsistency to "fix."
- `scripts/build.py`'s `build_experience_groups()` groups consecutive same-company role spans for the PDF only (matching how multiple Bloomberg roles are meant to nest under one company heading) — the website's timeline renders every span as its own row instead.
- Previewing the website locally: `python3 -m http.server` from the repo root, then visit `http://localhost:8000`.
- History note: the site previously (see `4f9b4e5`) was just a redirect stub pointing to an external Stony Brook `fsl.cs.stonybrook.edu` page; that's long obsolete.
