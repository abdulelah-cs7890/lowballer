"""Sources of raw listings for the pipeline.

- `fixture_source` (default): crafted realistic Arabic car listings — deterministic,
  offline, what the scraper hands to the normalizer.
- `live_haraj_source`: fetches + parses real listing URLs via the polite client.
  Implemented and rate-limited, but not exercised by tests or the default worker.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from legacy.scraper.client import HarajClient
from legacy.scraper.parse import extract_listing

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "car_listings.json"


def fixture_source() -> Iterator[dict]:
    yield from json.loads(FIXTURES.read_text(encoding="utf-8"))


def live_haraj_source(urls: Iterable[str], limit: int = 25) -> Iterator[dict]:
    """Fetch and parse a set of Haraj listing URLs (e.g. car listings from a tag page
    or the sitemap). Rate-limited and robots-aware via HarajClient.
    """
    with HarajClient() as client:
        for i, url in enumerate(urls):
            if i >= limit:
                break
            try:
                html = client.get(url)
            except Exception:
                continue
            yield extract_listing(html, url)
