"""Pipeline worker: source -> normalize -> value -> store (flag if underpriced).

Default run uses the offline fixture source so it works with no network:

    python -m legacy.worker                 # ingest fixtures, value, flag, write to DB
    python -m legacy.worker --keep          # add to existing rows instead of replacing

Shares `legacy.recorder.record_listing` with the seeder, so scraped deals show up in the
same API/dashboard.
"""

from __future__ import annotations

import argparse
from collections.abc import Iterable

from app.db import SessionLocal, init_db
from app.models.tables import Flag, Listing, Valuation
from legacy.recorder import record_listing
from legacy.scraper.normalize import normalize_listing
from legacy.scraper.sources import fixture_source
from legacy.valuation.model import Valuator


def run(source: Iterable[dict] | None = None, *, min_confidence: float = 0.5, replace: bool = True) -> dict:
    init_db()
    valuator = Valuator()
    session = SessionLocal()

    if replace:
        # reset previously-scraped rows (and their children) before re-ingesting
        haraj_ids = [r.id for r in session.query(Listing.id).filter(Listing.source == "haraj")]
        if haraj_ids:
            session.query(Flag).filter(Flag.listing_id.in_(haraj_ids)).delete(synchronize_session=False)
            session.query(Valuation).filter(Valuation.listing_id.in_(haraj_ids)).delete(synchronize_session=False)
            session.query(Listing).filter(Listing.id.in_(haraj_ids)).delete(synchronize_session=False)
            session.commit()

    stats = dict(seen=0, valued=0, flagged=0, skipped=0)
    for raw in source if source is not None else fixture_source():
        stats["seen"] += 1
        record = normalize_listing(raw)
        if record is None or record["parse_confidence"] < min_confidence:
            stats["skipped"] += 1
            continue
        valuation = valuator.value(record)
        record_listing(
            session,
            f"haraj-{record['id']}",
            record,
            valuation,
            source="haraj",
            url=record.get("url"),
            title=record.get("title"),
        )
        stats["valued"] += 1
        stats["flagged"] += int(valuation.is_flagged)

    session.commit()
    session.close()
    print(
        f"Ingested {stats['seen']} listings -> {stats['valued']} valued, "
        f"{stats['flagged']} flagged as deals, {stats['skipped']} skipped (low signal)."
    )
    return stats


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Lowballer ingest worker")
    ap.add_argument("--min-confidence", type=float, default=0.5)
    ap.add_argument("--keep", action="store_true", help="keep existing scraped rows")
    args = ap.parse_args()
    run(min_confidence=args.min_confidence, replace=not args.keep)
