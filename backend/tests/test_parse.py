"""Test the HTML parser against a real saved Haraj listing page."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.scraper.parse import extract_listing, extract_listing_id

FIXTURE = Path(__file__).parent / "fixtures" / "haraj_listing_sample.html"
SAMPLE_URL = "https://haraj.com.sa/11176430489/%D8%AA%D9%8A%D9%88%D8%B3_%D9%84%D9%84%D8%A8%D9%8A%D8%B9/"


def test_extract_listing_id():
    assert extract_listing_id(SAMPLE_URL) == "11176430489"


@pytest.mark.skipif(not FIXTURE.exists(), reason="real listing fixture not saved")
def test_extract_listing_from_real_html():
    html = FIXTURE.read_text(encoding="utf-8")
    raw = extract_listing(html, SAMPLE_URL)
    assert raw["id"] == "11176430489"
    assert raw["title"]  # og:title was present and non-empty
    assert "موقع حراج" not in raw["title"]  # site suffix stripped
