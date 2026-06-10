"""Seed the dev database with realistic deals so the dashboard has data before the
scraper exists. Generates sample cars, values them with the real model, and prices a
slice of them below fair value to create flagged deals.

    python -m legacy.seed
"""

from __future__ import annotations

import numpy as np

from app.db import SessionLocal, init_db
from app.models.tables import Flag, Listing, Valuation
from legacy.ml.synth import make_synthetic_dataset
from legacy.recorder import record_listing
from legacy.valuation.model import Valuator


def _to_native(record: dict) -> dict:
    """numpy scalars (np.int64/np.float64) -> python types so SQLite can bind them."""
    return {k: (v.item() if hasattr(v, "item") else v) for k, v in record.items()}


def seed(n: int = 200, seed_val: int = 7) -> None:
    init_db()
    valuator = Valuator()
    rng = np.random.default_rng(seed_val)
    cars = make_synthetic_dataset(n=n, seed=seed_val).to_dict("records")

    session = SessionLocal()
    # idempotent: wipe prior seed data
    session.query(Flag).delete()
    session.query(Valuation).delete()
    session.query(Listing).delete()
    session.commit()

    flagged = 0
    for i, raw in enumerate(cars):
        car = _to_native(raw)
        attrs = {k: v for k, v in car.items() if k != "price"}
        predicted = float(valuator.predict([{**attrs, "price": 0}])[0])
        # 60% priced fairly, 40% underpriced -> a healthy mix of flags
        if rng.random() < 0.4:
            factor = float(rng.uniform(0.62, 0.90))
        else:
            factor = float(rng.uniform(0.96, 1.06))
        asking = int(max(8_000, round(predicted * factor, -2)))

        valuation = valuator.value({**attrs, "price": asking})
        listing_id = f"seed-{i:04d}"
        record_listing(
            session,
            listing_id,
            {**attrs, "price": asking},
            valuation,
            source="seed",
            url=f"https://haraj.com.sa/{listing_id}",
            title=f"{car['make']} {car['model']} {car['year']}",
        )
        flagged += int(valuation.is_flagged)

    session.commit()
    session.close()
    print(f"Seeded {len(cars)} listings — {flagged} flagged as deals.")


if __name__ == "__main__":
    seed()
