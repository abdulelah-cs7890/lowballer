"""Ingest eBay product deals: for each watched model, search → median → flag → store.

Decoupled from the data source via `search_fn(query) -> list[item dict]`, so the same
logic runs against the live `EbayClient` or an offline fixture (used by tests until the
API keys are approved).

    python -m app.ebay.ingest          # live (needs EBAY_CLIENT_ID / EBAY_CLIENT_SECRET)
"""

from __future__ import annotations

from collections.abc import Callable

from app import repository
from app.config import settings
from app.db import SessionLocal, init_db
from app.models.tables import Flag, Listing, Valuation
from app.ebay.valuation import MIN_COMPS, assess, comps_value

# (label, query, eBay category id, must-include title tokens, must-exclude title tokens).
# The include/exclude tokens reject wrong models/variants that eBay's loose search returns.
GPUS, PHONES, LAPTOPS, CONSOLES = "27386", "9355", "177", "139971"
# desktop-GPU groups must exclude mobile/eGPU variants (very different value)
GPU_EX = ["mobile", "laptop", "egpu", "external", "xg"]
WATCHLIST: list[tuple[str, str, str, list[str], list[str]]] = [
    ("GPU", "RTX 4090", GPUS, ["4090"], GPU_EX),
    ("GPU", "RTX 4080 Super", GPUS, ["4080", "super"], GPU_EX),
    ("GPU", "RTX 4070 Ti", GPUS, ["4070", "ti"], GPU_EX + ["super"]),
    ("GPU", "RTX 3090", GPUS, ["3090"], GPU_EX + ["ti"]),
    ("GPU", "RX 7900 XTX", GPUS, ["7900", "xtx"], GPU_EX),
    ("Console", "PS5 Slim", CONSOLES, ["ps5"], ["digital", "controller", "stand", "cover"]),
    ("Console", "Xbox Series X", CONSOLES, ["series x"], ["series s", "controller"]),
    ("Laptop", "MacBook Pro 14 M3", LAPTOPS, ["macbook", "m3"], ["m1", "m2"]),
    ("Phone", "iPhone 15 Pro 256GB", PHONES, ["iphone", "15 pro", "256"], ["max", "plus"]),
    ("Phone", "Galaxy S24 Ultra 256GB", PHONES, ["s24 ultra", "256"], ["case", "cover"]),
]

# Cheap-for-a-reason markers — these aren't deals, they're defective/locked/incomplete.
JUNK_MARKERS = [
    "for parts", "not working", "as is", "as-is", "broken", "cracked", "faulty",
    "no power", "damaged", "repair", "spares", "untested", "box only", "empty box",
    "no os", "no ssd", "no hdd", "no battery", "no batt", "no ram", "no charger",
    "icloud", "frp", "locked to", "owner locked", "activation lock", "blacklisted",
    "bad esn", "financed", "unpaid", "carrier locked", "cellular only", "at&t only",
    "t-mobile only", "verizon only", "sprint only", "cricket only", "boost only",
    "metropcs", "metro pcs", "metro by", "tracfone", "simple mobile", "page plus",
    "consumer cellular", "xfinity mobile", "spectrum mobile", "visible by", "h2o",
    "straight talk", "read descr", "please read", "see desc",
]

# search_fn(query, category_id) -> items, so the same logic runs live or against a fixture.
SearchFn = Callable[[str, str | None], list[dict]]


def _relevant(title: str | None, include: list[str], exclude: list[str]) -> bool:
    t = (title or "").lower()
    if any(j in t for j in JUNK_MARKERS) or any(x in t for x in exclude):
        return False
    return all(tok in t for tok in include)


def ingest(search_fn: SearchFn, *, watchlist=WATCHLIST, threshold: float | None = None, replace: bool = True) -> dict:
    threshold = settings.flag_threshold if threshold is None else threshold
    init_db()
    session = SessionLocal()

    if replace:  # eBay products fully replace whatever was there
        session.query(Flag).delete()
        session.query(Valuation).delete()
        session.query(Listing).delete()
        session.commit()

    stats = dict(queries=0, thin=0, listings=0, flagged=0)
    for category, query, category_id, include, exclude in watchlist:
        try:
            items = search_fn(query, category_id)
        except Exception:
            continue
        items = [it for it in items if _relevant(it.get("title"), include, exclude)]
        stats["queries"] += 1
        fair = comps_value([it.get("price") for it in items])
        if fair is None:
            stats["thin"] += 1
            continue
        for it in items:
            if not it.get("price"):
                continue
            valuation = assess(it["price"], fair, threshold)
            record = {
                "make": category,
                "model": query,
                "price": it["price"],
                "title": it.get("title"),
                "image": it.get("image"),
                "condition": it.get("condition"),
            }
            repository.upsert_deal(
                session, f"ebay-{it['id']}", record, valuation,
                source="ebay", url=it.get("url"), title=it.get("title"),
            )
            stats["listings"] += 1
            stats["flagged"] += int(valuation.is_flagged)

    session.commit()
    session.close()
    print(
        f"Watched {stats['queries']} models ({stats['thin']} too thin for >={MIN_COMPS} comps) | "
        f"stored {stats['listings']} listings | {stats['flagged']} flagged as deals."
    )
    return stats


def refresh(search_fn: SearchFn | None = None, *, watchlist=WATCHLIST, threshold: float | None = None) -> list[dict]:
    """Incremental, idempotent refresh (no wipe): keep deals current and create flags only
    for the *newly* underpriced listings. Those new flags stream to the dashboard live via
    SSE (the on-site notification). Returns the new-deal dicts.
    """
    threshold = settings.flag_threshold if threshold is None else threshold
    if search_fn is None:
        search_fn = _live_search_fn()
    init_db()
    session = SessionLocal()
    new_deals: list[dict] = []

    for category, query, category_id, include, exclude in watchlist:
        try:
            items = search_fn(query, category_id)
        except Exception:
            continue
        items = [it for it in items if _relevant(it.get("title"), include, exclude)]
        fair = comps_value([it.get("price") for it in items])
        if fair is None:
            continue
        current_ids: set[str] = set()
        for it in items:
            if not it.get("price"):
                continue
            listing_id = f"ebay-{it['id']}"
            current_ids.add(listing_id)
            valuation = assess(it["price"], fair, threshold)
            record = {
                "make": category, "model": query, "price": it["price"],
                "title": it.get("title"), "image": it.get("image"), "condition": it.get("condition"),
            }
            status = repository.upsert_deal(
                session, listing_id, record, valuation,
                source="ebay", url=it.get("url"), title=it.get("title"),
            )
            if status == "new":
                new_deals.append({
                    "model": query, "category": category, "price": it["price"], "median": fair,
                    "percent_below": valuation.percent_below, "condition": it.get("condition"),
                    "url": it.get("url"), "title": it.get("title"),
                })
        repository.close_missing_flags(session, query, current_ids)
        session.commit()

    session.close()
    print(f"Refresh: {len(new_deals)} new deal(s).")
    return new_deals


def _live_search_fn() -> SearchFn:
    from app.ebay.client import EbayClient

    client = EbayClient()
    return lambda q, cat: client.search(q, limit=80, category_ids=cat)


if __name__ == "__main__":
    ingest(_live_search_fn())
