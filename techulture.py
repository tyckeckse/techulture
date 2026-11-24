#!/usr/bin/env python3
from __future__ import annotations

import argparse
import email.utils
import json
import re
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import llm
from render_index import DEFAULT_MAX_AGE_HOURS, DEFAULT_RENDER_LIMIT, render_store_to_file


BASE_DIR = Path(__file__).resolve().parent
STORE_VERSION = 1
USER_AGENT = "techulture/0.1"
DEFAULT_SECTION = "kultur"
SCORE_MAX = 20
SCORE_BATCH_SIZE = 10
LLM_CANDIDATE_LIMIT = 40


@dataclass
class Item:
    source_id: str
    source_title: str
    title: str
    url: str
    published_at: datetime
    max_age_hours: int
    section: str = DEFAULT_SECTION


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch a minimal local culture digest.")
    parser.add_argument("--sources", default="sources.json", help="Path to source config")
    parser.add_argument("--store", default="data/store.json", help="Path to local item store")
    parser.add_argument("--out", default="index.html", help="Path to output HTML file")
    parser.add_argument("--limit", type=int, default=5, help="Items to print per source")
    parser.add_argument("--render-limit", type=int, default=DEFAULT_RENDER_LIMIT, help="Maximum number of items to render")
    parser.add_argument(
        "--max-age-hours",
        type=int,
        default=DEFAULT_MAX_AGE_HOURS,
        help="Only render items published within this number of hours",
    )
    parser.add_argument(
        "--min-source-share",
        type=float,
        default=0.0,
        help="Fail without writing anything if a smaller share of sources (0-1) returned items",
    )
    return parser.parse_args()


def load_sources(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["sources"]


def item_to_dict(item: Item) -> dict[str, str]:
    return {
        "source_id": item.source_id,
        "source_title": item.source_title,
        "title": item.title,
        "url": item.url,
        "published_at": item.published_at.isoformat(),
        "max_age_hours": item.max_age_hours,
        "section": item.section,
    }


def save_store(path: Path, items: list[Item]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": STORE_VERSION,
        "items": [item_to_dict(item) for item in sorted(items, key=lambda item: item.published_at, reverse=True)],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def fetch_text(url: str, encoding: str | None = None) -> str:
    response = requests.get(url, timeout=20, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    if encoding:
        response.encoding = encoding
    return response.text


def fetch_omkonst_listing(source: dict[str, Any]) -> list[Item]:
    html = fetch_text(source["start_url"], encoding=source.get("encoding"))
    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []

    for row in soup.find_all("tr"):
        date_node = row.find("span")
        link = row.find("a", href=True)
        if date_node is None or link is None:
            continue

        href = link["href"].strip()
        if not href.endswith(source["item_link_suffix"]):
            continue

        date_text = date_node.get_text(" ", strip=True)
        title = link.get_text(" ", strip=True)
        if not date_text or not title:
            continue

        published_at = datetime.strptime(date_text, source["published_date_format"]).replace(tzinfo=timezone.utc)
        items.append(
            Item(
                source_id=source["source_id"],
                source_title=source["title"],
                title=title,
                url=urljoin(source["base_url"], href),
                published_at=published_at,
                max_age_hours=source.get("max_age_hours", DEFAULT_MAX_AGE_HOURS),
            )
        )

    return items


def fetch_html_selector_listing(source: dict[str, Any]) -> list[Item]:
    html = fetch_text(source["start_url"], encoding=source.get("encoding"))
    soup = BeautifulSoup(html, "html.parser")
    base_url = source.get("base_url", source["start_url"])
    items: list[Item] = []

    for node in soup.select(source["item_selector"]):
        title_node = node.select_one(source["title_selector"])
        published_node = node.select_one(source["published_selector"])
        if title_node is None or published_node is None:
            continue

        href = (title_node.get("href") or "").strip()
        title = title_node.get_text(" ", strip=True)

        published_attr = source.get("published_attr")
        if published_attr:
            published_value = (published_node.get(published_attr) or "").strip()
        else:
            published_value = published_node.get_text(" ", strip=True)

        if not href or not title or not published_value:
            continue

        if source.get("published_locale") == "sv":
            published_value = normalize_swedish_date(published_value)

        published_at = datetime.strptime(
            published_value,
            source["published_date_format"],
        )
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)

        items.append(
            Item(
                source_id=source["source_id"],
                source_title=source["title"],
                title=" ".join(title.split()),
                url=urljoin(base_url, href),
                published_at=published_at,
                max_age_hours=source.get("max_age_hours", DEFAULT_MAX_AGE_HOURS),
            )
        )

    return items


GOOGLE_NEWS_NS = {
    "sm": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
}


def fetch_google_news_xml(source: dict[str, Any]) -> list[Item]:
    xml_text = fetch_text(source["start_url"])
    root = ET.fromstring(xml_text)
    items: list[Item] = []

    for node in root.findall("sm:url", GOOGLE_NEWS_NS):
        url = (node.findtext("sm:loc", default="", namespaces=GOOGLE_NEWS_NS) or "").strip()
        title = (node.findtext("news:news/news:title", default="", namespaces=GOOGLE_NEWS_NS) or "").strip()
        published = (node.findtext("news:news/news:publication_date", default="", namespaces=GOOGLE_NEWS_NS) or "").strip()
        if not url or not title or not published:
            continue

        path = urlparse(url).path
        if not path.startswith(source["url_path_prefix"]):
            continue

        items.append(
            Item(
                source_id=source["source_id"],
                source_title=source["title"],
                title=" ".join(title.split()),
                url=url,
                published_at=datetime.fromisoformat(published.replace("Z", "+00:00")),
                max_age_hours=source.get("max_age_hours", DEFAULT_MAX_AGE_HOURS),
            )
        )

    return items


def parse_rss_pubdate(value: str) -> datetime:
    published_at = email.utils.parsedate_to_datetime(value)
    if published_at.tzinfo is None:
        return published_at.replace(tzinfo=timezone.utc)
    return published_at


def fetch_rss_xml(source: dict[str, Any]) -> list[Item]:
    xml_text = fetch_text(source["start_url"])
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []

    base_url = source.get("base_url", source["start_url"])
    items: list[Item] = []

    for node in channel.findall("item"):
        url = (node.findtext("link", default="") or "").strip()
        title = (node.findtext("title", default="") or "").strip()
        published = (node.findtext("pubDate", default="") or "").strip()
        if not url or not title or not published:
            continue

        items.append(
            Item(
                source_id=source["source_id"],
                source_title=source["title"],
                title=" ".join(title.split()),
                url=urljoin(base_url, url),
                published_at=parse_rss_pubdate(published),
                max_age_hours=source.get("max_age_hours", DEFAULT_MAX_AGE_HOURS),
            )
        )

    return items


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}


def fetch_atom_xml(source: dict[str, Any]) -> list[Item]:
    root = ET.fromstring(fetch_text(source["start_url"]))
    base_url = source.get("base_url", source["start_url"])
    items: list[Item] = []

    for entry in root.findall("atom:entry", ATOM_NS):
        title = (entry.findtext("atom:title", default="", namespaces=ATOM_NS) or "").strip()
        published = (entry.findtext("atom:published", default="", namespaces=ATOM_NS) or "").strip()
        link_node = entry.find("atom:link", ATOM_NS)
        url = link_node.get("href", "").strip() if link_node is not None else ""
        if not url or not title or not published:
            continue

        items.append(
            Item(
                source_id=source["source_id"],
                source_title=source["title"],
                title=" ".join(title.split()),
                url=urljoin(base_url, url),
                published_at=datetime.fromisoformat(published),
                max_age_hours=source.get("max_age_hours", DEFAULT_MAX_AGE_HOURS),
            )
        )

    return items


def resolve_urls_from_sitemap(items: list[Item], sitemap_url: str) -> list[Item]:
    # Some feeds (e.g. SR Kulturnytt Atom) emit broken numeric article IDs; look up canonical URLs by title.
    root = ET.fromstring(fetch_text(sitemap_url))
    url_by_title: dict[str, str] = {}

    for node in root.findall("sm:url", GOOGLE_NEWS_NS):
        url = (node.findtext("sm:loc", default="", namespaces=GOOGLE_NEWS_NS) or "").strip()
        title = (node.findtext("news:news/news:title", default="", namespaces=GOOGLE_NEWS_NS) or "").strip()
        if url and title:
            url_by_title.setdefault(" ".join(title.split()), url)

    for item in items:
        if item.title in url_by_title:
            item.url = url_by_title[item.title]

    return items


def normalize_swedish_date(value: str) -> str:
    normalized = " ".join(value.replace("\xa0", " ").split())

    weekdays = {
        "måndag": "Monday",
        "tisdag": "Tuesday",
        "onsdag": "Wednesday",
        "torsdag": "Thursday",
        "fredag": "Friday",
        "lördag": "Saturday",
        "söndag": "Sunday",
    }
    months = {
        "januari": "January",
        "februari": "February",
        "mars": "March",
        "april": "April",
        "maj": "May",
        "juni": "June",
        "juli": "July",
        "augusti": "August",
        "september": "September",
        "oktober": "October",
        "november": "November",
        "december": "December",
    }

    parts = normalized.split()
    translated: list[str] = []

    for part in parts:
        lower = part.lower()
        if lower in weekdays:
            translated.append(weekdays[lower])
        elif lower in months:
            translated.append(months[lower])
        else:
            translated.append(part)

    return " ".join(translated)



def fetch_items(source: dict[str, Any]) -> list[Item]:
    source_type = source["type"]
    if source_type == "html_listing":
        items = fetch_omkonst_listing(source)
    elif source_type == "google_news_xml":
        items = fetch_google_news_xml(source)
    elif source_type == "rss_xml":
        items = fetch_rss_xml(source)
    elif source_type == "atom_xml":
        items = fetch_atom_xml(source)
    elif source_type == "html_selector_listing":
        items = fetch_html_selector_listing(source)
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

    items = exclude_by_url(items, source.get("exclude_url_parts", []))
    sitemap_url = source.get("url_lookup_sitemap")
    if sitemap_url:
        try:
            items = resolve_urls_from_sitemap(items, sitemap_url)
        except (requests.RequestException, ET.ParseError) as error:
            fallback_url = source.get("url_lookup_fallback")
            if not fallback_url:
                raise
            # The feed's own article links are unreliable, so link to the program page instead.
            print(f"{source['source_id']}: url lookup failed, using fallback link: {error}", file=sys.stderr)
            for item in items:
                item.url = fallback_url
    for item in items:
        item.section = source.get("section", DEFAULT_SECTION)

    if source.get("llm_select"):
        return select_with_llm(source, items, source.get("max_items"))
    return limit_newest(items, source.get("max_items"))


def exclude_by_url(items: list[Item], url_parts: list[str]) -> list[Item]:
    # Cheap pre-filter, e.g. sport or local news, before any LLM call.
    return [item for item in items if not any(part in item.url for part in url_parts)]


def filter_fresh(items: list[Item], now: datetime | None = None) -> list[Item]:
    reference_now = now or datetime.now(timezone.utc)
    return [
        item for item in items
        if (reference_now - item.published_at).total_seconds() <= item.max_age_hours * 3600
    ]


def build_scoring_prompt(items: list[Item]) -> str:
    headlines = "\n".join(f"{index}. {item.title}" for index, item in enumerate(items, start=1))
    return (
        f"Score each Swedish news headline from 0 to {SCORE_MAX}.\n"
        "Estimate how much a curious, well-read adult would want to open the story. "
        "You only have the headline; do not invent details.\n"
        "0-5: routine updates, vague teasers, local or niche stories, sport, "
        "match results and sports transfers.\n"
        "6-12: concrete new facts with clear stakes for many people.\n"
        "13-20: important or surprising developments in politics, society, "
        "economy, science or the world that people will want to understand.\n"
        "Do not reward sensational wording, crime details or celebrity names alone.\n\n"
        f"HEADLINES:\n{headlines}\n\n"
        "Output one line per headline, index then score, for example:\n"
        "1. 7.5\n"
        "2. 3.0\n"
        "Do not repeat the headline text. No other text.\n"
    )


def parse_scores(response_text: str) -> dict[int, float]:
    # Map 1-based headline index to score, so skipped or reordered lines stay aligned.
    # Small models often echo the headline ("1. Title: 9.0"), so the score is the last number.
    scores: dict[int, float] = {}
    for line in response_text.splitlines():
        match = re.match(r"^(\d+)[.):]\s*(.*)$", line.strip())
        if not match:
            continue
        numbers = re.findall(r"\d+(?:\.\d+)?", match.group(2))
        if numbers and float(numbers[-1]) <= SCORE_MAX:
            scores[int(match.group(1))] = float(numbers[-1])
    return scores


def select_with_llm(source: dict[str, Any], items: list[Item], max_items: int | None) -> list[Item]:
    # Only score fresh items; older ones would be dropped at render time anyway.
    candidates = limit_newest(filter_fresh(items), LLM_CANDIDATE_LIMIT)
    if max_items is None or len(candidates) <= max_items:
        return candidates

    scored: list[tuple[float, Item]] = []
    for start in range(0, len(candidates), SCORE_BATCH_SIZE):
        batch = candidates[start:start + SCORE_BATCH_SIZE]
        try:
            response_text = llm.call_llm(build_scoring_prompt(batch))
        except Exception as error:
            # Model down or slow: fall back to the newest items.
            print(f"{source['source_id']}: llm scoring skipped: {error}", file=sys.stderr)
            return limit_newest(candidates, max_items)
        scores = parse_scores(response_text)
        scored.extend((scores.get(index, 0.0), item) for index, item in enumerate(batch, start=1))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    for score, item in scored[:max_items]:
        print(f"  {score:4.1f}  {item.title}")
    return [item for _, item in scored[:max_items]]


def limit_newest(items: list[Item], max_items: int | None) -> list[Item]:
    # Keep only the newest items so one busy source cannot crowd out the rest.
    if max_items is None:
        return items
    return sorted(items, key=lambda item: item.published_at, reverse=True)[:max_items]


def print_items(items: list[Item], limit: int) -> None:
    by_source: dict[str, list[Item]] = {}
    for item in items:
        by_source.setdefault(item.source_id, []).append(item)

    for group in by_source.values():
        group.sort(key=lambda item: item.published_at, reverse=True)

    ordered_groups = sorted(
        by_source.values(),
        key=lambda group: group[0].source_title.lower(),
    )

    for group in ordered_groups:
        print(group[0].source_title)
        for item in group[:limit]:
            published_label = item.published_at.isoformat(sep=" ", timespec="minutes")
            print(f"  - {published_label} | {item.title}")
            print(f"    {item.url}")
        print()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = parse_args()
    sources = load_sources(BASE_DIR / args.sources)
    store_path = BASE_DIR / args.store

    items: list[Item] = []
    sources_with_items = 0

    for source in sources:
        try:
            source_items = fetch_items(source)
        except Exception as error:
            # One broken source should not stop the whole refresh.
            print(f"Skipping {source['source_id']}: {error}", file=sys.stderr)
            continue
        items.extend(source_items)
        sources_with_items += bool(source_items)

    if sources_with_items < args.min_source_share * len(sources):
        print(f"Only {sources_with_items} of {len(sources)} sources returned items; nothing written", file=sys.stderr)
        return 1

    save_store(store_path, items)
    render_store_to_file(
        store_path,
        BASE_DIR / args.out,
        limit=args.render_limit,
        max_age_hours=args.max_age_hours,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
