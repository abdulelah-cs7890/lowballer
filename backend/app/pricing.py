"""Core pricing primitives shared by the live product (no ML / sklearn deps).

The eBay path values items with a comps median (see `app.ebay.valuation`); this module
just holds the result type and the default flag threshold.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

# A listing must be at least this far below fair value to be flagged as a deal.
DEFAULT_FLAG_THRESHOLD = 0.12  # 12%


@dataclass
class Valuation:
    asking_price: float
    predicted_price: float        # fair value (eBay: comps median)
    percent_below: float          # 0.13 == asking is 13% below fair value
    is_flagged: bool
    needs_review: bool            # too-good-to-be-true; surface but warn

    def to_dict(self) -> dict:
        return asdict(self)
