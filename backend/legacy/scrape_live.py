"""Harvest REAL car deals from live Haraj.

Listing IDs are sequential, so we walk back from the newest id on the homepage, fetch
each listing (rate-limited, robots-aware), and keep the ones that are (a) cars and
(b) have a published price — combining the clean `og:title`/`og:description` text with the
structured fields recovered from the React-Router data stream (`haraj_stream`).

Reality check: most Haraj sellers don't publish a price (they negotiate in chat), so the
yield is low — expect to scan many listings per usable deal. Run:

    python -m legacy.scrape_live --scan 600 --target 25
"""

from __future__ import annotations

import argparse
import re

from app.db import SessionLocal, init_db
from app.models.tables import Flag, Listing, Valuation
from legacy.recorder import record_listing
from legacy.scraper.client import BASE, HarajClient
from legacy.scraper.haraj_stream import extract_stream_fields
from legacy.scraper.normalize import (
    _CITY_REGION,
    _ORIGIN,
    _match_dict,
    _norm,
    detect_make_model,
    extract_price,
    extract_year,
)
from legacy.valuation.model import Valuator

_FUEL_MAP = {"GASOLINE": "Gas", "GAS": "Gas", "DIESEL": "Diesel", "HYBRID": "Hybrid", "ELECTRIC": "Hybrid"}
_GEAR_MAP = {"AUTO": "Automatic", "AUTOMATIC": "Automatic", "MANUAL": "Manual"}


def _og(html: str, prop: str) -> str:
    m = re.search(rf'og:{prop}["\']\s+content=["\'](.*?)["\']', html, re.S)
    return m.group(1).strip() if m else ""


def build_record(listing_id: str, url: str, title: str, body: str, stream: dict) -> dict | None:
    """Merge stream fields + title/body text into a canonical, model-ready record."""
    text = _norm(f"{title} {body}")
    make, model = detect_make_model(text)
    year = stream.get("year") or extract_year(text)
    sp = stream.get("price")
    price = sp if isinstance(sp, (int, float)) and sp >= 1000 else extract_price(text)
    if not (make and year and price):
        return None  # need make + year + price to value a deal

    mileage = stream.get("mileage_km")
    mileage = int(mileage) if isinstance(mileage, (int, float)) and mileage > 0 else None
    found = [make is not None, model is not None, mileage is not None, True]
    return {
        "id": listing_id,
        "url": url,
        "title": title,
        "make": make,
        "model": model,
        "year": int(year),
        "mileage_km": mileage if mileage is not None else int(max(5_000, (2025 - int(year)) * 18_000)),
        "engine_size": 2.5,
        "fuel_type": _FUEL_MAP.get(str(stream.get("fuel") or "").upper()),
        "gear_type": _GEAR_MAP.get(str(stream.get("gear") or "").upper()),
        "origin": _match_dict(text, _ORIGIN),
        "region": _match_dict(text, _CITY_REGION),
        "color": None,
        "options": None,
        "price": int(price),
        "parse_confidence": round(sum(found) / len(found), 2),
    }


def _newest_id(client: HarajClient) -> int:
    ids = [int(x) for x in re.findall(r"haraj\.com\.sa/(\d{8,})", client.get(f"{BASE}/"))]
    return max(ids)


def harvest(scan: int = 600, target: int = 25, min_delay: float = 0.4, replace: bool = True) -> dict:
    init_db()
    valuator = Valuator()
    session = SessionLocal()
    client = HarajClient(min_delay=min_delay)

    if replace:  # "real deals only" — clear all prior (synthetic) data
        session.query(Flag).delete()
        session.query(Valuation).delete()
        session.query(Listing).delete()
        session.commit()

    newest = _newest_id(client)
    stats = dict(scanned=0, cars=0, priced=0, ingested=0, flagged=0)
    for offset in range(scan):
        lid = newest - offset
        url = f"{BASE}/{lid}/x/"
        try:
            html = client.get(url)
        except Exception:
            continue
        stats["scanned"] += 1
        stream = extract_stream_fields(html)
        if not stream.get("is_car"):
            continue
        stats["cars"] += 1
        rec = build_record(str(lid), url, _og(html, "title"), _og(html, "description"), stream)
        if rec is None:
            continue
        stats["priced"] += 1
        valuation = valuator.value(rec)
        record_listing(
            session, f"haraj-{lid}", rec, valuation, source="haraj-live", url=url, title=rec["title"]
        )
        stats["ingested"] += 1
        stats["flagged"] += int(valuation.is_flagged)
        if stats["ingested"] >= target:
            break

    session.commit()
    session.close()
    client.close()
    print(
        f"Scanned {stats['scanned']} listings | {stats['cars']} cars | {stats['priced']} priced "
        f"| ingested {stats['ingested']} | {stats['flagged']} flagged as deals."
    )
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Harvest real Haraj car deals")
    ap.add_argument("--scan", type=int, default=600, help="max listings to scan")
    ap.add_argument("--target", type=int, default=25, help="stop after this many ingested")
    ap.add_argument("--delay", type=float, default=0.4, help="seconds between requests")
    ap.add_argument("--keep", action="store_true", help="keep existing rows instead of replacing")
    args = ap.parse_args()
    harvest(scan=args.scan, target=args.target, min_delay=args.delay, replace=not args.keep)
