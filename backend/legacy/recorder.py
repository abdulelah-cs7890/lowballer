"""Legacy persistence for the Haraj-era pipeline.

Originally `repository.record_listing`, kept here so the archived seeder/worker/scraper
stay runnable on their own. The live eBay path uses `app.repository.upsert_deal` instead.
The current `Listing` model no longer carries car columns, so only the fields that still
exist are persisted; the rich car attributes live in the in-memory record (which is all
the ML `Valuator` needs to predict).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tables import Flag, Listing, Valuation
from legacy.valuation.model import Valuation as ValuationResult


def record_listing(
    session: Session,
    listing_id: str,
    record: dict,
    valuation: ValuationResult,
    *,
    source: str = "seed",
    url: str | None = None,
    title: str | None = None,
) -> tuple[Listing, Valuation]:
    """Upsert a listing, store its valuation, and open a flag if it's a deal."""
    listing = session.get(Listing, listing_id) or Listing(id=listing_id)
    listing.make = record.get("make")
    listing.model = record.get("model")
    listing.asking_price = record["price"]
    listing.image = record.get("image")
    listing.condition = record.get("condition")
    listing.source = source
    listing.url = url
    listing.title = title
    session.add(listing)

    val = Valuation(
        listing_id=listing_id,
        predicted_price=valuation.predicted_price,
        percent_below=valuation.percent_below,
        needs_review=valuation.needs_review,
        model_mae=valuation.model_mae,
        model_version="xgb-1",
    )
    session.add(val)
    session.flush()  # assign val.id

    if valuation.is_flagged:
        session.add(
            Flag(
                listing_id=listing_id,
                valuation_id=val.id,
                percent_below=valuation.percent_below,
                needs_review=valuation.needs_review,
                status="open",
            )
        )
    return listing, val
