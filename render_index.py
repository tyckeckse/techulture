#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo


BASE_DIR = Path(__file__).resolve().parent
LOCAL_TIMEZONE = ZoneInfo("Europe/Stockholm")
DEFAULT_RENDER_LIMIT = 40
DEFAULT_MAX_AGE_HOURS = 24
DEFAULT_SECTION = "kultur"
# Column order and headings; items with an unknown section fall back to the first column.
SECTIONS = [("kultur", "Kultur"), ("nyheter", "Nyheter")]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render a minimal HTML page from the local store.")
    parser.add_argument("--store", default="data/store.json", help="Path to local item store")
    parser.add_argument("--out", default="index.html", help="Path to output HTML file")
    parser.add_argument("--limit", type=int, default=DEFAULT_RENDER_LIMIT, help="Maximum number of items to render")
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Only render items published within this number of hours",
    )
    return parser.parse_args()


def load_store(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("items", [])

def group_items_by_source(items: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = {}

    for item in items:
        source_title = item["source_title"]
        grouped.setdefault(source_title, []).append(item)

    return grouped

def find_inactive_sources(
    all_items: list[dict[str, str]],
    recent_items: list[dict[str, str]],
) -> list[dict[str, str]]:
    all_sources = group_items_by_source(all_items)
    recent_sources = group_items_by_source(recent_items)

    inactive: list[dict[str, str]] = []

    for source_title in sorted(all_sources):
        if source_title in recent_sources:
            continue

        latest_item = all_sources[source_title][0]
        inactive.append(
            {
                "source_title": source_title,
                "latest_published_at": latest_item["published_at"],
                "section": latest_item.get("section", DEFAULT_SECTION),
            }
        )

    return inactive

def render_inactive_sources(source_titles: list[str]) -> str:
    if not source_titles:
        return ""

    parts: list[str] = []
    for source_info in source_titles:
        source = html.escape(source_info["source_title"])
        latest = html.escape(format_published_at(source_info["latest_published_at"])[:10])
        parts.append(
            f"<article class='card card-inactive'>"
            f"<h3>{source}</h3>"
            f"<p class='meta'>Senaste post: {latest}</p>"
            f"</article>"
        )

    return "\n".join(parts)



def parse_published_at(value: str) -> datetime:
    published_at = datetime.fromisoformat(value)
    if published_at.tzinfo is None:
        return published_at.replace(tzinfo=timezone.utc)
    return published_at


def format_published_at(value: str) -> str:
    published_at = parse_published_at(value)
    # Sources that only publish a date are stored as midnight UTC, so there is no real time to show.
    if published_at.utcoffset() == timedelta(0) and published_at.strftime("%H:%M:%S") == "00:00:00":
        return published_at.strftime("%Y-%m-%d")
    return published_at.astimezone(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M")


def sort_items(items: list[dict[str, str]]) -> list[dict[str, str]]:
    return sorted(
        items,
        key=lambda item: parse_published_at(item["published_at"]),
        reverse=True,
    )


def filter_recent_items(
    items: list[dict[str, str]],
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    now: datetime | None = None,
) -> list[dict[str, str]]:
    if max_age_hours < 0:
        raise ValueError("max_age_hours must be non-negative")
    
    reference_now = now or datetime.now(timezone.utc)
    filtered: list[dict[str, str]] = []

    for item in items:
        window_hours = int(item.get("max_age_hours", max_age_hours))
        if window_hours < 0:
            raise ValueError("max_age_hours must be non-negative")

        cutoff = reference_now - timedelta(hours=window_hours)
        if parse_published_at(item["published_at"]) >= cutoff:
            filtered.append(item)

    return filtered

def render_items(items: list[dict[str, str]], max_age_hours: int) -> str:
    if not items:
        return "<p class='empty'>Inga artiklar just nu.</p>"

    parts: list[str] = []
    for item in items:
        title = html.escape(item["title"])
        url = html.escape(item["url"])
        source = html.escape(item["source_title"])
        published = html.escape(format_published_at(item["published_at"]))
        parts.append(
            f"<article class='card'>"
            f"<h3><a href='{url}' target='_blank' rel='noopener noreferrer'>{title}</a></h3>"
            f"<p class='meta'>{source} | {published}</p>"
            f"</article>"
        )
    return "\n".join(parts)


def split_by_section(items: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    known = {key for key, _ in SECTIONS}
    columns: dict[str, list[dict[str, str]]] = {key: [] for key, _ in SECTIONS}
    for item in items:
        section = item.get("section", DEFAULT_SECTION)
        columns[section if section in known else DEFAULT_SECTION].append(item)
    return columns


def render_columns(
    items: list[dict[str, str]],
    inactive_sources: list[dict[str, str]],
    max_age_hours: int,
) -> str:
    columns = split_by_section(items)
    # Inactive sources sit at the bottom of their own column, so short columns fill up.
    inactive_columns = split_by_section(inactive_sources)
    parts = [
        f"<section class='column column-{key}'>"
        f"<h2>{html.escape(heading)}</h2>"
        f"{render_items(columns[key], max_age_hours=max_age_hours)}"
        f"{render_inactive_sources(inactive_columns[key])}"
        f"</section>"
        for key, heading in SECTIONS
    ]
    return "<div class='columns'>" + "\n".join(parts) + "</div>"


def render_page(
    recent_items: list[dict[str, str]],
    all_items: list[dict[str, str]],
    max_age_hours: int,
) -> str:
    updated = datetime.now(LOCAL_TIMEZONE).strftime("%Y-%m-%d %H:%M")
    inactive_sources = find_inactive_sources(all_items, recent_items)
    body = render_columns(recent_items, inactive_sources, max_age_hours=max_age_hours)
    return f"""<!doctype html>
<html lang='sv'>
<head>
  <meta charset='utf-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1'>
  <title>Techulture</title>
  <link rel='icon' href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🧭</text></svg>">
  <style>
    /* shared-theme:start */
    :root {{
      color-scheme: light;
      --bg: #f6f2e9;
      --panel: #fffdf8;
      --text: #1d2a2f;
      --muted: #617076;
      --line: #d9d0c3;
      --accent: #1c4f73;
      --error: #8a2f2f;
    }}

    body {{
      margin: 0;
      font-family: "Segoe UI", -apple-system, sans-serif;
      background: radial-gradient(circle at top, #fefcf6, var(--bg));
      color: var(--text);
    }}

    a {{
      color: var(--accent);
      text-decoration: none;
    }}

    a:hover {{
      text-decoration: underline;
    }}
    /* shared-theme:end */

    main {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 36px; }}
    h1 {{ margin: 0 0 6px; font-size: 1.6rem; }}
    h2 {{ margin: 20px 0 10px; }}
    .columns {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      align-items: start;
    }}
    .column h2 {{
      margin: 0 0 10px;
      font-size: 0.85rem;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--muted);
    }}
    @media (max-width: 720px) {{
      .columns {{ grid-template-columns: 1fr; gap: 20px; }}
      /* News first on small screens. */
      .column-nyheter {{ order: -1; }}
    }}
    p {{ margin: 0 0 12px; }}
    .updated {{ color: var(--muted); margin-bottom: 18px; font-size: 0.95rem; }}
    .meta {{ color: var(--muted); font-size: 0.88rem; }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px 16px;
      margin: 0 0 12px;
    }}
    .card-inactive {{
      background: transparent;
      border: 1px solid var(--line);
      color: var(--muted);
      padding: 10px 14px;
      margin: 0 0 8px;
    }}
    .card + .card-inactive, .empty + .card-inactive {{ margin-top: 20px; }}
    .card-inactive h3 {{
      margin: 0 0 4px;
      font-size: 1rem;
      font-weight: normal;
      color: var(--muted);
    }}
    .card-inactive .meta {{
      color: var(--muted);
    }}

    .card h3 {{ margin: 0 0 6px; font-size: 1rem; font-weight: normal; }}
    .card h3 a {{ font-weight: 600; }}
    .card p {{ margin: 0; line-height: 1.35; }}
    .empty {{ color: var(--muted); }}
  </style>
</head>
<body>
  <main>
    <h1>Techulture</h1>
    <p class='updated'>Senaste uppdatering: {html.escape(updated)}</p>
    {body}
  </main>
</body>
</html>
"""


def render_store_to_file(
    store_path: Path,
    out_path: Path,
    limit: int,
    max_age_hours: int = DEFAULT_MAX_AGE_HOURS,
    now: datetime | None = None,
) -> int:
    all_items = sort_items(load_store(store_path))
    recent_items = filter_recent_items(all_items, max_age_hours=max_age_hours, now=now)[:limit]
    out_path.write_text(
        render_page(recent_items, all_items, max_age_hours=max_age_hours),
        encoding="utf-8",
    )
    return len(recent_items)



def main() -> int:
    args = parse_args()
    store_path = BASE_DIR / args.store
    out_path = BASE_DIR / args.out

    count = render_store_to_file(
        store_path,
        out_path,
        args.limit,
        max_age_hours=args.max_age_hours,
    )
    print(f"Rendered {count} items to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
