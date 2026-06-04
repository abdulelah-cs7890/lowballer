"""Parse a Haraj listing page into a raw dict for the normalizer.

Haraj is a React-Router SSR app; the reliable, stable signals in the HTML are the
OpenGraph meta tags (clean title) and the listing id (from the URL). Price/body live
in a deduplicated turbo-stream blob, so we extract those best-effort — the normalizer
re-derives them from the title/body text anyway.
"""

from __future__ import annotations

import re


def _meta(html: str, prop: str) -> str | None:
    for pat in (
        rf'property=["\']{re.escape(prop)}["\']\s+content=["\'](.*?)["\']',
        rf'content=["\'](.*?)["\']\s+property=["\']{re.escape(prop)}["\']',
    ):
        m = re.search(pat, html, re.S)
        if m:
            return m.group(1).strip()
    return None


def extract_listing_id(url: str) -> str:
    m = re.search(r"haraj\.com\.sa/(\d+)", url)
    return m.group(1) if m else url.rstrip("/").rsplit("/", 1)[-1]


def _best_effort_price(html: str) -> int | None:
    m = re.search(r'\\?"price\\?"[^0-9]{0,40}([0-9]{4,7})', html)
    return int(m.group(1)) if m else None


def extract_listing(html: str, url: str) -> dict:
    title = _meta(html, "og:title") or ""
    title = re.split(r"\s*\|\s*", title)[0].strip()  # drop "| موقع حراج" suffix
    return {
        "id": extract_listing_id(url),
        "url": url,
        "title": title,
        "body_text": _meta(html, "og:description") or "",
        "price": _best_effort_price(html),
        "city": None,
    }
