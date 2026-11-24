from __future__ import annotations

import json
from datetime import datetime, timezone

from render_index import format_published_at, render_store_to_file


def test_render_store_to_file_only_keeps_latest_24_hours(tmp_path) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    payload = {
        "items": [
            {
                "title": "Newest",
                "url": "https://example.com/newest",
                "source_title": "Example",
                "published_at": "2026-03-01T12:00:00+00:00",
            },
            {
                "title": "Still recent",
                "url": "https://example.com/recent",
                "source_title": "Example",
                "published_at": "2026-02-28T13:00:00+00:00",
            },
            {
                "title": "Too old",
                "url": "https://example.com/old",
                "source_title": "Example",
                "published_at": "2026-02-28T11:59:00+00:00",
            },
        ]
    }
    store_path.write_text(json.dumps(payload), encoding="utf-8")

    count = render_store_to_file(
        store_path,
        out_path,
        limit=10,
        max_age_hours=24,
        now=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )

    rendered = out_path.read_text(encoding="utf-8")
    assert count == 2
    assert "Newest" in rendered
    assert "Still recent" in rendered
    assert "Too old" not in rendered


def test_render_store_to_file_preserves_unicode_characters(tmp_path) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    payload = {
        "items": [
            {
                "title": "Filippa Friberg – Göteborg",
                "url": "https://example.com/unicode",
                "source_title": "Omkonst",
                "published_at": "2026-03-01T12:00:00+00:00",
            }
        ]
    }
    store_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    render_store_to_file(
        store_path,
        out_path,
        limit=10,
        max_age_hours=24,
        now=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )

    rendered = out_path.read_text(encoding="utf-8")
    assert "Filippa Friberg – Göteborg" in rendered


def test_render_store_to_file_uses_per_source_windows(tmp_path) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    payload = {
        "items": [
            {
                "title": "Expressen recent",
                "url": "https://example.com/expressen-recent",
                "source_title": "Expressen Kultur",
                "published_at": "2026-03-01T13:00:00+00:00",
                "max_age_hours": 24,
            },
            {
                "title": "Kunstkritikk within 48",
                "url": "https://example.com/kunstkritikk",
                "source_title": "Kunstkritikk",
                "published_at": "2026-02-28T16:00:00+00:00",
                "max_age_hours": 48,
            },
            {
                "title": "Omkonst too old",
                "url": "https://example.com/omkonst-old",
                "source_title": "Omkonst",
                "published_at": "2026-02-27T11:59:00+00:00",
                "max_age_hours": 48,
            },
        ]
    }
    store_path.write_text(json.dumps(payload), encoding="utf-8")

    count = render_store_to_file(
        store_path,
        out_path,
        limit=10,
        max_age_hours=24,
        now=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )

    rendered = out_path.read_text(encoding="utf-8")
    assert count == 2
    assert "Expressen recent" in rendered
    assert "Kunstkritikk within 48" in rendered
    assert "Omkonst too old" not in rendered


def test_render_store_to_file_splits_items_into_section_columns(tmp_path) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    payload = {
        "items": [
            {
                "title": "Nyhetsartikel",
                "url": "https://example.com/news",
                "source_title": "SVT Nyheter",
                "published_at": "2026-03-01T11:00:00+00:00",
                "section": "nyheter",
            },
            {
                "title": "Kulturartikel utan sektion",
                "url": "https://example.com/culture",
                "source_title": "Omkonst",
                "published_at": "2026-03-01T10:00:00+00:00",
            },
        ]
    }
    store_path.write_text(json.dumps(payload), encoding="utf-8")

    render_store_to_file(
        store_path,
        out_path,
        limit=10,
        max_age_hours=24,
        now=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )

    rendered = out_path.read_text(encoding="utf-8")
    culture_column, news_column = rendered.split("<h2>Nyheter</h2>")
    assert "<h2>Kultur</h2>" in culture_column
    assert "Kulturartikel utan sektion" in culture_column
    assert "Nyhetsartikel" in news_column
    assert "Kulturartikel" not in news_column


def test_render_store_to_file_puts_inactive_sources_in_their_column(tmp_path) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    payload = {
        "items": [
            {
                "title": "Färsk nyhet",
                "url": "https://example.com/news",
                "source_title": "SVT Nyheter",
                "published_at": "2026-03-01T11:00:00+00:00",
                "section": "nyheter",
            },
            {
                "title": "Gammal kultur",
                "url": "https://example.com/old",
                "source_title": "Konstfack",
                "published_at": "2026-02-20T10:00:00+00:00",
            },
        ]
    }
    store_path.write_text(json.dumps(payload), encoding="utf-8")

    render_store_to_file(
        store_path,
        out_path,
        limit=10,
        max_age_hours=24,
        now=datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc),
    )

    culture_column, news_column = out_path.read_text(encoding="utf-8").split("<h2>Nyheter</h2>")
    assert "Konstfack" in culture_column
    assert "Konstfack" not in news_column


def test_format_published_at_shows_swedish_time() -> None:
    assert format_published_at("2026-11-24T11:33:00+00:00") == "2026-11-24 12:33"
    assert format_published_at("2026-07-01T11:33:00+00:00") == "2026-07-01 13:33"
    assert format_published_at("2026-11-24T12:52:00+01:00") == "2026-11-24 12:52"


def test_format_published_at_omits_time_for_date_only_sources() -> None:
    assert format_published_at("2026-11-24T00:00:00+00:00") == "2026-11-24"
