#!/usr/bin/env python3
"""Regenerate ../index.html and ../data/resume.pdf from ../content/resume.yaml.

Usage: python3 scripts/build.py
"""

import datetime as dt
import pathlib
import sys

import jinja2
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
CONTENT_FILE = ROOT / "content" / "resume.yaml"
TEMPLATES_DIR = ROOT / "templates"
OUT_HTML = ROOT / "index.html"
OUT_PDF = ROOT / "data" / "resume.pdf"

OUTSIDE_LABEL_THRESHOLD_PCT = 6  # bars narrower than this get their duration label outside


def parse_month(value: str) -> dt.date:
    year, month = (int(part) for part in value.split("-"))
    return dt.date(year, month, 1)


def month_end(value: str) -> dt.date:
    """Last day of the given 'YYYY-MM' month (inclusive end of an employment span)."""
    year, month = (int(part) for part in value.split("-"))
    if month == 12:
        return dt.date(year, 12, 31)
    return dt.date(year, month + 1, 1) - dt.timedelta(days=1)


def duration_years(start: dt.date, end: dt.date) -> float:
    return (end - start).days / 365.25


def format_duration(start: dt.date, end: dt.date) -> str:
    years = duration_years(start, end)
    if years < 1:
        months = max(1, round(years * 12))
        return f"{months}mo"
    return f"{years:.1f}y"


def format_month_abbrev(value: str) -> str:
    """'2022-03' -> 'Mar 2022', for the PDF's traditional-resume date style."""
    return parse_month(value).strftime("%b %Y")


def split_company_location(org_line: str) -> tuple[str, str]:
    company, _, location = org_line.partition(", ")
    return company, location


def build_experience_groups(spans_raw: list[dict], today: dt.date) -> list[dict]:
    """Group consecutive same-company role spans for the PDF's traditional
    resume layout (one company heading, multiple role sub-entries beneath
    it) — mirrors how the original hand-written resume.pdf presented
    multiple Bloomberg roles under a single "Bloomberg LP" heading."""
    roles = [s for s in spans_raw if s["kind"] == "role"]

    groups: list[dict] = []
    for role in roles:
        company, location = split_company_location(role["org_line"])
        start = parse_month(role["start"])
        end = today if not role.get("end") else parse_month(role["end"])
        entry = {
            "job_title": role["short_title"],
            "location": location,
            "pdf_dates": f"{format_month_abbrev(role['start'])} – "
                         f"{'Present' if not role.get('end') else format_month_abbrev(role['end'])}",
            "facts": [tuple(fact) for fact in role["facts"]],
            "_start": start,
            "_end": end,
        }
        if groups and groups[-1]["company"] == company:
            groups[-1]["roles"].append(entry)
        else:
            groups.append({"company": company, "location": location, "roles": [entry]})

    for group in groups:
        starts = [r["_start"] for r in group["roles"]]
        ends = [r["_end"] for r in group["roles"]]
        group["pdf_dates"] = (
            f"{min(starts).strftime('%b %Y')} – "
            f"{'Present' if today in ends else max(ends).strftime('%b %Y')}"
        )
        for r in group["roles"]:
            del r["_start"], r["_end"]

    return groups


def build_experience(data: dict, today: dt.date) -> dict:
    spans_raw = data["experience"]["spans"]

    parsed = []
    for span in spans_raw:
        start = parse_month(span["start"])
        end = month_end(span["end"]) if span.get("end") else today
        parsed.append({**span, "_start": start, "_end": end})

    min_date = min(p["_start"] for p in parsed)
    total_days = (today - min_date).days

    trace_spans = []
    role_cards = []
    for p in parsed:
        left_pct = (p["_start"] - min_date).days / total_days * 100
        width_pct = (p["_end"] - p["_start"]).days / total_days * 100
        is_current = p.get("end") is None
        duration = format_duration(p["_start"], p["_end"])
        label_full = f"{duration} · in progress" if is_current else duration

        trace_spans.append({
            "id": p["id"],
            "variant": p["variant"],
            "short_title": p["short_title"],
            "trace_org": p["trace_org"],
            "end": p.get("end"),
            "left_pct": round(left_pct, 1),
            "width_pct": round(width_pct, 1),
            "duration": duration,
            "label_full": label_full,
            "label_short": duration,
            "outside_label": width_pct < OUTSIDE_LABEL_THRESHOLD_PCT,
        })

        if p["kind"] == "role":
            end_text = "now" if is_current else p["end"]
            role_cards.append({
                "id": p["id"],
                "title": p["title"],
                "dates_text": f"{p['start']} → {end_text} · {p['org_line']}",
                "current": is_current,
                "facts": [tuple(fact) for fact in p["facts"]],
            })

    min_year, max_year = min_date.year, today.year
    year_span = max_year - min_year
    axis_ticks = [min_year + int(i * year_span / 4) for i in range(5)]

    uptime_label = format_duration(min_date, today)
    trace_meta = f"{len(trace_spans)} spans · {min_date.strftime('%Y-%b')} → now"

    return {
        "trace_spans": trace_spans,
        "role_cards": role_cards,
        "axis_ticks": axis_ticks,
        "trace_meta": trace_meta,
        "uptime_label": uptime_label,
        "experience_groups": build_experience_groups(spans_raw, today),
    }


def render_site(env: jinja2.Environment, context: dict) -> None:
    template = env.get_template("site.html.j2")
    OUT_HTML.write_text(template.render(**context))
    print(f"wrote {OUT_HTML.relative_to(ROOT)}")


def render_pdf(env: jinja2.Environment, context: dict) -> None:
    from playwright.sync_api import sync_playwright

    template = env.get_template("resume.html.j2")
    html = template.render(**context)

    OUT_PDF.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(
            path=str(OUT_PDF),
            format="Letter",
            print_background=True,
        )
        browser.close()
    print(f"wrote {OUT_PDF.relative_to(ROOT)}")


def main() -> int:
    if not CONTENT_FILE.exists():
        print(f"error: {CONTENT_FILE} not found", file=sys.stderr)
        return 1

    data = yaml.safe_load(CONTENT_FILE.read_text())
    today = dt.date.today()

    context = {**data, "today": today, "last_deploy": today.strftime("%Y-%m")}
    context.update(build_experience(data, today))

    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=jinja2.select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    render_site(env, context)
    render_pdf(env, context)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
