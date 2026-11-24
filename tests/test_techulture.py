from __future__ import annotations

import json

from datetime import datetime, timedelta, timezone

import pytest

import techulture

def test_fetch_html_selector_listing_parses_attribute_dates(monkeypatch) -> None:
    html = """
    <li class="search-result-hit">
      <span class="search-result-hit-title">
        <a href="/press/pressmeddelanden/2026/test"> Uppsala test </a>
      </span>
      <time datetime="2026-03-06T00:00:00Z">6 mars 2026</time>
    </li>
    """

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: html)
    source = {
        "source_id": "uu_press",
        "title": "Uppsala universitet",
        "type": "html_selector_listing",
        "start_url": "https://www.uu.se/press/pressmeddelanden",
        "base_url": "https://www.uu.se/",
        "item_selector": ".search-result-hit",
        "title_selector": ".search-result-hit-title a",
        "published_selector": "time",
        "published_attr": "datetime",
        "published_date_format": "%Y-%m-%dT%H:%M:%SZ",
    }

    items = techulture.fetch_html_selector_listing(source)

    assert len(items) == 1
    assert items[0].title == "Uppsala test"
    assert items[0].url == "https://www.uu.se/press/pressmeddelanden/2026/test"
    assert items[0].published_at == datetime(2026, 3, 6, 0, 0, tzinfo=timezone.utc)


def test_fetch_html_selector_listing_preserves_timezone_offsets(monkeypatch) -> None:
    html = """
    <li class="search-result-hit">
      <span class="search-result-hit-title">
        <a href="/press/pressmeddelanden/2026/test-offset"> Uppsala offset test </a>
      </span>
      <time datetime="2026-03-06T13:30:00+0100">6 mars 2026</time>
    </li>
    """

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: html)
    source = {
        "source_id": "uu_press",
        "title": "Uppsala universitet",
        "type": "html_selector_listing",
        "start_url": "https://www.uu.se/press/pressmeddelanden",
        "base_url": "https://www.uu.se/",
        "item_selector": ".search-result-hit",
        "title_selector": ".search-result-hit-title a",
        "published_selector": "time",
        "published_attr": "datetime",
        "published_date_format": "%Y-%m-%dT%H:%M:%S%z",
    }

    items = techulture.fetch_html_selector_listing(source)

    assert len(items) == 1
    assert items[0].published_at == datetime(
        2026,
        3,
        6,
        13,
        30,
        tzinfo=timezone(timedelta(hours=1)),
    )


def test_fetch_html_selector_listing_parses_swedish_dates(monkeypatch) -> None:
    html = """
    <div class="NewsListItem">
      <a class="newslink" href="/sv/Aktuellt/Nyheter-och-pressmeddelanden/2026/test/">
        Test från Konstfack
      </a>
      <div class="NewsListDate">Måndag 3 mars 2026</div>
    </div>
    """

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: html)
    source = {
        "source_id": "konstfack_news",
        "title": "Konstfack",
        "type": "html_selector_listing",
        "start_url": "https://www.konstfack.se/sv/Aktuellt/Nyheter-och-pressmeddelanden/",
        "base_url": "https://www.konstfack.se/",
        "item_selector": ".NewsListItem",
        "title_selector": ".newslink",
        "published_selector": ".NewsListDate",
        "published_date_format": "%A %d %B %Y",
        "published_locale": "sv",
    }

    items = techulture.fetch_html_selector_listing(source)

    assert len(items) == 1
    assert items[0].title == "Test från Konstfack"
    assert items[0].url == "https://www.konstfack.se/sv/Aktuellt/Nyheter-och-pressmeddelanden/2026/test/"
    assert items[0].published_at == datetime(2026, 3, 3, 0, 0, tzinfo=timezone.utc)


def test_fetch_rss_xml_parses_items(monkeypatch) -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Kunstkritikk</title>
    <item>
      <title> En oandlig   ekvation </title>
      <link>https://kunstkritikk.se/en-oandlig-ekvation/</link>
      <pubDate>Wed, 25 Feb 2026 09:29:18 +0000</pubDate>
    </item>
    <item>
      <title></title>
      <link>https://kunstkritikk.se/missing-title/</link>
      <pubDate>Wed, 25 Feb 2026 09:29:18 +0000</pubDate>
    </item>
  </channel>
</rss>
"""

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: xml)
    source = {
        "source_id": "kunstkritikk_rss",
        "title": "Kunstkritikk",
        "type": "rss_xml",
        "start_url": "https://kunstkritikk.se/feed/",
        "base_url": "https://kunstkritikk.se/",
    }

    items = techulture.fetch_rss_xml(source)

    assert len(items) == 1
    assert items[0].title == "En oandlig ekvation"
    assert items[0].url == "https://kunstkritikk.se/en-oandlig-ekvation/"
    assert items[0].published_at == datetime(2026, 2, 25, 9, 29, 18, tzinfo=timezone.utc)


def test_fetch_atom_xml_parses_entries(monkeypatch) -> None:
    xml = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <title>Kulturnytt</title>
      <entry>
        <title> Dansmuseet labbar </title>
        <link href="https://www.sverigesradio.se/artikel/9340083" />
        <published>2026-11-13T06:00:00+01:00</published>
      </entry>
      <entry>
        <title>Saknar datum</title>
        <link href="https://www.sverigesradio.se/artikel/1" />
      </entry>
    </feed>
    """

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: xml)
    source = {
        "source_id": "sr_kulturnytt_atom",
        "title": "SR Kulturnytt",
        "type": "atom_xml",
        "start_url": "https://api.sr.se/api/rss/program/478",
        "base_url": "https://www.sverigesradio.se/",
    }

    items = techulture.fetch_items(source)

    assert len(items) == 1
    assert items[0].title == "Dansmuseet labbar"
    assert items[0].url == "https://www.sverigesradio.se/artikel/9340083"
    assert items[0].published_at == datetime(2026, 11, 13, 5, 0, tzinfo=timezone.utc)


def test_fetch_items_keeps_only_newest_max_items(monkeypatch) -> None:
    entries = "".join(
        f"""
      <entry>
        <title>Artikel {hour}</title>
        <link href="https://www.sverigesradio.se/artikel/{hour}" />
        <published>2026-11-13T{hour:02d}:00:00+00:00</published>
      </entry>"""
        for hour in [3, 9, 1, 7, 5]
    )
    xml = f'<feed xmlns="http://www.w3.org/2005/Atom">{entries}</feed>'

    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: xml)
    source = {
        "source_id": "sr_kulturnytt_atom",
        "title": "SR Kulturnytt",
        "type": "atom_xml",
        "start_url": "https://api.sr.se/api/rss/program/478",
        "max_items": 2,
    }

    items = techulture.fetch_items(source)

    assert [item.title for item in items] == ["Artikel 9", "Artikel 7"]


def make_item(title: str, url: str = "https://example.se/a", hours_ago: int = 1) -> techulture.Item:
    return techulture.Item(
        source_id="svt_nyheter",
        source_title="SVT Nyheter",
        title=title,
        url=url,
        published_at=datetime.now(timezone.utc) - timedelta(hours=hours_ago),
        max_age_hours=24,
    )


def test_exclude_by_url_drops_matching_parts() -> None:
    items = [
        make_item("Inrikes", "https://www.svt.se/nyheter/inrikes/a"),
        make_item("Sport", "https://www.svt.se/sport/a"),
        make_item("Lokalt", "https://www.svt.se/nyheter/lokalt/skane/a"),
    ]

    kept = techulture.exclude_by_url(items, ["/sport/", "/lokalt/"])

    assert [item.title for item in kept] == ["Inrikes"]


def test_parse_scores_maps_index_to_score_and_ignores_noise() -> None:
    response = "Here you go:\n1. 7.5\n3. 12\n2. 99\nnonsense"

    assert techulture.parse_scores(response) == {1: 7.5, 3: 12.0}


def test_parse_scores_handles_echoed_headlines() -> None:
    response = "1. Minst 44 dödade i Kongo: 6.8\n2. Malmö FF vann: 0.5"

    assert techulture.parse_scores(response) == {1: 6.8, 2: 0.5}


def test_select_with_llm_keeps_highest_scored_fresh_items(monkeypatch) -> None:
    # Candidates are sent newest first: A, B, C.
    items = [
        make_item("C", hours_ago=3),
        make_item("A", hours_ago=1),
        make_item("Gammal", hours_ago=48),
        make_item("B", hours_ago=2),
    ]
    monkeypatch.setattr(techulture.llm, "call_llm", lambda prompt, **kwargs: "1. 2\n2. 15\n3. 9")

    selected = techulture.select_with_llm({"source_id": "svt_nyheter"}, items, max_items=2)

    assert [item.title for item in selected] == ["B", "C"]


def test_select_with_llm_falls_back_to_newest_when_model_fails(monkeypatch) -> None:
    items = [make_item("Äldre", hours_ago=5), make_item("Nyast", hours_ago=1), make_item("Mitten", hours_ago=3)]

    def fail(prompt, **kwargs):
        raise ConnectionError("model down")

    monkeypatch.setattr(techulture.llm, "call_llm", fail)

    selected = techulture.select_with_llm({"source_id": "svt_nyheter"}, items, max_items=2)

    assert [item.title for item in selected] == ["Nyast", "Mitten"]


def test_fetch_items_sets_section_from_source(monkeypatch) -> None:
    xml = """<feed xmlns="http://www.w3.org/2005/Atom"><entry>
      <title>Nyhet</title><link href="https://www.sverigesradio.se/artikel/1" />
      <published>2026-11-13T09:00:00+00:00</published></entry></feed>"""
    monkeypatch.setattr(techulture, "fetch_text", lambda url, encoding=None: xml)

    news = techulture.fetch_items({"source_id": "x", "title": "X", "type": "atom_xml", "start_url": "u", "section": "nyheter"})
    culture = techulture.fetch_items({"source_id": "y", "title": "Y", "type": "atom_xml", "start_url": "u"})

    assert news[0].section == "nyheter"
    assert culture[0].section == "kultur"


def test_fetch_items_resolves_urls_from_sitemap(monkeypatch) -> None:
    atom_xml = """<feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Patti Smith –\u00a0inviger scen</title>
        <link href="https://www.sverigesradio.se/artikel/9348176" />
        <published>2026-11-23T15:00:00+01:00</published>
      </entry>
      <entry>
        <title>Saknas i sitemap</title>
        <link href="https://www.sverigesradio.se/artikel/9999999" />
        <published>2026-11-23T14:00:00+01:00</published>
      </entry>
    </feed>"""
    sitemap_xml = """<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:news="http://www.google.com/schemas/sitemap-news/0.9">
      <url>
        <loc>https://www.sverigesradio.se/artikel/gasometer-invigs</loc>
        <news:news><news:title>Patti Smith – inviger scen</news:title></news:news>
      </url>
    </urlset>"""

    def fake_fetch(url: str, encoding=None) -> str:
        return sitemap_xml if url == "https://www.sverigesradio.se/newssitemap" else atom_xml

    monkeypatch.setattr(techulture, "fetch_text", fake_fetch)
    source = {
        "source_id": "sr_kulturnytt_atom",
        "title": "SR Kulturnytt",
        "type": "atom_xml",
        "start_url": "https://api.sr.se/api/rss/program/478",
        "url_lookup_sitemap": "https://www.sverigesradio.se/newssitemap",
    }

    items = techulture.fetch_items(source)

    assert items[0].url == "https://www.sverigesradio.se/artikel/gasometer-invigs"
    assert items[1].url == "https://www.sverigesradio.se/artikel/9999999"


def test_fetch_items_links_to_program_page_when_sitemap_fails(monkeypatch) -> None:
    atom_xml = """<feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Kulturnyhet</title>
        <link href="https://www.sverigesradio.se/artikel/9348176" />
        <published>2026-11-23T15:00:00+01:00</published>
      </entry>
    </feed>"""

    def fake_fetch(url: str, encoding=None) -> str:
        if url == "https://www.sverigesradio.se/newssitemap":
            raise techulture.requests.HTTPError("403 Forbidden")
        return atom_xml

    monkeypatch.setattr(techulture, "fetch_text", fake_fetch)
    source = {
        "source_id": "sr_kulturnytt_atom",
        "title": "SR Kulturnytt",
        "type": "atom_xml",
        "start_url": "https://api.sr.se/api/rss/program/478",
        "url_lookup_sitemap": "https://www.sverigesradio.se/newssitemap",
        "url_lookup_fallback": "https://www.sverigesradio.se/kultur",
    }

    items = techulture.fetch_items(source)

    assert [item.url for item in items] == ["https://www.sverigesradio.se/kultur"]


@pytest.mark.parametrize(("share", "expected_code"), [("0.5", 1), ("0", 0)])
def test_main_min_source_share_protects_existing_page(tmp_path, monkeypatch, share, expected_code) -> None:
    store_path = tmp_path / "store.json"
    out_path = tmp_path / "index.html"
    out_path.write_text("old page", encoding="utf-8")

    def fail(source):
        raise RuntimeError("blocked")

    monkeypatch.setattr(techulture, "load_sources", lambda path: [{"source_id": "a"}, {"source_id": "b"}])
    monkeypatch.setattr(techulture, "fetch_items", fail)
    monkeypatch.setattr(
        "sys.argv",
        ["techulture.py", "--store", str(store_path), "--out", str(out_path), "--min-source-share", share],
    )

    assert techulture.main() == expected_code
    assert (out_path.read_text(encoding="utf-8") == "old page") == bool(expected_code)


def test_call_llm_reads_chat_completion(monkeypatch) -> None:
    sent = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"choices": [{"message": {"content": "1. 7"}}]}'

    def fake_urlopen(request, timeout):
        sent["body"] = json.loads(request.data)
        return FakeResponse()

    monkeypatch.setattr(techulture.llm.urllib.request, "urlopen", fake_urlopen)

    assert techulture.llm.call_llm("Score this") == "1. 7"
    assert sent["body"]["messages"] == [{"role": "user", "content": "Score this"}]
    assert sent["body"]["temperature"] == 0
