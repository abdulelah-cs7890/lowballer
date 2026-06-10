"""Comps-based valuation for eBay products.

eBay exposes exact-model search, so a model's *fair value* is just the median of its
comparable listings. A listing well below that median is a deal — but an item priced
absurdly low is usually an accessory, broken unit, or wrong listing, so we guard against
those rather than surface them as deals.
"""

from __future__ import annotations

import statistics

from app.pricing import DEFAULT_FLAG_THRESHOLD, Valuation

SUSPICIOUS_DISCOUNT = 0.45  # eBay is efficient: a bigger gap is almost always defective/wrong
MIN_COMPS = 8  # need enough listings for a trustworthy median


def comps_value(prices: list[float]) -> float | None:
    """Median fair value from comparable prices, trimming extremes to cut outlier skew."""
    clean = sorted(p for p in prices if isinstance(p, (int, float)) and p > 0)
    if len(clean) < MIN_COMPS:
        return None
    k = max(1, len(clean) // 10)  # trim ~10% off each tail
    core = clean[k : len(clean) - k] or clean
    return float(statistics.median(core))


def assess(price: float, fair_value: float, threshold: float = DEFAULT_FLAG_THRESHOLD) -> Valuation:
    pct_below = (fair_value - price) / fair_value if fair_value > 0 else 0.0
    suspicious = pct_below >= SUSPICIOUS_DISCOUNT
    return Valuation(
        asking_price=float(price),
        predicted_price=round(fair_value, 2),
        percent_below=round(pct_below, 4),
        # a real deal: meaningfully below median but not absurdly so
        is_flagged=(threshold <= pct_below < SUSPICIOUS_DISCOUNT),
        needs_review=suspicious,
    )
