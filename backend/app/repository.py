"""Data-access layer. All DB reads/writes for deals go through here, so the API and
the worker share one consistent path and the storage engine stays swappable.
"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.tables import Flag, Listing, Valuation
from app.pricing import Valuation as ValuationResult


def _deal_dict(listing: Listing, valuation: Valuation) -> dict:
    return {
        "id": listing.id,
        "make": listing.make,
        "model": listing.model,
        "url": listing.url,
        "title": listing.title,
        "image": listing.image,
        "condition": listing.condition,
        "asking_price": listing.asking_price,
        "predicted_price": valuation.predicted_price,
        "percent_below": valuation.percent_below,
        "needs_review": valuation.needs_review,
    }


def list_deals(
    session: Session,
    *,
    make: str | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    min_percent_below: float | None = None,
    limit: int = 100,
) -> list[dict]:
    stmt = (
        select(Listing, Valuation)
        .join(Valuation, Valuation.listing_id == Listing.id)
        .join(Flag, Flag.valuation_id == Valuation.id)
        .where(Flag.status == "open")
    )
    if make:
        stmt = stmt.where(func.lower(Listing.make) == make.lower())
    if min_price is not None:
        stmt = stmt.where(Listing.asking_price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Listing.asking_price <= max_price)
    if min_percent_below is not None:
        stmt = stmt.where(Valuation.percent_below >= min_percent_below)
    stmt = stmt.order_by(Valuation.percent_below.desc()).limit(limit)

    return [_deal_dict(listing, val) for listing, val in session.execute(stmt).all()]


def max_flag_id(session: Session) -> int:
    """Highest open-flag id right now — the live stream's starting cursor."""
    return session.scalar(
        select(func.coalesce(func.max(Flag.id), 0)).where(Flag.status == "open")
    ) or 0


def new_flagged_deals(session: Session, after_id: int) -> list[tuple[int, dict]]:
    """Open flags created after `after_id`, oldest first, as (flag_id, deal dict)."""
    stmt = (
        select(Flag.id, Listing, Valuation)
        .join(Listing, Flag.listing_id == Listing.id)
        .join(Valuation, Flag.valuation_id == Valuation.id)
        .where(Flag.status == "open", Flag.id > after_id)
        .order_by(Flag.id.asc())
    )
    return [(fid, _deal_dict(listing, val)) for fid, listing, val in session.execute(stmt).all()]


def get_deal(session: Session, listing_id: str) -> dict | None:
    stmt = (
        select(Listing, Valuation)
        .join(Valuation, Valuation.listing_id == Listing.id)
        .where(Listing.id == listing_id)
        .order_by(Valuation.created_at.desc(), Valuation.id.desc())
        .limit(1)
    )
    row = session.execute(stmt).first()
    if row is None:
        return None
    listing, val = row
    deal = _deal_dict(listing, val)
    deal["comps"] = find_comps(session, listing)
    return deal


def find_comps(session: Session, listing: Listing, limit: int = 8) -> list[dict]:
    """Comparable listings that justify the valuation. Prefer the same product model; if that's
    sparse, fall back to the same category so the user always sees context. Cheapest first.
    """
    base = select(Listing).where(Listing.id != listing.id).order_by(Listing.asking_price)

    exact = base.where(Listing.make == listing.make, Listing.model == listing.model)
    comps = list(session.execute(exact.limit(limit)).scalars().all())

    if len(comps) < limit and listing.make:
        have = {c.id for c in comps}
        fill = base.where(Listing.make == listing.make, Listing.model != listing.model)
        for c in session.execute(fill.limit(limit * 2)).scalars().all():
            if c.id not in have:
                comps.append(c)
                if len(comps) >= limit:
                    break

    return [
        {
            "make": c.make,
            "model": c.model,
            "title": c.title,
            "condition": c.condition,
            "asking_price": c.asking_price,
        }
        for c in comps
    ]


def count_ebay_listings(session: Session) -> int:
    return session.scalar(
        select(func.count()).select_from(Listing).where(Listing.source == "ebay")
    ) or 0


def upsert_deal(
    session: Session,
    listing_id: str,
    record: dict,
    valuation: ValuationResult,
    *,
    source: str = "ebay",
    url: str | None = None,
    title: str | None = None,
) -> str:
    """Idempotent upsert for repeated refreshes: one Valuation + at most one OPEN Flag per
    listing. Returns "new" | "existing" | "closed" | "none" so the caller can alert only on
    genuinely-new deals.
    """
    listing = session.get(Listing, listing_id) or Listing(id=listing_id)
    listing.make = record.get("make")        # category (GPU, Phone, …)
    listing.model = record.get("model")      # product model (RTX 4090, …)
    listing.asking_price = record["price"]
    listing.image = record.get("image")
    listing.condition = record.get("condition")
    listing.source = source
    listing.url = url
    listing.title = title
    session.add(listing)

    # keep a single current valuation per listing (update in place)
    val = session.execute(
        select(Valuation).where(Valuation.listing_id == listing_id).order_by(Valuation.id.desc()).limit(1)
    ).scalar_one_or_none()
    if val is None:
        val = Valuation(listing_id=listing_id)
        session.add(val)
    val.predicted_price = valuation.predicted_price
    val.percent_below = valuation.percent_below
    val.needs_review = valuation.needs_review
    val.model_version = "ebay-comps"
    session.flush()

    open_flag = session.execute(
        select(Flag).where(Flag.listing_id == listing_id, Flag.status == "open").limit(1)
    ).scalar_one_or_none()

    if valuation.is_flagged:
        if open_flag is None:
            session.add(
                Flag(
                    listing_id=listing_id,
                    valuation_id=val.id,
                    percent_below=valuation.percent_below,
                    needs_review=valuation.needs_review,
                    status="open",
                )
            )
            return "new"
        open_flag.valuation_id = val.id
        open_flag.percent_below = valuation.percent_below
        open_flag.needs_review = valuation.needs_review
        return "existing"

    if open_flag is not None:
        open_flag.status = "dismissed"  # deal gone (price moved up / sold)
        return "closed"
    return "none"


def close_missing_flags(session: Session, model: str, current_ids: set[str]) -> int:
    """Dismiss open flags for a model whose listing vanished from the latest results."""
    rows = (
        session.execute(
            select(Flag)
            .join(Listing, Flag.listing_id == Listing.id)
            .where(Flag.status == "open", Listing.model == model)
        )
        .scalars()
        .all()
    )
    closed = 0
    for flag in rows:
        if flag.listing_id not in current_ids:
            flag.status = "dismissed"
            closed += 1
    return closed
